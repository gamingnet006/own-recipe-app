// KH: tests for the shopping page without network (D63): the queue (enqueue, replay order, vanished items, restart),
// what is kept on the device, and the page's behavior offline and when the network is back.
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { khAddons } from "../composables/use-kh-addons";
import { useKhShopping } from "../composables/use-kh-shopping";
import { clearStored, enqueue, isLocalId, lastUser, newLocalId, noAnswer, readStored, rememberUser, replay, writeStored, type QueuedOp } from "../lib/shopping-offline";

const api = vi.hoisted(() => ({
  shopping: {
    lists: { getOne: vi.fn(), getAll: vi.fn() },
    items: { getOne: vi.fn(), updateOne: vi.fn(), createMany: vi.fn(), deleteOne: vi.fn() },
  },
  foods: { getOne: vi.fn() },
}));
type Food = { id: string; name: string; pluralName: string | null; labelId: string | null };
const holder = vi.hoisted(() => ({ foods: undefined as unknown as { value: Food[] } }));
// a real ref, because the page watches the store
const foods = { get value() { return holder.foods.value; }, set value(next: Food[]) { holder.foods.value = next; } };
const ensureFoodApi = vi.hoisted(() => vi.fn());
const toast = vi.hoisted(() => ({ error: vi.fn() }));

vi.mock("~/composables/api", () => ({ useUserApi: () => api }));
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({}) }));
vi.mock("../lib/api/shopping", () => ({ KhShoppingApi: class { ensureFood = ensureFoodApi; } }));
vi.mock("../lib/api/amounts", () => ({ KhAmountsApi: class { parseLine = vi.fn(); } }));
vi.mock("~/composables/store/use-food-store", async () => {
  const { ref } = await import("vue");
  holder.foods = ref<Food[]>([]);
  return { useFoodStore: () => ({ store: holder.foods }) };
});
vi.mock("~/composables/store/use-label-store", () => ({ useLabelStore: () => ({ store: { value: [] } }) }));
vi.mock("~/composables/store/use-unit-store", () => ({ useUnitStore: () => ({ store: { value: [] } }) }));
vi.mock("~/composables/use-toast", () => ({ alert: toast }));
vi.mock("vue-i18n", () => ({ useI18n: () => ({ t: (key: string) => key, locale: { value: "de-DE" } }) }));
vi.stubGlobal("useMealieAuth", () => ({ user: { value: { id: "u1", householdSlug: "home" } } }));

const change = (itemId: string, changes: Record<string, unknown>): QueuedOp => ({ kind: "change", itemId, changes });

describe("enqueue", () => {
  test("keeps the order of different items", () => {
    const queue = enqueue(enqueue([], change("a", { checked: true })), change("b", { checked: true }));
    expect(queue.map(op => (op as { itemId: string }).itemId)).toEqual(["a", "b"]);
  });

  test("merges a second change of the same item into its first", () => {
    const queue = enqueue(enqueue([change("a", { checked: true, note: "x" })], change("b", { quantity: 2 })), change("a", { note: "y" }));
    expect(queue).toEqual([change("a", { checked: true, note: "y" }), change("b", { quantity: 2 })]);
  });

  test("merges a change of an item still to be added into the add", () => {
    const add: QueuedOp = { kind: "add", tempId: "local-1", listId: "l", foodId: "f", name: "Butter", labelId: null, fields: { quantity: 1 } };
    expect(enqueue([add], change("local-1", { checked: true }))).toEqual([{ ...add, fields: { quantity: 1, checked: true } }]);
  });

  test("a removal drops what was queued for the item, and is dropped itself for an item that never reached the server", () => {
    const add: QueuedOp = { kind: "add", tempId: newLocalId(), listId: "l", foodId: "f", name: "Butter", labelId: null, fields: {} };
    const tempId = (add as { tempId: string }).tempId;
    expect(enqueue([add], { kind: "remove", itemId: tempId })).toEqual([]);
    expect(enqueue([change("a", { checked: true })], { kind: "remove", itemId: "a" })).toEqual([{ kind: "remove", itemId: "a" }]);
  });

  test("a removal of a local item whose add is not in the queue (it is on its way) is kept", () => {
    const local = newLocalId();
    expect(enqueue([], { kind: "remove", itemId: local })).toEqual([{ kind: "remove", itemId: local }]);
  });

  test("local ids are recognized and unique", () => {
    expect(isLocalId(newLocalId())).toBe(true);
    expect(isLocalId("5f3c")).toBe(false);
    expect(newLocalId()).not.toBe(newLocalId());
  });
});

