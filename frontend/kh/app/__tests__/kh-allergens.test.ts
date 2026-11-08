// KH: tests for the allergen block of the recipe page (D44): chips and the warning with substitutions, the correction
// calls, the variant and where it leads, and that nothing can be edited without the right to.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, test, vi } from "vitest";
import KhAllergens from "../components/KhAllergens.vue";
import type { KhRecipeAllergens } from "../lib/api/allergens";
import { i18n } from "~/tests/setup";
import de from "../../lang/de-DE.json";

const getMock = vi.hoisted(() => vi.fn());
const putMock = vi.hoisted(() => vi.fn());
const postMock = vi.hoisted(() => vi.fn());
const pushMock = vi.hoisted(() => vi.fn());
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock, put: putMock, post: postMock }) }));

i18n.global.mergeLocaleMessage("en-US", de);

const stubs = { VBtn: { template: "<button><slot /></button>" }, VChip: { template: "<button><slot /></button>" } };
const answer = (extra: Partial<KhRecipeAllergens> = {}): KhRecipeAllergens => ({
  hits: [
    { allergen: "milk", lines: ["200 g Butter"], corrected: null },
    { allergen: "gluten", lines: ["300 g Mehl"], corrected: null },
  ],
  warnings: [{ allergen: "milk", names: ["Lena Muster"] }],
  substitutions: [{ line: "200 g Butter", allergen: "milk", replacement: "Margarine" }],
  ...extra,
});

async function render(data: KhRecipeAllergens, canEdit = true) {
  getMock.mockResolvedValue({ data });
  const wrapper = mount(KhAllergens, { props: { slug: "kuchen", groupSlug: "familie", canEdit }, global: { stubs } });
  await flushPromises();
  return wrapper;
}
const button = (wrapper: Awaited<ReturnType<typeof render>>, text: string) => wrapper.findAll("button").find(b => b.text().includes(text));

beforeEach(() => {
  vi.stubGlobal("useRouter", () => ({ push: pushMock }));
  getMock.mockReset();
  putMock.mockReset();
  postMock.mockReset();
  pushMock.mockReset();
});

describe("KhAllergens", () => {
  test("chips and the disclaimer, never a claim of being free of something", async () => {
    const wrapper = await render(answer());
    expect(getMock).toHaveBeenCalledWith("/api/kh/recipes/kuchen/allergens");
    expect(wrapper.text()).toContain("Enthält wahrscheinlich");
    expect(wrapper.text()).toContain("Milch");
    expect(wrapper.text()).toContain("Gluten");
    expect(wrapper.text()).toContain("Erkannt aus den Zutaten, ohne Gewähr");
  });

  test("the warning names the person and the replacement", async () => {
    const wrapper = await render(answer());
    expect(wrapper.text()).toContain("Enthält wahrscheinlich Milch. Lena Muster verträgt das nicht.");
    expect(wrapper.text()).toContain("Statt 200 g Butter: Margarine");
  });

  test("several people: plural verb", async () => {
    const wrapper = await render(answer({ warnings: [{ allergen: "milk", names: ["Lena Muster", "Paul Muster"] }] }));
    expect(wrapper.text()).toMatch(/Lena Muster.*Paul Muster vertragen das nicht/);
  });

  test("no warning: no warning box, no variant button", async () => {
    const wrapper = await render(answer({ warnings: [], substitutions: [] }));
    expect(wrapper.text()).not.toContain("verträgt das nicht");
    expect(button(wrapper, "Als Variante speichern")).toBeUndefined();
  });

  test("a tap on a chip shows its lines; 'stimmt nicht' takes the allergen out", async () => {
    putMock.mockResolvedValue({ data: answer({ hits: [{ allergen: "milk", lines: ["200 g Butter"], corrected: false }], warnings: [] }) });
    const wrapper = await render(answer());
    await button(wrapper, "Gluten")!.trigger("click");
    expect(wrapper.text()).toContain("300 g Mehl");
    await button(wrapper, "stimmt nicht")!.trigger("click");
    await flushPromises();
    expect(putMock).toHaveBeenCalledWith("/api/kh/recipes/kuchen/allergens/gluten", { present: false });
    expect(wrapper.text()).not.toContain("verträgt das nicht");
  });

  test("a taken-out allergen is struck and can be undone", async () => {
    const wrapper = await render(answer({ hits: [{ allergen: "milk", lines: ["Butter"], corrected: false }], warnings: [] }));
    expect(wrapper.find(".kh-allergens__chip--out").exists()).toBe(true);
    putMock.mockResolvedValue({ data: answer() });
    await wrapper.find(".kh-allergens__chip--out").trigger("click");
    await button(wrapper, "Rückgängig")!.trigger("click");
    expect(putMock).toHaveBeenCalledWith("/api/kh/recipes/kuchen/allergens/milk", { present: null });
  });

  test("'Allergen ergänzen' adds one that is missing, not one already shown", async () => {
    const wrapper = await render(answer());
    const select = wrapper.find("select");
    const options = select.findAll("option").map(o => o.attributes("value"));
    expect(options).toContain("eggs");
    expect(options).not.toContain("milk");
    putMock.mockResolvedValue({ data: answer() });
    await select.setValue("eggs");
    expect(putMock).toHaveBeenCalledWith("/api/kh/recipes/kuchen/allergens/eggs", { present: true });
  });

  test("without the right to edit there are no controls, but chips and the warning stay", async () => {
    const wrapper = await render(answer(), false);
    await button(wrapper, "Gluten")!.trigger("click");
    expect(wrapper.text()).toContain("300 g Mehl");
    expect(button(wrapper, "stimmt nicht")).toBeUndefined();
    expect(wrapper.find("select").exists()).toBe(false);
    expect(wrapper.text()).toContain("verträgt das nicht");
  });

  test("the variant asks for the warned allergens and goes to the new recipe", async () => {
    postMock.mockResolvedValue({ data: { slug: "kuchen-ohne-milch" } });
    const wrapper = await render(answer());
    await button(wrapper, "Als Variante speichern")!.trigger("click");
    await flushPromises();
    expect(postMock).toHaveBeenCalledWith("/api/kh/recipes/kuchen/variant", { allergens: ["milk"] });
    expect(pushMock).toHaveBeenCalledWith("/g/familie/r/kuchen-ohne-milch");
  });

  test("a variant with nothing to replace (422) says so and stays", async () => {
    postMock.mockResolvedValue({ data: null, error: { response: { status: 422 } } });
    const wrapper = await render(answer());
    await button(wrapper, "Als Variante speichern")!.trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Dafür gibt es keinen Ersatz");
    expect(pushMock).not.toHaveBeenCalled();
  });
});
