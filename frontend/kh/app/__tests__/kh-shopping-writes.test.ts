// KH: tests for what the shopping page writes (D60): an item is read fresh before a change so others' changes stay,
// late answers do not overwrite newer ones, and tiles and typed lines become foods of the group.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { useKhShopping } from "../composables/use-kh-shopping";

const api = vi.hoisted(() => ({
  shopping: {
    lists: { getOne: vi.fn(), getAll: vi.fn() },
    items: { getOne: vi.fn(), updateOne: vi.fn(), createMany: vi.fn(), deleteOne: vi.fn() },
  },
  foods: { getOne: vi.fn() },
}));
const parseLine = vi.hoisted(() => vi.fn());
const ensure = vi.hoisted(() => ({ food: vi.fn(), unit: vi.fn() }));
// a real ref: the page waits for the foods to load
const foods = await vi.hoisted(async () => {
  const { ref } = await import("vue");
  return ref<{ id: string; name: string; pluralName: string | null; labelId: string | null }[]>([]);
});
const units = vi.hoisted(() => ({ value: [] as { id: string; name: string; abbreviation: string }[] }));
const toast = vi.hoisted(() => ({ error: vi.fn() }));

vi.mock("~/composables/api", () => ({ useUserApi: () => api }));
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({}) }));
vi.mock("../lib/api/shopping", () => ({ KhShoppingApi: class { ensureFood = ensure.food; ensureUnit = ensure.unit; } }));
vi.mock("../lib/api/amounts", () => ({ KhAmountsApi: class { parseLine = parseLine; } }));
vi.mock("~/composables/store/use-food-store", () => ({ useFoodStore: () => ({ store: foods }) }));
vi.mock("~/composables/store/use-label-store", () => ({ useLabelStore: () => ({ store: { value: [] } }) }));
vi.mock("~/composables/store/use-unit-store", () => ({ useUnitStore: () => ({ store: units }) }));
vi.mock("~/composables/use-toast", () => ({ alert: toast }));
vi.mock("vue-i18n", () => ({ useI18n: () => ({ t: (key: string) => key, locale: { value: "de-DE" } }) }));
vi.stubGlobal("useMealieAuth", () => ({ user: { value: { id: "u1", householdSlug: "home" } } }));

const item = (over = {}) => ({
  id: "i1", checked: false, quantity: 0, unit: null, unitId: null, note: "", extras: null, position: 1,
  foodId: "f1", food: { id: "f1", name: "Milch" }, labelId: null, label: null, recipeReferences: [], updatedAt: null, ...over,
});
const listWith = (items: unknown[]) => ({ id: "l1", name: "Rewe", listItems: items, labelSettings: [], recipeReferences: [] });

async function opened(items: unknown[] = [item()]) {
  api.shopping.lists.getAll.mockResolvedValue({ data: { items: [{ id: "l1" }] } });
  api.shopping.lists.getOne.mockResolvedValue({ data: listWith(items) });
  const shopping = useKhShopping();
  await shopping.start(null);
  return shopping;
}

beforeEach(() => {
  vi.clearAllMocks();
  foods.value = [{ id: "f1", name: "Milch", pluralName: null, labelId: null }];
  units.value = [{ id: "u-l", name: "Liter", abbreviation: "l" }];
  vi.stubGlobal("localStorage", { getItem: () => null, setItem: vi.fn() });
  api.shopping.items.updateOne.mockResolvedValue({ data: {}, error: null });
});

describe("change", () => {
  test("writes only the changed fields on top of the fresh item", async () => {
    const shopping = await opened();
    const stale = shopping.items.value[0]!;
    // meanwhile somebody else checked it off and wrote a note
    api.shopping.items.getOne.mockResolvedValue({ data: item({ checked: true, note: "Bio" }) });
    await shopping.change(stale, { quantity: 2 });
    expect(api.shopping.items.updateOne).toHaveBeenCalledWith("i1", expect.objectContaining({ checked: true, note: "Bio", quantity: 2 }));
  });

  test("tells the person when the item cannot be read", async () => {
    const shopping = await opened();
    api.shopping.items.getOne.mockResolvedValue({ data: null });
    await shopping.change(shopping.items.value[0]!, { quantity: 2 });
    expect(api.shopping.items.updateOne).not.toHaveBeenCalled();
    expect(toast.error).toHaveBeenCalled();
  });
});