describe("replay", () => {
  const storeOf = (initial: QueuedOp[]) => {
    const store = { queue: initial, get: () => store.queue, set: (next: QueuedOp[]) => { store.queue = next; } };
    return store;
  };

  test("sends oldest first and empties the queue", async () => {
    const store = storeOf([change("a", {}), change("b", {}), change("c", {})]);
    const sent: string[] = [];
    const failed = await replay(store, async (op) => {
      sent.push((op as { itemId: string }).itemId);
      return "done";
    });
    expect(sent).toEqual(["a", "b", "c"]);
    expect(failed).toBe(0);
    expect(store.queue).toEqual([]);
  });

  test("a vanished item is skipped and the rest goes on", async () => {
    const store = storeOf([change("gone", {}), change("b", {})]);
    const sent: string[] = [];
    await replay(store, async (op) => {
      sent.push((op as { itemId: string }).itemId);
      return (op as { itemId: string }).itemId === "gone" ? "gone" : "done";
    });
    expect(sent).toEqual(["gone", "b"]);
    expect(store.queue).toEqual([]);
  });

  test("without network the op stays at the front and nothing after it is sent", async () => {
    const store = storeOf([change("a", {}), change("b", {})]);
    const run = vi.fn().mockResolvedValueOnce("done").mockResolvedValueOnce("offline");
    await replay(store, run);
    expect(run).toHaveBeenCalledTimes(2);
    expect(store.queue).toEqual([change("b", {})]);
  });

  test("a refused op is dropped and counted", async () => {
    const store = storeOf([change("a", {}), change("b", {})]);
    expect(await replay(store, async op => ((op as { itemId: string }).itemId === "a" ? "failed" : "done"))).toBe(1);
    expect(store.queue).toEqual([]);
  });

  test("changes made while an op is sent are sent too", async () => {
    const store = storeOf([change("a", {})]);
    const sent: string[] = [];
    await replay(store, async (op) => {
      sent.push((op as { itemId: string }).itemId);
      if (sent.length === 1) store.set(enqueue(store.get(), change("late", {})));
      return "done";
    });
    expect(sent).toEqual(["a", "late"]);
  });
});

describe("stored values", () => {
  beforeEach(() => localStorage.clear());

  test("survive a reload and are kept per user", () => {
    writeStored("u1", "queue", [change("a", { checked: true })]);
    expect(readStored("u1", "queue", [])).toEqual([change("a", { checked: true })]);
    expect(readStored("u2", "queue", [])).toEqual([]);
  });

  test("a broken or blocked storage gives the fallback", () => {
    localStorage.setItem("kh-shop-offline:u1:queue", "{not json");
    expect(readStored("u1", "queue", ["fallback"])).toEqual(["fallback"]);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(readStored("u1", "queue", ["fallback"])).toEqual(["fallback"]);
    vi.restoreAllMocks();
  });

  test("clearing removes only what the page kept", () => {
    writeStored("u1", "queue", []);
    writeStored("u2", "lists", []);
    localStorage.setItem("kh-shopping-list", "l1");
    clearStored();
    expect(Object.keys(localStorage)).toEqual(["kh-shopping-list"]);
  });

  test("the last user is remembered for a start without a session, and forgotten with the rest", () => {
    expect(lastUser()).toBe("");
    rememberUser("u1");
    expect(lastUser()).toBe("u1");
    clearStored();
    expect(lastUser()).toBe("");
  });

  test("no answer is told from an answer with an error status", () => {
    expect(noAnswer(new Error("Network Error"))).toBe(true);
    expect(noAnswer({ response: { status: 500 } })).toBe(false);
    expect(noAnswer(null)).toBe(false);
  });
});

