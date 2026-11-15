// KH: tests for the add-ons page (D46): the rules (presets, locked rows, redirect guard), loading the household's
// switches once per user, and the page's component.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { defineComponent } from "vue";
import KhAddons from "../components/KhAddons.vue";
import {
  addonRedirect,
  applyPreset,
  currentPreset,
  DEFAULT_ADDONS,
  type KhAddonFlags,
  rowState,
} from "../lib/addons";
import { khAddons, loadKhAddonsFor, resetKhAddons } from "../composables/use-kh-addons";
import { i18n } from "~/tests/setup";
import en from "../../lang/en-US.json";
import de from "../../lang/de-DE.json";

const getMock = vi.hoisted(() => vi.fn());
const putMock = vi.hoisted(() => vi.fn());
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock, put: putMock }) }));

i18n.global.mergeLocaleMessage("en-US", en);

const on = (changes: Partial<KhAddonFlags> = {}): KhAddonFlags => ({ ...DEFAULT_ADDONS, ...changes });
const answer = (flags: KhAddonFlags, unavailable: string[] = []) => ({
  data: { flags, enabled: { ...flags, substitutions: flags.substitutions && flags.allergens }, unavailable },
});

beforeEach(() => {
  getMock.mockReset();
  putMock.mockReset();
  resetKhAddons();
});
afterEach(() => vi.restoreAllMocks());

describe("presets", () => {
  test("only set the two big switches", () => {
    expect(applyPreset(on({ books: false }), "recipes")).toEqual(on({ books: false, shopping: false, planner: false }));
    expect(applyPreset(on({ planner: false }), "planner")).toEqual(on());
    expect(applyPreset(on(), "shopping")).toEqual(on({ planner: false }));
  });

  test("are recognized again, a mix of the two switches is none", () => {
    expect(currentPreset(on({ shopping: false, planner: false }))).toBe("recipes");
    expect(currentPreset(on({ planner: false }))).toBe("shopping");
    expect(currentPreset(on())).toBe("planner");
    expect(currentPreset(on({ shopping: false }))).toBeNull();
  });
});

describe("rows", () => {
  test("a row the host does not offer is locked off", () => {
    expect(rowState("telegram", on({ telegram: true }), ["telegram"])).toEqual({ on: false, disabled: true, reason: "unavailable" });
    expect(rowState("telegram", on({ telegram: true }), [])).toEqual({ on: true, disabled: false, reason: null });
  });

  test("exchange needs allergens and shows off without them", () => {
    expect(rowState("substitutions", on({ allergens: false }), [])).toEqual({ on: false, disabled: true, reason: "needs-allergens" });
    expect(rowState("substitutions", on(), []).on).toBe(true);
  });

  test("the defaults are those of a fresh install", () => {
    const off = Object.entries(DEFAULT_ADDONS).filter(([, value]) => !value).map(([key]) => key);
    expect(off).toEqual(["shareLinks", "telegram", "whisper", "voice"]);
  });
});

describe("redirect guard", () => {
  test("sends the pages of a switched-off add-on to the recipes with the add-on's name", () => {
    const go = (path: string, changes: Partial<KhAddonFlags>) => addonRedirect(path, on(changes), "familie");
    expect(go("/shopping-lists/abc", { shopping: false })).toEqual({ to: "/g/familie", addon: "shopping" });
    expect(go("/household/mealplan/planner/view", { planner: false })).toEqual({ to: "/g/familie", addon: "planner" });
    expect(go("/g/familie/doppelte", { duplicates: false })).toEqual({ to: "/g/familie", addon: "duplicates" });
    expect(go("/g/familie/naehrwerte", { nutrition: false })?.addon).toBe("nutrition");
    expect(go("/g/familie/vertraeglichkeit", { allergens: false })?.addon).toBe("allergens");
    expect(go("/g/familie/kochbuch/rezept/x", { books: false })?.addon).toBe("books");
    expect(go("/g/familie/kochbuch/kuchen", { books: false })?.addon).toBe("books");
  });

  test("lets everything else through, also while the add-on is on", () => {
    expect(addonRedirect("/g/familie/doppelte", on(), "familie")).toBeNull();
    expect(addonRedirect("/g/familie", on({ shopping: false }), "familie")).toBeNull();
    expect(addonRedirect("/g/familie/zusatzfunktionen", on({ books: false }), "familie")).toBeNull();
    expect(addonRedirect("/g/familie/cookbooks/x", on({ books: false }), "familie")).toBeNull();
  });
});