describe("reload", () => {
  test("drops an answer a newer request overtook", async () => {
    const shopping = await opened();
    let slow: (value: unknown) => void = () => {};
    api.shopping.lists.getOne.mockReturnValueOnce(new Promise((resolve) => { slow = resolve; }));
    const first = shopping.reload();
    api.shopping.lists.getOne.mockResolvedValueOnce({ data: listWith([item({ id: "new" })]) });
    await shopping.reload();
    slow({ data: listWith([item({ id: "old" })]) });
    await first;
    expect(shopping.items.value.map(entry => entry.id)).toEqual(["new"]);
  });
});

describe("adding", () => {
  test("a tile that is no food yet becomes one, once, with its department", async () => {
    const shopping = await opened([]);
    ensure.food.mockResolvedValue({ data: { id: "f2", name: "Brot", pluralName: null, labelId: "lab" } });
    api.shopping.items.createMany.mockResolvedValue({ data: { createdItems: [item({ id: "n1" })], updatedItems: [] } });
    await shopping.addTile({ name: "Brot", emoji: "", labelId: "lab" });
    expect(ensure.food).toHaveBeenCalledWith("Brot", "lab");
    expect(api.shopping.items.createMany.mock.calls[0]![0][0]).toMatchObject({ foodId: "f2", note: "", labelId: "lab" });
    await shopping.addTile({ name: "brot", emoji: "", labelId: "lab" });
    expect(ensure.food).toHaveBeenCalledTimes(1);
  });

  test("a typed line becomes the food with amount, unit and note", async () => {
    const shopping = await opened([]);
    parseLine.mockResolvedValue({ data: { quantity: 2, unitId: "u-l", foodId: "f1", name: "Milch", note: "3,5 %" } });
    api.foods.getOne.mockResolvedValue({ data: foods.value[0] });
    api.shopping.items.createMany.mockResolvedValue({ data: { createdItems: [item({ id: "n1" })], updatedItems: [] } });
    await shopping.addTyped("2 Liter Milch 3,5 %");
    expect(api.shopping.items.createMany.mock.calls[0]![0][0]).toMatchObject({ foodId: "f1", quantity: 2, unitId: "u-l", note: "3,5 %" });
  });
});

describe("typed line details", () => {
  test("keeps a unit the page has not loaded yet", async () => {
    const shopping = await opened([]);
    parseLine.mockResolvedValue({ data: { quantity: 2, unitId: "u-unknown", foodId: "f1", name: "Milch", note: "" } });
    api.foods.getOne.mockResolvedValue({ data: foods.value[0] });
    api.shopping.items.createMany.mockResolvedValue({ data: { createdItems: [item({ id: "n1" })], updatedItems: [] } });
    await shopping.addTyped("2 Becher Milch");
    expect(api.shopping.items.createMany.mock.calls[0]![0][0]).toMatchObject({ unitId: "u-unknown", quantity: 2 });
  });

  test("an article already on the list takes the typed amount", async () => {
    const there = item({ id: "m1", foodId: "f1", food: foods.value[0], quantity: 1 });
    const shopping = await opened([there]);
    parseLine.mockResolvedValue({ data: { quantity: 3, unitId: null, foodId: "f1", name: "Milch", note: "" } });
    api.foods.getOne.mockResolvedValue({ data: foods.value[0] });
    api.shopping.items.getOne.mockResolvedValue({ data: there });
    await shopping.addTyped("3 Milch");
    expect(api.shopping.items.createMany).not.toHaveBeenCalled();
    expect(api.shopping.items.updateOne.mock.calls[0]![1]).toMatchObject({ quantity: 3 });
  });
});