const item = (over = {}) => ({
  id: "i1", checked: false, quantity: 0, unit: null, unitId: null, note: "", extras: null, position: 1,
  foodId: "f1", food: { id: "f1", name: "Milch" }, labelId: null, label: null, recipeReferences: [], updatedAt: null, ...over,
});
const listWith = (items: unknown[]) => ({ id: "l1", name: "Rewe", groupId: "g", householdId: "h", listItems: items, labelSettings: [], recipeReferences: [] });
const queueOnDisk = () => readStored<QueuedOp[]>("u1", "queue", []);
// lets a flush that a write started in the background finish
const settle = () => new Promise(resolve => setTimeout(resolve, 0));
const networkDown = { data: null, error: new Error("Network Error") };

function setOnline(value: boolean) {
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(value);
}

async function opened(items: unknown[] = [item()]) {
  api.shopping.lists.getAll.mockResolvedValue({ data: { items: [{ id: "l1", name: "Rewe" }] } });
  api.shopping.lists.getOne.mockResolvedValue({ data: listWith(items) });
  const shopping = useKhShopping();
  await shopping.start(null);
  return shopping;
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  khAddons.enabled.offline = true;
  foods.value = [
    { id: "f1", name: "Milch", pluralName: null, labelId: null },
    { id: "f2", name: "Butter", pluralName: null, labelId: null },
  ];
  api.shopping.items.updateOne.mockResolvedValue({ data: {}, error: null });
  api.shopping.items.deleteOne.mockResolvedValue({ data: {}, error: null });
});

afterEach(() => vi.restoreAllMocks());

