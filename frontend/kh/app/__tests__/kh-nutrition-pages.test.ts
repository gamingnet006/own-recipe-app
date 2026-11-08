// KH: tests for the nutrition and allergen pages (D44): the order of the mapping list, one row's search (debounced) and
// its saves, the piece weight, and the card marks' cache doing one request for many cards.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import KhFoodMapping from "../components/KhFoodMapping.vue";
import type { KhFoodMapping as Mapping } from "../lib/api/nutrition";
import { openFirst, parsePieceGrams } from "../lib/nutrition";
import { i18n } from "~/tests/setup";
import de from "../../lang/de-DE.json";

const getMock = vi.hoisted(() => vi.fn());
const putMock = vi.hoisted(() => vi.fn());
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock, put: putMock }) }));

i18n.global.mergeLocaleMessage("en-US", de);

const food = (foodId: string, confirmed: boolean, extra: Partial<Mapping> = {}): Mapping => ({
  foodId, foodName: foodId, blsCode: "B1", blsName: "Butter mild gesäuert", confirmed, suggested: !confirmed, pieceGrams: null, recipeCount: 2, ...extra,
});

beforeEach(() => {
  getMock.mockReset();
  putMock.mockReset();
});
afterEach(() => vi.useRealTimers());

describe("openFirst", () => {
  test("the open ones first, each group in the order it came", () => {
    const list = [food("a", true), food("b", false), food("c", true), food("d", false)];
    expect(openFirst(list).map(f => f.foodId)).toEqual(["b", "d", "a", "c"]);
  });
  test("does not change the list it was given", () => {
    const list = [food("a", true), food("b", false)];
    openFirst(list);
    expect(list.map(f => f.foodId)).toEqual(["a", "b"]);
  });
});

describe("parsePieceGrams", () => {
  test("empty is none, a number with a comma or a point is that many grams", () => {
    expect(parsePieceGrams("")).toBeNull();
    expect(parsePieceGrams(" 55,5 ")).toBe(55.5);
    expect(parsePieceGrams("80")).toBe(80);
  });
  test("zero, negative or text is invalid", () => {
    for (const bad of ["0", "-3", "abc"]) expect(parsePieceGrams(bad)).toBe("invalid");
  });
});

describe("KhFoodMapping", () => {
  function render(mapping: Mapping) {
    return mount(KhFoodMapping, { props: { mapping }, global: { stubs: { VBtn: { template: "<button><slot /></button>" }, VCard: { template: "<div><slot /></div>" } } } });
  }
  const button = (wrapper: ReturnType<typeof render>, text: string) => wrapper.findAll("button").find(b => b.text().includes(text))!;

  test("the search waits 300 ms after the last key, then asks once", async () => {
    vi.useFakeTimers();
    getMock.mockResolvedValue({ data: [{ code: "M1", name: "Weizen Mehl, Type 405", kcal: 340 }] });
    const wrapper = render(food("Mehl", false));
    const input = wrapper.find("input[type=search]");
    await input.setValue("me");
    await input.setValue("mehl");
    await vi.advanceTimersByTimeAsync(299);
    expect(getMock).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(1);
    await flushPromises();
    expect(getMock).toHaveBeenCalledTimes(1);
    expect(getMock).toHaveBeenCalledWith("/api/kh/nutrition/bls?q=mehl");
    expect(wrapper.text()).toContain("Weizen Mehl, Type 405");
  });

  test("choosing a hit and 'Bestätigen' stores that code, confirmed, with the piece weight", async () => {
    vi.useFakeTimers();
    getMock.mockResolvedValue({ data: [{ code: "M1", name: "Weizen Mehl, Type 405", kcal: 340 }] });
    putMock.mockResolvedValue({ data: food("Mehl", true, { blsCode: "M1" }) });
    const wrapper = render(food("Mehl", false));
    await wrapper.find("input[type=search]").setValue("mehl");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();
    await button(wrapper, "Weizen Mehl").trigger("click");
    await wrapper.find("input[inputmode=decimal]").setValue("55,5");
    await button(wrapper, "Bestätigen").trigger("click");
    await flushPromises();
    expect(putMock).toHaveBeenCalledWith("/api/kh/nutrition/foods/Mehl", { blsCode: "M1", confirmed: true, pieceGrams: 55.5 });
    expect(wrapper.emitted("saved")![0]![0]).toMatchObject({ confirmed: true, blsCode: "M1" });
  });

  test("'Bestätigen' without a choice confirms the suggestion", async () => {
    putMock.mockResolvedValue({ data: food("Butter", true) });
    const wrapper = render(food("Butter", false));
    await button(wrapper, "Bestätigen").trigger("click");
    expect(putMock).toHaveBeenCalledWith("/api/kh/nutrition/foods/Butter", { blsCode: "B1", confirmed: true, pieceGrams: null });
  });

  test("'Kein passender Eintrag' stores no code, confirmed", async () => {
    putMock.mockResolvedValue({ data: food("Wasser", true, { blsCode: null }) });
    const wrapper = render(food("Wasser", false));
    await button(wrapper, "Kein passender Eintrag").trigger("click");
    expect(putMock).toHaveBeenCalledWith("/api/kh/nutrition/foods/Wasser", { blsCode: null, confirmed: true, pieceGrams: null });
  });

  test("an invalid piece weight is not sent", async () => {
    const wrapper = render(food("Ei", false));
    await wrapper.find("input[inputmode=decimal]").setValue("0");
    await button(wrapper, "Bestätigen").trigger("click");
    expect(putMock).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain("Das hat nicht geklappt");
  });

  test("an unknown code (422) is said in words", async () => {
    putMock.mockResolvedValue({ data: null, error: { response: { status: 422 } } });
    const wrapper = render(food("Ei", false));
    await button(wrapper, "Bestätigen").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Diesen BLS-Eintrag gibt es nicht");
    expect(wrapper.emitted("saved")).toBeUndefined();
  });
});

describe("useKhAllergenWarnings", () => {
  test("many cards, one request; a refresh asks again", async () => {
    vi.resetModules();
    getMock.mockResolvedValue({ data: { kuchen: ["milk"] } });
    const { refreshKhAllergenWarnings, useKhAllergenWarnings } = await import("../composables/use-kh-allergens");
    const cards = Array.from({ length: 5 }, () => useKhAllergenWarnings());
    await flushPromises();
    expect(getMock).toHaveBeenCalledTimes(1);
    expect(getMock).toHaveBeenCalledWith("/api/kh/allergens/warnings");
    expect(cards[4]!.warnings.value).toEqual({ kuchen: ["milk"] });
    getMock.mockResolvedValue({ data: {} });
    await refreshKhAllergenWarnings();
    expect(getMock).toHaveBeenCalledTimes(2);
    expect(cards[0]!.warnings.value).toEqual({});
  });

  test("a failed request leaves no marks", async () => {
    vi.resetModules();
    getMock.mockResolvedValue({ data: null, error: new Error("down") });
    const { useKhAllergenWarnings } = await import("../composables/use-kh-allergens");
    const { warnings } = useKhAllergenWarnings();
    await flushPromises();
    expect(warnings.value).toEqual({});
  });
});
