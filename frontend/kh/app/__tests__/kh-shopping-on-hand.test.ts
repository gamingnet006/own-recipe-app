// KH: tests for "always in the house" (D65) on the shopping page: the tiles of such foods and their place in the
// department, the state read from the household's slug, and what setting it does.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { useKhShopping } from "../composables/use-kh-shopping";
import { catalog, existingFor, isOnHand } from "../lib/shopping-tiles";

const api = vi.hoisted(() => ({ shopping: { lists: { getOne: vi.fn(), getAll: vi.fn() }, items: {} }, foods: {} }));
const setOnHandApi = vi.hoisted(() => vi.fn());
type Food = { id: string; name: string; pluralName: string | null; labelId: string | null; householdsWithIngredientFood: string[] };
const holder = vi.hoisted(() => ({ foods: undefined as unknown as { value: Food[] } }));
const toast = vi.hoisted(() => ({ error: vi.fn() }));

vi.mock("~/composables/api", () => ({ useUserApi: () => api }));
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({}) }));
vi.mock("../lib/api/shopping", () => ({ KhShoppingApi: class { setOnHand = setOnHandApi; } }));
vi.mock("../lib/api/amounts", () => ({ KhAmountsApi: class { parseLine = vi.fn(); } }));
vi.mock("~/composables/store/use-food-store", async () => {
  const { ref } = await import("vue");
  holder.foods = ref<Food[]>([]);
  return { useFoodStore: () => ({ store: holder.foods }) };
});
vi.mock("~/composables/store/use-label-store", () => ({ useLabelStore: () => ({ store: { value: [] } }) }));
vi.mock("~/composables/store/use-unit-store", () => ({ useUnitStore: () => ({ store: { value: [] } }) }));
vi.mock("~/composables/use-toast", () => ({ alert: toast }));
vi.mock("vue-i18n", () => ({ useI18n: () => ({ t: (key: string) => key }) }));
vi.stubGlobal("useMealieAuth", () => ({ user: { value: { id: "u1", householdSlug: "home" } } }));

const food = (id: string, name: string, households: string[] = []): Food => ({ id, name, pluralName: null, labelId: null, householdsWithIngredientFood: households });

describe("catalog", () => {
  const foods = [food("1", "Mehl", ["home"]), food("2", "Apfel"), food("3", "Salz", ["other"]), food("4", "Zucker", ["home"])];

  test("marks the foods the household always has and puts them after the others of the department", () => {
    const tiles = catalog(foods, [], [], [], "home")[0]!.tiles;
    expect(tiles.map(tile => tile.name)).toEqual(["Apfel", "Salz", "Mehl", "Zucker"]);
    expect(tiles.map(tile => !!tile.onHand)).toEqual([false, false, true, true]);
  });

  test("another household's state does not count, and without a household nothing is marked", () => {
    expect(catalog(foods, [], [], [], "other")[0]!.tiles.filter(tile => tile.onHand).map(tile => tile.name)).toEqual(["Salz"]);
    expect(catalog(foods, [], [], []).flatMap(department => department.tiles).some(tile => tile.onHand)).toBe(false);
  });

  test("isOnHand reads the slug list", () => {
    expect(isOnHand(food("1", "Mehl", ["home"]), "home")).toBe(true);
    expect(isOnHand(food("1", "Mehl"), "home")).toBe(false);
    expect(isOnHand(undefined, "home")).toBe(false);
    expect(isOnHand(food("1", "Mehl", [""]), "")).toBe(false);
  });
});

describe("existingFor", () => {
  const tile = { name: "Milch", emoji: "", foodId: "f1", labelId: null };
  const entry = (over = {}) => ({ id: "a", checked: false, foodId: "f1", note: null, food: { name: "Milch" }, ...over });

  test("an open item takes what was typed", () => {
    expect(existingFor(tile, [entry()], { quantity: 2 })).toEqual({ item: entry(), changes: { quantity: 2 } });
  });

  test("a bought item is put back with it", () => {
    expect(existingFor(tile, [entry({ checked: true })], { quantity: 2 })?.changes).toEqual({ quantity: 2, checked: false });
  });

  test("an article that is not there gives nothing", () => {
    expect(existingFor(tile, [entry({ foodId: "x", food: { name: "Brot" } })], {})).toBeUndefined();
  });
});

describe("setOnHand", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    holder.foods.value = [food("1", "Mehl")];
  });

  test("sends the choice, takes the food the server answers and reads the state from it", async () => {
    setOnHandApi.mockResolvedValue({ data: food("1", "Mehl", ["home"]) });
    const shopping = useKhShopping();
    expect(shopping.onHand("1")).toBe(false);
    await shopping.setOnHand("1", true);
    expect(setOnHandApi).toHaveBeenCalledWith("1", true);
    expect(shopping.onHand("1")).toBe(true);
  });

  test("tells the person when it fails and keeps the state", async () => {
    setOnHandApi.mockResolvedValue({ data: null });
    const shopping = useKhShopping();
    await shopping.setOnHand("1", true);
    expect(toast.error).toHaveBeenCalled();
    expect(shopping.onHand("1")).toBe(false);
  });
});