describe("the page offline", () => {
  test("a change applies at once, waits in the queue on the device and shows the banner", async () => {
    const shopping = await opened();
    setOnline(false);
    const offlineShopping = useKhShopping();
    offlineShopping.list.value = shopping.list.value;
    api.shopping.items.getOne.mockClear();
    await offlineShopping.check(offlineShopping.items.value[0]!);
    expect(offlineShopping.items.value[0]!.checked).toBe(true);
    expect(api.shopping.items.getOne).not.toHaveBeenCalled();
    expect(queueOnDisk()).toEqual([change("i1", { checked: true })]);
    expect(offlineShopping.offline.value).toBe(true);
    expect(toast.error).not.toHaveBeenCalled();
  });

  test("a request without any answer queues the change instead of failing", async () => {
    const shopping = await opened();
    api.shopping.items.getOne.mockResolvedValue(networkDown);
    await shopping.check(shopping.items.value[0]!);
    expect(queueOnDisk()).toEqual([change("i1", { checked: true })]);
    expect(shopping.items.value[0]!.checked).toBe(true);
    expect(toast.error).not.toHaveBeenCalled();
  });

  test("with the network back the queue is sent in order on top of the fresh items, then the list loads again", async () => {
    const shopping = await opened([item(), item({ id: "i2", foodId: "f2", food: { id: "f2", name: "Butter" } })]);
    api.shopping.items.getOne.mockResolvedValue(networkDown);
    await shopping.check(shopping.items.value[0]!);
    await shopping.change(shopping.items.value[1]!, { quantity: 3 });
    expect(queueOnDisk()).toHaveLength(2);

    api.shopping.items.getOne.mockImplementation(async (id: string) => ({ data: item({ id, note: "Bio" }) }));
    await shopping.reload(true);
    expect(api.shopping.items.updateOne.mock.calls.map(call => call[0])).toEqual(["i1", "i2"]);
    expect(api.shopping.items.updateOne).toHaveBeenCalledWith("i1", expect.objectContaining({ checked: true, note: "Bio" }));
    expect(queueOnDisk()).toEqual([]);
    expect(shopping.offline.value).toBe(false);
  });

  test("an item deleted meanwhile is skipped without a message", async () => {
    const shopping = await opened();
    api.shopping.items.getOne.mockResolvedValue(networkDown);
    await shopping.check(shopping.items.value[0]!);
    api.shopping.items.getOne.mockResolvedValue({ data: null, error: { response: { status: 404 } } });
    await shopping.reload(true);
    expect(api.shopping.items.updateOne).not.toHaveBeenCalled();
    expect(queueOnDisk()).toEqual([]);
    expect(toast.error).not.toHaveBeenCalled();
  });

  test("a food written down offline appears at once and is created when the network is back", async () => {
    const shopping = await opened([]);
    api.shopping.lists.getOne.mockResolvedValue(networkDown);
    api.shopping.items.createMany.mockResolvedValue(networkDown);
    const added = await shopping.addTile({ name: "Butter", emoji: "", foodId: "f2", labelId: null });
    expect(isLocalId(added!.id)).toBe(true);
    expect(shopping.items.value.map(entry => entry.food?.name)).toEqual(["Butter"]);
    expect(queueOnDisk()).toEqual([expect.objectContaining({ kind: "add", foodId: "f2" })]);
    await settle();

    api.shopping.lists.getOne.mockResolvedValue({ data: listWith([]) });
    api.shopping.items.createMany.mockResolvedValue({ data: { createdItems: [item({ id: "real", foodId: "f2" })], updatedItems: [] } });
    await shopping.reload(true);
    await vi.waitFor(() => expect(queueOnDisk()).toEqual([]));
    expect(api.shopping.items.createMany).toHaveBeenLastCalledWith([expect.objectContaining({ shoppingListId: "l1", foodId: "f2", quantity: 0 })]);
    expect(queueOnDisk()).toEqual([]);
  });

  test("an add of a food that is on the list by then merges into it", async () => {
    const shopping = await opened([]);
    api.shopping.lists.getOne.mockResolvedValue(networkDown);
    api.shopping.items.createMany.mockResolvedValue(networkDown);
    await shopping.addTile({ name: "Milch", emoji: "", foodId: "f1", labelId: null }, { quantity: 2, unit: null });
    await settle();
    api.shopping.lists.getOne.mockResolvedValue({ data: listWith([item({ id: "there" })]) });
    api.shopping.items.getOne.mockResolvedValue({ data: item({ id: "there" }) });
    api.shopping.items.createMany.mockClear();
    await shopping.reload(true);
    await vi.waitFor(() => expect(queueOnDisk()).toEqual([]));
    expect(api.shopping.items.createMany).not.toHaveBeenCalled();
    expect(api.shopping.items.updateOne).toHaveBeenCalledWith("there", expect.objectContaining({ quantity: 2 }));
  });

  test("a change of an item made offline is sent with the add, not as a second request", async () => {
    const shopping = await opened([]);
    api.shopping.lists.getOne.mockResolvedValue(networkDown);
    api.shopping.items.createMany.mockResolvedValue(networkDown);
    const added = await shopping.addTile({ name: "Butter", emoji: "", foodId: "f2", labelId: null });
    await shopping.check(added!);
    const queue = queueOnDisk();
    expect(queue).toHaveLength(1);
    expect(queue[0]).toMatchObject({ kind: "add", fields: { checked: true } });
  });

  test("a queue on the device is picked up again after a restart", async () => {
    writeStored("u1", "queue", [change("i1", { checked: true })]);
    writeStored("u1", "lists", [{ id: "l1", name: "Rewe" }]);
    setOnline(false);
    const shopping = useKhShopping();
    api.shopping.lists.getAll.mockResolvedValue(networkDown);
    api.shopping.lists.getOne.mockResolvedValue(networkDown);
    await shopping.start(null);
    expect(shopping.offline.value).toBe(true);
    expect(queueOnDisk()).toEqual([change("i1", { checked: true })]);
  });

  test("changes made while the queue is being sent go behind it, not past it", async () => {
    const shopping = await opened([item(), item({ id: "i2", foodId: "f2", food: { id: "f2", name: "Butter" } })]);
    api.shopping.items.getOne.mockResolvedValue(networkDown);
    await shopping.check(shopping.items.value[0]!);
    let release: (value: unknown) => void = () => {};
    api.shopping.items.getOne.mockReturnValueOnce(new Promise((resolve) => { release = resolve; }));
    const flushing = shopping.reload(true); // the op leaves the queue while it is sent
    api.shopping.items.getOne.mockResolvedValue({ data: item({ id: "i2", foodId: "f2" }) });
    await shopping.change(shopping.items.value[1]!, { quantity: 3 });
    expect(api.shopping.items.updateOne).not.toHaveBeenCalled();
    release({ data: item() });
    await flushing;
    await vi.waitFor(() => expect(api.shopping.items.updateOne.mock.calls.map(call => call[0])).toEqual(["i1", "i2"]));
  });

  test("a change of an item made offline, while its add is being sent, reaches the server item", async () => {
    const shopping = await opened([]);
    api.shopping.lists.getOne.mockResolvedValue(networkDown);
    api.shopping.items.createMany.mockResolvedValue(networkDown);
    const added = await shopping.addTile({ name: "Butter", emoji: "", foodId: "f2", labelId: null });
    await settle();
    let release: (value: unknown) => void = () => {};
    api.shopping.lists.getOne.mockReturnValueOnce(new Promise((resolve) => { release = resolve; }));
    const sending = shopping.reload(true);
    api.shopping.items.createMany.mockResolvedValue({ data: { createdItems: [item({ id: "real", foodId: "f2" })], updatedItems: [] } });
    api.shopping.items.getOne.mockResolvedValue({ data: item({ id: "real", foodId: "f2" }) });
    await shopping.check(added!);
    release({ data: listWith([]) });
    await sending;
    await vi.waitFor(() => expect(api.shopping.items.updateOne).toHaveBeenCalledWith("real", expect.objectContaining({ checked: true })));
    expect(toast.error).not.toHaveBeenCalled();
  });

  test("an add merged into an article that is there by then lets later changes of the local item reach that one", async () => {
    const shopping = await opened([]);
    api.shopping.lists.getOne.mockResolvedValue(networkDown);
    api.shopping.items.createMany.mockResolvedValue(networkDown);
    const added = await shopping.addTile({ name: "Milch", emoji: "", foodId: "f1", labelId: null });
    await settle();
    let release: (value: unknown) => void = () => {};
    api.shopping.lists.getOne.mockReturnValueOnce(new Promise((resolve) => { release = resolve; }));
    const sending = shopping.reload(true);
    api.shopping.items.getOne.mockResolvedValue({ data: item({ id: "there" }) });
    await shopping.setQuantity(added!, "3");
    release({ data: listWith([item({ id: "there" })]) });
    await sending;
    await vi.waitFor(() => expect(api.shopping.items.updateOne).toHaveBeenCalledWith("there", expect.objectContaining({ quantity: 3 })));
  });

  test("an everyday item without a food yet is written down offline by name and its food is made when the network is back", async () => {
    const shopping = await opened([]);
    api.shopping.lists.getOne.mockResolvedValue(networkDown);
    ensureFoodApi.mockResolvedValue(networkDown);
    const added = await shopping.addTile({ name: "Brötchen", emoji: "🥖", labelId: "bak" });
    expect(shopping.items.value.map(entry => entry.food?.name)).toEqual(["Brötchen"]);
    expect(isLocalId(added!.id)).toBe(true);
    expect(queueOnDisk()).toEqual([expect.objectContaining({ kind: "add", foodId: null, name: "Brötchen", labelId: "bak" })]);
    expect(toast.error).not.toHaveBeenCalled();
    await settle();

    api.shopping.lists.getOne.mockResolvedValue({ data: listWith([]) });
    ensureFoodApi.mockResolvedValue({ data: { id: "f9", name: "Brötchen", labelId: "bak" } });
    api.shopping.items.createMany.mockResolvedValue({ data: { createdItems: [item({ id: "real", foodId: "f9" })], updatedItems: [] } });
    await shopping.reload(true);
    await vi.waitFor(() => expect(queueOnDisk()).toEqual([]));
    expect(ensureFoodApi).toHaveBeenLastCalledWith("Brötchen", "bak");
    expect(api.shopping.items.createMany).toHaveBeenLastCalledWith([expect.objectContaining({ foodId: "f9", shoppingListId: "l1" })]);
  });

  test("with no answer for the session the last user's stored lists open", async () => {
    await opened([item()]);
    vi.stubGlobal("useMealieAuth", () => ({ user: { value: null } }));
    setOnline(false);
    api.shopping.lists.getAll.mockResolvedValue(networkDown);
    api.shopping.lists.getOne.mockResolvedValue(networkDown);
    const again = useKhShopping();
    await again.start(null);
    vi.stubGlobal("useMealieAuth", () => ({ user: { value: { id: "u1", householdSlug: "home" } } }));
    expect(again.items.value.map(entry => entry.id)).toEqual(["i1"]);
    expect(again.offline.value).toBe(true);
  });

  test("a signed-out user online gets nothing from the device", async () => {
    await opened([item()]);
    vi.stubGlobal("useMealieAuth", () => ({ user: { value: null } }));
    api.shopping.lists.getAll.mockResolvedValue(networkDown);
    const again = useKhShopping();
    await again.start(null);
    vi.stubGlobal("useMealieAuth", () => ({ user: { value: { id: "u1", householdSlug: "home" } } }));
    expect(again.items.value).toEqual([]);
  });
});

