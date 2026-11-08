// KH: tests for the nutrition block of the recipe page (D44): the number formats, the per-device switch, and the block's
// states (calculated, estimated, entered by hand, nothing counted, switched off), plus the texts in both languages.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, test, vi } from "vitest";
import type KhNutrition from "../components/KhNutrition.vue";
import type { KhRecipeNutrition } from "../lib/api/nutrition";
import { formatNutrient } from "../lib/nutrition";
import { i18n } from "~/tests/setup";
import de from "../../lang/de-DE.json";
import en from "../../lang/en-US.json";

const getMock = vi.hoisted(() => vi.fn());
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock }) }));

// The German texts, as the app is used in German; the test locale is only the slot they sit in.
i18n.global.mergeLocaleMessage("en-US", de);

const KEY = "kh-show-nutrition";
const stubs = { NuxtLink: { props: ["to"], template: "<a :href=\"to\"><slot /></a>" } };
const values = { kcal: 320, fat: 16, saturated: 9.5, carbs: 38, sugar: 12, protein: 6.4, fiber: 1.2, salt: 0.2 };
const nutrition = (extra: Partial<KhRecipeNutrition> = {}): KhRecipeNutrition => ({
  per: "serving", servings: 4, values, counted: 7, total: 8, missing: ["etwas Salz"], estimated: false, manual: false, ...extra,
});

/** Mounts the block with the server's answer; a fresh module so the stored switch is read again. */
async function render(answer: KhRecipeNutrition | null) {
  vi.resetModules();
  getMock.mockResolvedValue(answer ? { data: answer } : { data: null, error: new Error("down") });
  const component = (await import("../components/KhNutrition.vue")).default as typeof KhNutrition;
  const wrapper = mount(component, { props: { slug: "kuchen", groupSlug: "familie" }, global: { stubs } });
  await flushPromises();
  return wrapper;
}

beforeEach(() => {
  localStorage.clear();
  getMock.mockReset();
});

describe("formatNutrient", () => {
  test("energy in kcal, the rest in grams, German decimal comma", () => {
    expect(formatNutrient("kcal", 320, "de-DE")).toBe("320 kcal");
    expect(formatNutrient("protein", 16, "de-DE")).toBe("16 g");
    expect(formatNutrient("salt", 0.2, "de-DE")).toBe("0,2 g");
    expect(formatNutrient("salt", 0.2, "en-US")).toBe("0.2 g");
  });
  test("nothing counted gives a dash", () => {
    expect(formatNutrient("fat", null, "de-DE")).toBe("–");
    expect(formatNutrient("kcal", null, "de-DE")).toBe("–");
  });
});

describe("useKhNutritionSetting", () => {
  const fresh = async () => {
    vi.resetModules();
    return (await import("../lib/nutrition")).useKhNutritionSetting();
  };
  test("on at first", async () => {
    expect((await fresh()).value).toBe(true);
  });
  test("a stored choice comes back, and changes are stored", async () => {
    localStorage.setItem(KEY, "false");
    const show = await fresh();
    expect(show.value).toBe(false);
    show.value = true;
    expect(localStorage.getItem(KEY)).toBe("true");
  });
});

describe("KhNutrition", () => {
  test("the header says the energy per serving; the table lists the values", async () => {
    const wrapper = await render(nutrition());
    expect(getMock).toHaveBeenCalledWith("/api/kh/recipes/kuchen/nutrition");
    expect(wrapper.find("summary").text()).toContain("ca. 320 kcal pro Portion");
    const rows = wrapper.findAll("tr").map(row => row.text());
    expect(rows).toHaveLength(8);
    expect(rows[2]).toBe("davon gesättigte Fettsäuren9.5 g");
    expect(wrapper.text()).toContain("aus 7 von 8 Zutaten");
    expect(wrapper.text()).toContain("ohne: etwas Salz");
    expect(wrapper.text()).toContain("Quelle: BLS 4.0, Max Rubner-Institut, CC BY 4.0");
    expect(wrapper.text()).not.toContain("geschätzt");
  });

  test("a recipe without servings is for the whole recipe", async () => {
    const wrapper = await render(nutrition({ per: "recipe", servings: null }));
    expect(wrapper.find("summary").text()).toContain("ca. 320 kcal für das ganze Rezept");
  });

  test("estimated links to the mapping page", async () => {
    const wrapper = await render(nutrition({ estimated: true }));
    const link = wrapper.find("a");
    expect(link.text()).toContain("geschätzt");
    expect(link.attributes("href")).toBe("/g/familie/naehrwerte");
  });

  test("values entered by hand say so and show no counts or source", async () => {
    const wrapper = await render(nutrition({ manual: true, counted: 0, total: 0, missing: [] }));
    expect(wrapper.text()).toContain("von Hand eingetragen");
    expect(wrapper.text()).not.toContain("aus 0 von");
    expect(wrapper.text()).not.toContain("Quelle");
  });

  test("nothing counted: no table, the lines that were left out", async () => {
    const wrapper = await render(nutrition({ values: null, counted: 0 }));
    expect(wrapper.find("table").exists()).toBe(false);
    expect(wrapper.text()).toContain("keine Zutat konnte gerechnet werden");
    expect(wrapper.text()).toContain("ohne: etwas Salz");
  });

  test("switched off: nothing shows and nothing is asked", async () => {
    localStorage.setItem(KEY, "false");
    const wrapper = await render(nutrition());
    expect(wrapper.html()).toBe("<!--v-if-->");
    expect(getMock).not.toHaveBeenCalled();
  });

  test("a failed request says so instead of leaving a gap", async () => {
    const wrapper = await render(null);
    expect(wrapper.text()).toContain("nicht geladen");
  });
});

describe("texts", () => {
  const keys = (node: object, prefix = ""): string[] => Object.entries(node)
    .flatMap(([key, value]) => (typeof value === "object" ? keys(value, `${prefix}${key}.`) : [`${prefix}${key}`])).sort();
  test("German and English have the same keys under nutrition and allergens", () => {
    for (const part of ["nutrition", "allergens"] as const) {
      expect(keys(en.kh[part]), part).toEqual(keys(de.kh[part]));
    }
  });
  test("no text claims anything is free of an allergen", () => {
    expect(JSON.stringify(de.kh.allergens).toLowerCase()).not.toMatch(/frei von|allergenfrei/);
  });
});
