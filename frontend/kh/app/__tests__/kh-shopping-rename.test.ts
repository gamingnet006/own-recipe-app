// KH: renaming a shopping list: the pure name check, and the write that keeps the list's items and shows the new
// name in the store chips at once.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { useKhShopping } from "../composables/use-kh-shopping";
import { cleanListName } from "../lib/shopping-items";

const api = vi.hoisted(() => ({
  shopping: { lists: { getOne: vi.fn(), getAll: vi.fn(), updateOne: vi.fn() }, items: {} },
  foods: { getOne: vi.fn() },
}));
const toast = vi.hoisted(() => ({ error: vi.fn() }));
// real refs: the page watches the stores
const stores = await vi.hoisted(async () => {
  const { ref } = await import("vue");
  return { foods: ref([]), labels: ref([]), units: ref([]) };
});

vi.mock("~/composables/api", () => ({ useUserApi: () => api }));
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({}) }));
vi.mock("../lib/api/shopping", () => ({ KhShoppingApi: class { unused = null; } }));
vi.mock("../lib/api/amounts", () => ({ KhAmountsApi: class { unused = null; } }));
vi.mock("~/composables/store/use-food-store", () => ({ useFoodStore: () => ({ store: stores.foods }) }));
vi.mock("~/composables/store/use-label-store", () => ({ useLabelStore: () => ({ store: stores.labels }) }));
vi.mock("~/composables/store/use-unit-store", () => ({ useUnitStore: () => ({ store: stores.units }) }));
vi.mock("~/composables/use-toast", () => ({ alert: toast }));
vi.mock("vue-i18n", () => ({ useI18n: () => ({ t: (key: string) => key }) }));
vi.stubGlobal("useMealieAuth", () => ({ user: { value: { id: "u1", householdSlug: "home" } } }));

const listWith = (name: string) => ({ id: "l1", name, listItems: [{ id: "i1" }], labelSettings: [], recipeReferences: [] });

async function opened() {
  api.shopping.lists.getAll.mockResolvedValue({ data: { items: [{ id: "l1", name: "Rewe" }] } });
  api.shopping.lists.getOne.mockResolvedValue({ data: listWith("Rewe") });
  const shopping = useKhShopping();
  await shopping.start(null);
  return shopping;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("localStorage", { getItem: () => null, setItem: vi.fn() });
});

describe("cleanListName", () => {
  test("trims the name", () => expect(cleanListName("  Aldi  ")).toBe("Aldi"));
  test("refuses empty and blank names", () => {
    expect(cleanListName("")).toBeNull();
    expect(cleanListName(" \t ")).toBeNull();
  });
});

describe("rename", () => {
  test("writes the fresh list with the new name, so no items are lost", async () => {
    const shopping = await opened();
    api.shopping.lists.updateOne.mockResolvedValue({ data: listWith("Aldi"), error: null });
    expect(await shopping.rename(" Aldi ")).toBe(true);
    expect(api.shopping.lists.updateOne).toHaveBeenCalledWith("l1", expect.objectContaining({ name: "Aldi", listItems: [{ id: "i1" }] }));
    expect(shopping.list.value?.name).toBe("Aldi");
    expect(shopping.lists.value[0]?.name).toBe("Aldi");
  });

  test("refuses a blank name without asking the server", async () => {
    const shopping = await opened();
    expect(await shopping.rename("   ")).toBe(false);
    expect(api.shopping.lists.updateOne).not.toHaveBeenCalled();
  });

  test("tells the person when the server refuses and keeps the old name", async () => {
    const shopping = await opened();
    api.shopping.lists.updateOne.mockResolvedValue({ data: null, error: new Error("no") });
    expect(await shopping.rename("Aldi")).toBe(false);
    expect(toast.error).toHaveBeenCalled();
    expect(shopping.list.value?.name).toBe("Rewe");
  });
});