describe("the page opens from the device", () => {
  test("shows the last loaded list at once when the network is away", async () => {
    await opened([item()]);
    foods.value = [];
    api.shopping.lists.getAll.mockResolvedValue(networkDown);
    api.shopping.lists.getOne.mockResolvedValue(networkDown);
    const again = useKhShopping();
    await again.start(null);
    expect(again.lists.value.map(entry => entry.id)).toEqual(["l1"]);
    expect(again.items.value.map(entry => entry.id)).toEqual(["i1"]);
    expect(again.offline.value).toBe(true);
    expect(toast.error).not.toHaveBeenCalled();
  });

  test("keeps the foods for the tiles", async () => {
    await opened();
    vi.useFakeTimers();
    foods.value = [...foods.value];
    await vi.advanceTimersByTimeAsync(1100);
    vi.useRealTimers();
    expect(readStored<{ foods: { name: string }[] }>("u1", "catalog", { foods: [] }).foods.map(food => food.name)).toEqual(["Milch", "Butter"]);
  });

  test("with nothing stored the failure is reported as before", async () => {
    api.shopping.lists.getAll.mockResolvedValue(networkDown);
    await useKhShopping().start(null);
    expect(toast.error).toHaveBeenCalled();
  });

  test("with the add-on off nothing is stored or queued", async () => {
    khAddons.enabled.offline = false;
    const shopping = await opened();
    expect(Object.keys(localStorage).filter(key => key.startsWith("kh-shop-offline"))).toEqual([]);
    api.shopping.items.getOne.mockResolvedValue(networkDown);
    await shopping.check(shopping.items.value[0]!);
    expect(toast.error).toHaveBeenCalled();
    expect(Object.keys(localStorage).filter(key => key.startsWith("kh-shop-offline"))).toEqual([]);
    expect(shopping.offline.value).toBe(false);
  });
});