describe("typed amount without a unit", () => {
  test("keeps the unit of an article already on the list", async () => {
    const liter = { id: "u-l", name: "Liter", abbreviation: "l" };
    const there = item({ id: "m1", food: foods.value[0], quantity: 1, unit: liter, unitId: "u-l" });
    const shopping = await opened([there]);
    parseLine.mockResolvedValue({ data: { quantity: 2, unitId: null, foodId: "f1", name: "Milch", note: "" } });
    api.foods.getOne.mockResolvedValue({ data: foods.value[0] });
    api.shopping.items.getOne.mockResolvedValue({ data: there });
    await shopping.addTyped("2 Milch");
    expect(api.shopping.items.updateOne.mock.calls[0]![1]).toMatchObject({ quantity: 2, unit: liter, unitId: "u-l" });
  });
});

describe("linking recipe items to foods", () => {
  test("an item 'ml Milch' gets the food Milch and a clean note", async () => {
    units.value.push({ id: "u-ml", name: "Milliliter", abbreviation: "ml" });
    const loose = item({ id: "r1", foodId: null, food: null, note: "ml Milch", quantity: 200 });
    api.shopping.items.getOne.mockResolvedValue({ data: loose });
    await opened([loose]);
    await vi.waitFor(() => expect(api.shopping.items.updateOne).toHaveBeenCalled());
    expect(api.shopping.items.updateOne.mock.calls[0]![1]).toMatchObject({ foodId: "f1", note: "", quantity: 200, unitId: "u-ml" });
  });
});

describe("typed line with a unit the group lacks", () => {
  test("has the unit ensured and uses it", async () => {
    const shopping = await opened([]);
    parseLine.mockResolvedValue({ data: { quantity: 2, unitId: null, unitAbbreviation: "l", foodId: "f1", name: "Milch", note: "3,5 %" } });
    api.foods.getOne.mockResolvedValue({ data: foods.value[0] });
    ensure.unit.mockResolvedValue({ data: { id: "u-new", name: "Liter", abbreviation: "l" } });
    api.shopping.items.createMany.mockResolvedValue({ data: { createdItems: [item({ id: "n1" })], updatedItems: [] } });
    await shopping.addTyped("2 Liter Milch 3,5%");
    expect(ensure.unit).toHaveBeenCalledWith("l");
    expect(api.shopping.items.createMany.mock.calls[0]![0][0]).toMatchObject({ unitId: "u-new", quantity: 2 });
  });
});

describe("setQuantity", () => {
  test("a size the group has no unit for creates the unit and replaces the old size", async () => {
    const shopping = await opened([item({ quantity: 500, unit: { id: "u-g", name: "Gramm", abbreviation: "g" } })]);
    ensure.unit.mockResolvedValue({ data: { id: "u-kg", name: "Kilogramm", abbreviation: "kg" } });
    api.shopping.items.getOne.mockResolvedValue({ data: item() });
    await shopping.setQuantity(shopping.items.value[0]!, "1 kg");
    expect(ensure.unit).toHaveBeenCalledWith("kg");
    expect(api.shopping.items.updateOne).toHaveBeenCalledWith("i1", expect.objectContaining({ quantity: 1, unitId: "u-kg" }));
  });

  test("the chosen size again clears amount and unit", async () => {
    const shopping = await opened([item({ quantity: 1, unit: { id: "u-l", name: "Liter", abbreviation: "l" } })]);
    api.shopping.items.getOne.mockResolvedValue({ data: item() });
    await shopping.setQuantity(shopping.items.value[0]!, "1 l");
    expect(api.shopping.items.updateOne).toHaveBeenCalledWith("i1", expect.objectContaining({ quantity: 0, unit: null, unitId: null }));
  });
});
