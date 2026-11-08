// KH: a mount test of the print layout (D43): title page, table of contents with numbers, photos only on request,
// the amount bracket in a step and the switches that leave parts out. The preview and the printout are this one component.
import { mount } from "@vue/test-utils";
import { describe, expect, test, vi } from "vitest";
import KhPrintBook from "../components/KhPrintBook.vue";
import { defaultBookSettings, type BookEntry } from "../lib/book";
import { i18n } from "~/tests/setup";
import khTexts from "../../lang/de-DE.json";

vi.mock("~/composables/use-locales", () => ({ useLocales: () => ({ locales: [{ value: "de-DE", pluralFoodHandling: "without-unit" }], locale: { value: "de-DE" } }) }));
vi.mock("~/composables/api", () => ({ useStaticRoutes: () => ({ recipeImage: (id: string) => `/img/${id}` }) }));

// The German texts, as the book is printed in German; the test locale is only the slot they sit in.
i18n.global.mergeLocaleMessage("en-US", khTexts);

const markdown = { props: ["source"], template: "<div class=\"md\" v-html=\"source\" />" };
const butter = { referenceId: "b", quantity: 200, unit: null, food: { id: "f", name: "Butter" }, note: "", title: "" };
const step = (text: string, ...refs: string[]) => ({ id: text, title: "", summary: "", text, ingredientReferences: refs.map(referenceId => ({ referenceId })) });
const recipe = (id: string, name: string, extra: object = {}) => ({
  id, slug: id, name, image: "x", description: "Beschreibung von " + id, recipeServings: 4, recipeIngredient: [butter],
  recipeInstructions: [step("Die Butter schmelzen", "b"), step("Backen")], notes: [{ title: "Tipp", text: "Notiz zu " + id }], ...extra,
});
const entry = (number: number, name: string, photo = false): BookEntry => ({ number, recipe: recipe(`r${number}`, name) as never, photo, servings: 4 });
const entries = [entry(1, "Apfelkuchen"), entry(2, "Brot")];

function render(settings = defaultBookSettings("Kuchen", "Muster", 2026), list = entries, oven: "fan" | null = null, preview = false) {
  return mount(KhPrintBook, { props: { settings, entries: list, oven, preview }, global: { stubs: { SafeMarkdown: markdown } } });
}

describe("KhPrintBook", () => {
  test("title page, numbered table of contents and a numbered sheet per recipe", () => {
    const wrapper = render();
    expect(wrapper.find(".kh-title-page").text()).toContain("Kuchen");
    expect(wrapper.find(".kh-title-page").text()).toContain("Muster · 2026");
    const toc = wrapper.find(".kh-toc").text();
    expect(toc).toContain("Nr. 1 Apfelkuchen");
    expect(toc).toContain("Nr. 2 Brot");
    expect(wrapper.findAll(".kh-recipe")).toHaveLength(2);
    expect(wrapper.findAll(".kh-recipe")[1]!.find("h2").text()).toContain("Nr. 2");
  });

  test("a single recipe has no number, title page or table of contents", () => {
    const wrapper = render({ ...defaultBookSettings("Karte", "x", 2026), titlePage: false, toc: false }, [entry(1, "Apfelkuchen")]);
    expect(wrapper.find(".kh-title-page").exists()).toBe(false);
    expect(wrapper.find(".kh-toc").exists()).toBe(false);
    expect(wrapper.find(".kh-recipe h2").text()).not.toContain("Nr.");
  });

  test("a photo only where the entry has one", () => {
    const wrapper = render(undefined, [entry(1, "Apfelkuchen", true), entry(2, "Brot", false)]);
    const sheets = wrapper.findAll(".kh-recipe");
    expect(sheets[0]!.find("img").exists()).toBe(true);
    expect(sheets[1]!.find("img").exists()).toBe(false);
  });

  test("steps carry the amount and the oven brackets", () => {
    const list = [{ ...entry(1, "Brot"), recipe: recipe("r1", "Brot", { recipeInstructions: [step("Die Butter schmelzen", "b"), step("Bei 180 °C backen")] }) as never }];
    const text = render(undefined, list, "fan").find(".kh-recipe").text();
    expect(text).toContain("Butter (200) schmelzen");
    expect(text).toContain("(Umluft 160 °C)");
    expect(render(undefined, list, null).find(".kh-recipe").text()).not.toContain("Umluft");
  });

  test("description and notes follow their switches; the preview marks the sheets", () => {
    const off = render({ ...defaultBookSettings("K", "x", 2026), description: false, notes: false }).find(".kh-recipe").text();
    expect(off).not.toContain("Beschreibung von");
    expect(off).not.toContain("Notiz zu");
    const on = render(undefined, entries, null, true);
    expect(on.find(".kh-recipe").text()).toContain("Notiz zu r1");
    expect(on.classes()).toContain("kh-preview");
  });

  test("nothing at all without entries", () => {
    expect(render(undefined, []).find(".kh-sheet").exists()).toBe(false);
  });
});