describe("loading", () => {
  test("asks once per user and keeps the answer", async () => {
    getMock.mockResolvedValue(answer(on({ books: false })));
    await loadKhAddonsFor("u1");
    await loadKhAddonsFor("u1");
    expect(getMock).toHaveBeenCalledTimes(1);
    expect(getMock).toHaveBeenCalledWith("/api/kh/addons");
    expect(khAddons.enabled.books).toBe(false);
    await loadKhAddonsFor("u2");
    expect(getMock).toHaveBeenCalledTimes(2);
  });

  test("another user whose load fails does not keep the previous household's switches", async () => {
    getMock.mockResolvedValue(answer(on({ books: false })));
    await loadKhAddonsFor("u1");
    getMock.mockResolvedValue({ data: null, error: new Error("offline") });
    await loadKhAddonsFor("u2");
    expect(khAddons.enabled).toEqual(DEFAULT_ADDONS);
  });

  test("after a failed load the next navigations do not ask again for 60 seconds", async () => {
    vi.useFakeTimers();
    getMock.mockResolvedValue({ data: null, error: new Error("offline") });
    await loadKhAddonsFor("u1");
    await loadKhAddonsFor("u1");
    expect(getMock).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(61_000);
    getMock.mockResolvedValue(answer(on({ books: false })));
    await loadKhAddonsFor("u1");
    expect(getMock).toHaveBeenCalledTimes(2);
    expect(khAddons.enabled.books).toBe(false);
    vi.useRealTimers();
  });

  test("keeps the defaults when the answer fails", async () => {
    getMock.mockResolvedValue({ data: null, error: new Error("offline") });
    await loadKhAddonsFor("u1");
    expect(khAddons.enabled).toEqual(DEFAULT_ADDONS);
  });
});

describe("KhAddons", () => {
  const Switch = defineComponent({
    props: { modelValue: Boolean, disabled: Boolean },
    emits: ["update:modelValue"],
    template: `<input type="checkbox" :checked="modelValue" :disabled="disabled" @change="$emit('update:modelValue', $event.target.checked)">`,
  });
  const Button = defineComponent({ emits: ["click"], template: `<button @click="$emit('click')"><slot /></button>` });

  async function render(flags: KhAddonFlags, canChange = true, unavailable: string[] = []) {
    getMock.mockResolvedValue(answer(flags, unavailable));
    putMock.mockImplementation((_url: string, body: KhAddonFlags) => Promise.resolve(answer(body, unavailable)));
    await loadKhAddonsFor("u1");
    const wrapper = mount(KhAddons, {
      props: { canChange },
      global: { stubs: { VSwitch: Switch, VBtn: Button, VCard: { template: "<div><slot /></div>" } } },
    });
    await flushPromises();
    return wrapper;
  }
  const box = (wrapper: Awaited<ReturnType<typeof render>>, name: string) => wrapper.find(`[data-testid="addon-${name}"]`);

  test("a preset sets both big switches and stores them", async () => {
    const wrapper = await render(on());
    await wrapper.findAll("button").find(b => b.text() === en.kh.addons.presets.recipes)!.trigger("click");
    await flushPromises();
    expect(putMock).toHaveBeenCalledWith("/api/kh/addons", on({ shopping: false, planner: false }));
    expect((box(wrapper, "shopping").element as HTMLInputElement).checked).toBe(false);
    expect((box(wrapper, "planner").element as HTMLInputElement).checked).toBe(false);
    expect(khAddons.enabled.shopping).toBe(false);
  });

  test("a switch stores the whole set", async () => {
    const wrapper = await render(on());
    await box(wrapper, "books").setValue(false);
    await flushPromises();
    expect(putMock).toHaveBeenCalledWith("/api/kh/addons", on({ books: false }));
  });

  test("lists every add-on with a text and the host's gaps as locked", async () => {
    const wrapper = await render(on(), true, ["telegram"]);
    for (const name of Object.keys(DEFAULT_ADDONS)) expect(box(wrapper, name).exists(), name).toBe(true);
    expect((box(wrapper, "telegram").element as HTMLInputElement).disabled).toBe(true);
    expect(wrapper.text()).toContain(en.kh.addons.unavailable);
  });

  test("exchange is locked with a hint while allergens are off", async () => {
    const wrapper = await render(on({ allergens: false }));
    expect((box(wrapper, "substitutions").element as HTMLInputElement).disabled).toBe(true);
    expect(wrapper.text()).toContain(en.kh.addons["needs-allergens"]);
  });

  test("members only read", async () => {
    const wrapper = await render(on(), false);
    expect(wrapper.findAll("input").every(input => (input.element as HTMLInputElement).disabled)).toBe(true);
    expect(wrapper.findAll("button")).toHaveLength(0);
  });
});

test("both languages name every add-on and area", () => {
  for (const texts of [en, de]) {
    for (const name of Object.keys(DEFAULT_ADDONS)) {
      const entry = (texts.kh.addons.items as Record<string, { title: string; text: string }>)[name]
        ?? (texts.kh.addons.areas as Record<string, { title: string; text: string }>)[name];
      expect(entry?.title, name).toBeTruthy();
      expect(entry?.text, name).toBeTruthy();
    }
    expect(Object.keys(texts.kh.addons.presets)).toEqual(["title", "recipes", "shopping", "planner"]);
  }
});
