// KH: tests for the accent colours (wave 2): every variant is readable, the choice order is person, installation,
// Salbei, and the colours reach Vuetify's themes.
import { mount } from "@vue/test-utils";
import { describe, expect, test } from "vitest";
import KhLogo from "../components/KhLogo.vue";
import { KH_ACCENT_KEYS, KH_ACCENTS, asKhAccent, chooseAccent, personAccent, readAccentCache, themeColours, writeAccentCache } from "../lib/accent-colours";
import { applyKhAccent, resetKhAccentOriginal } from "../composables/use-kh-accent";
import { KH_HINT_COLORS } from "../lib/theme";

/** WCAG contrast ratio of two #RRGGBB colors. */
function contrast(first: string, second: string): number {
  const luminance = (hex: string) => {
    const [r, g, b] = [1, 3, 5].map((start) => {
      const channel = parseInt(hex.slice(start, start + 2), 16) / 255;
      return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
  };
  const [light, dark] = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (light! + 0.05) / (dark! + 0.05);
}

const WHITE = "#FFFFFF";
const DARK_GROUND = "#1E1E1E"; // Mealie's dark background and surface
const LIGHT_GROUND = "#F4F5F1"; // Kochheft's light background

describe("contrast of all 20 variants (WCAG AA, 4.5:1)", () => {
  test.each(KH_ACCENT_KEYS)("%s", (key) => {
    const { light, dark } = KH_ACCENTS[key];
    expect(contrast(light.primary, WHITE)).toBeGreaterThanOrEqual(4.5); // white text on a button
    expect(contrast(light.primary, LIGHT_GROUND)).toBeGreaterThanOrEqual(4.5); // links and icons on the page
    expect(contrast(light.onHint, light.hint)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(dark.onPrimary, dark.primary)).toBeGreaterThanOrEqual(4.5); // dark text on a button
    expect(contrast(dark.primary, DARK_GROUND)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(dark.onHint, dark.hint)).toBeGreaterThanOrEqual(4.5);
  });
});

test("Salbei is the look of every older installation, exactly", () => {
  expect(KH_ACCENTS.salbei.light.primary).toBe("#2F7A55");
  expect(KH_ACCENTS.salbei.dark.primary).toBe("#4FB07E");
  expect(KH_ACCENTS.salbei.dark.onPrimary).toBe("#0E1A13");
  expect(themeColours("salbei").light["kh-hint"]).toBe(KH_HINT_COLORS.light["kh-hint"]);
});

test("there are ten colours and unknown keys are refused", () => {
  expect(KH_ACCENT_KEYS).toHaveLength(10);
  expect(asKhAccent("senf")).toBe("senf");
  expect(asKhAccent("pink")).toBeNull();
  expect(asKhAccent(null)).toBeNull();
});

test("the person's colour beats the installation's; with neither the operator's theme stays (null)", () => {
  expect(chooseAccent("lila", "petrol")).toBe("lila");
  expect(chooseAccent(null, "petrol")).toBe("petrol");
  expect(chooseAccent(undefined, "pink")).toBeNull();
  expect(chooseAccent(null, null)).toBeNull();
});

test("the colours land in both Vuetify themes and keep the other colours", () => {
  const themes = { light: { colors: { primary: "#000000", error: "#B42318" } }, dark: { colors: { "primary": "#000000", "on-primary": "#000000" } } };
  applyKhAccent(themes, "blau");
  expect(themes.light.colors).toMatchObject({ primary: "#236DC7", error: "#B42318" });
  expect(themes.dark.colors).toMatchObject({ "primary": "#78A6DD", "on-primary": "#0E141B" });
});

test("no accent puts the operator's own theme colours back", () => {
  resetKhAccentOriginal();
  const themes = { light: { colors: { primary: "#112233" } }, dark: { colors: { primary: "#445566" } } };
  applyKhAccent(themes, "blau");
  expect(themes.light.colors.primary).toBe("#236DC7");
  applyKhAccent(themes, null);
  expect(themes.light.colors.primary).toBe("#112233");
  expect(themes.dark.colors.primary).toBe("#445566");
  resetKhAccentOriginal();
});

describe("the remembered colours of the last start", () => {
  const memory = () => {
    const data = new Map<string, string>();
    return { getItem: (key: string) => data.get(key) ?? null, setItem: (key: string, value: string) => void data.set(key, value) };
  };

  test("what was written is read back, unknown keys are dropped", () => {
    const storage = memory();
    writeAccentCache(storage, { installation: "petrol", person: { userId: "u1", accent: "beere" } });
    expect(readAccentCache(storage)).toEqual({ installation: "petrol", person: { userId: "u1", accent: "beere" } });
    storage.setItem("kh-accent", JSON.stringify({ installation: "pink", person: { userId: "u1", accent: "x" } }));
    expect(readAccentCache(storage)).toEqual({ installation: null, person: { userId: "u1", accent: null } });
  });

  test("broken or blocked storage counts as empty and never throws", () => {
    const broken = { getItem: () => "{not json", setItem: () => { throw new Error("full"); } };
    expect(readAccentCache(broken)).toEqual({ installation: null, person: null });
    expect(() => writeAccentCache(broken, { installation: null, person: null })).not.toThrow();
  });

  test("the cached colour is only for the person who is signed in, and only until the loaded one is there", () => {
    const cached = { userId: "u1", accent: "beere" as const };
    expect(personAccent({ userId: null, accent: null }, cached, "u1")).toBe("beere");
    expect(personAccent({ userId: null, accent: null }, cached, "u2")).toBeNull();
    expect(personAccent({ userId: null, accent: null }, cached, null)).toBeNull();
    expect(personAccent({ userId: "u1", accent: null }, cached, "u1")).toBeNull(); // they gave it up meanwhile
    expect(personAccent({ userId: "u1", accent: "lila" }, cached, "u1")).toBe("lila");
  });
});

describe("the logo", () => {
  const draw = (brandingLogoUrl: string) =>
    mount(KhLogo, { global: { mocks: { $appInfo: { brandingLogoUrl } }, stubs: { VImg: { template: "<img class='custom' />" } } } });

  test("is the own picture alone when a branding logo is configured", () => {
    const wrapper = draw("/logo.png");
    expect(wrapper.find("img.custom").exists()).toBe(true);
    expect(wrapper.find("svg").exists()).toBe(false);
  });

  test("is the drawn icon alone otherwise", () => {
    const wrapper = draw("");
    expect(wrapper.find("svg").exists()).toBe(true);
    expect(wrapper.find("img.custom").exists()).toBe(false);
  });
});
