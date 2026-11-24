// KH: loading and writing for the shopping page (D60): the household's lists, the open list with its items, and every
// action of the tiles (check off, put back, add, change details, remove, new store) on Mealie's shopping list API.
// Without network (D63) the last loaded lists are shown from the device and changes wait in a queue until it is back.
import { until, useDebounceFn } from "@vueuse/core";
import { alert } from "~/composables/use-toast";
import { useUserApi } from "~/composables/api";
import { useFoodStore } from "~/composables/store/use-food-store";
import { useLabelStore } from "~/composables/store/use-label-store";
import { useUnitStore } from "~/composables/store/use-unit-store";
import type { IngredientFoodOut, IngredientUnitOut } from "~/lib/api/types/recipe";
import type { MultiPurposeLabelOut } from "~/lib/api/types/labels";
import { useRequests } from "~/composables/api/api-client";
import { KhAmountsApi } from "../lib/api/amounts";
import { KhShoppingApi } from "../lib/api/shopping";
import type {
  ShoppingListItemCreate,
  ShoppingListItemOut,
  ShoppingListItemsCollectionOut,
  ShoppingListOut,
  ShoppingListSummary,
} from "~/lib/api/types/household";
import { applyQuantity, cleanListName, foodLink, foodMatches, lastList, pickListId, rememberList, quantityText, sameAmount, recentItems, sortListItems } from "../lib/shopping-items";
import {
  type Fields, type Outcome, type QueuedOp, enqueue, isLocalId, lastUser, newLocalId, noAnswer, readStored, rememberUser, replay, writeStored,
} from "../lib/shopping-offline";
import { type StoreKind, labelSettingsFor } from "../lib/shopping-stores";
import { type Tile, BASICS, catalog, existingFor, isOnHand } from "../lib/shopping-tiles";
import { khAddons } from "./use-kh-addons";
import { useKhOnline } from "./use-kh-connection";

/** What a change of an item may set: the fields the detail sheet edits. */
export type ItemChanges = Partial<Pick<ShoppingListItemOut, "quantity" | "unit" | "unitId" | "note" | "extras" | "checked" | "food" | "foodId">>;

/** The foods the page keeps for offline use: what the tiles and the on-hand state need (not aliases and the like). */
const trimFood = (food: IngredientFoodOut) => ({
  id: food.id,
  name: food.name,
  pluralName: food.pluralName,
  labelId: food.labelId,
  householdsWithIngredientFood: food.householdsWithIngredientFood,
});

interface Catalog {
  foods: IngredientFoodOut[];
  labels: MultiPurposeLabelOut[];
  units: IngredientUnitOut[];
}

const NAME = { lists: "lists", catalog: "catalog", queue: "queue", list: (id: string) => `list-${id}` };

export function useKhShopping() {
  const api = useUserApi();
  const khApi = new KhAmountsApi(useRequests());
  const shoppingApi = new KhShoppingApi(useRequests());
  const i18n = useI18n();
  const auth = useMealieAuth();
  const { store: foods } = useFoodStore();
  const { store: labels } = useLabelStore();
  const { store: units } = useUnitStore();

  const lists = ref<ShoppingListSummary[]>([]);
  const list = ref<ShoppingListOut | null>(null);
  const ready = ref(false);

  // Offline use (D63): only for the signed-in user and while the add-on is on
  const online = useKhOnline(); // the browser has a network and the server answers (D63)
  // Without network the session may not have loaded (no user): then the last user of this device stands in
  const userId = () => auth.user.value?.id ?? (online.value ? "" : lastUser());
  const householdSlug = () => auth.user.value?.householdSlug ?? "";
  const keeping = () => khAddons.enabled.offline && !!userId();
  const keep = (name: string, value: unknown) => {
    if (keeping()) writeStored(userId(), name, value);
  };
  const queue = ref<QueuedOp[]>([]); // read by start(), when the session is settled
  const unanswered = ref(false); // the last request got no answer
  const offline = computed(() => keeping() && (!online.value || unanswered.value || queue.value.length > 0));
  // The ids the server gave to items made offline, for changes that were queued against their local ids
  const madeIds = new Map<string, string>();
  let flushing = false;

  function saveQueue(next: QueuedOp[]) {
    queue.value = next;
    keep(NAME.queue, next);
  }

  const saveList = () => {
    if (list.value) keep(NAME.list(list.value.id), list.value);
  };

  /** Keeps the stores' foods, labels and units, which the tiles need; never an empty list over a good one. */
  const saveCatalog = useDebounceFn(() => {
    if (foods.value.length) keep(NAME.catalog, { foods: foods.value.map(trimFood), labels: labels.value, units: units.value });
  }, 1000);
  watch([foods, labels, units], saveCatalog);

  /** Says in the person's language that something failed; the null it returns lets the caller stop. */
  function fail(): null {
    alert.error(i18n.t("kh.shopping.failed"));
    return null;
  }

  /** What the page can show before the network answers: the stored lists, the one it will open, and the stores' data. */
  function showStored(fromAddress: string | null) {
    if (!keeping()) return;
    if (auth.user.value) rememberUser(userId());
    if (!queue.value.length) queue.value = readStored<QueuedOp[]>(userId(), NAME.queue, []);
    const stored = readStored<ShoppingListSummary[]>(userId(), NAME.lists, []);
    if (!stored.length) return;
    lists.value = stored;
    const id = pickListId(stored.map(entry => entry.id), fromAddress, lastList());
    list.value = id ? readStored<ShoppingListOut | null>(userId(), NAME.list(id), null) : null;
    const known = readStored<Catalog | null>(userId(), NAME.catalog, null);
    if (known && !foods.value.length) {
      foods.value = known.foods;
      labels.value = known.labels;
      units.value = known.units;
    }
  }

  const items = computed(() => list.value?.listItems ?? []);
  const open = computed(() => sortListItems(items.value));
  const recent = computed(() => recentItems(items.value));
  const recipes = computed(() =>
    Object.fromEntries((list.value?.recipeReferences ?? []).map(ref => [ref.recipeId, ref.recipe.name])),
  );
  const departments = computed(() => {
    const order = [...(list.value?.labelSettings ?? [])].sort((a, b) => a.position - b.position).map(setting => setting.labelId);
    return catalog(foods.value, labels.value, BASICS, order, householdSlug());
  });

  // Answers can arrive out of order (a slow refresh after a quick tap); only the newest request counts.
  let asked = 0;

  /**
   * Loads the list's items again; QUIET keeps the periodic refresh from nagging when the network is away. Changes
   * still waiting in the queue are sent first, so the answer cannot undo them on the screen.
   */
  async function reload(quiet = false) {
    if (!list.value) return;
    if (queue.value.length || flushing) return flush();
    const mine = ++asked;
    const { data, error } = await api.shopping.lists.getOne(list.value.id);
    if (mine !== asked) return;
    unanswered.value = noAnswer(error);
    if (data) {
      list.value = data;
      saveList();
    }
    else if (!quiet) fail();
  }

  /** Opens a list and remembers it for the next visit on this device; without network the stored copy opens. */
  async function select(id: string) {
    if (queue.value.length) await flush();
    const mine = ++asked;
    const { data, error } = await api.shopping.lists.getOne(id);
    if (mine !== asked) return;
    unanswered.value = noAnswer(error);
    const stored = !data && keeping() && noAnswer(error) ? readStored<ShoppingListOut | null>(userId(), NAME.list(id), null) : null;
    if (!data && !stored) return fail();
    list.value = data ?? stored;
    saveList();
    rememberList(id);
  }

  async function loadLists() {
    const { data, error } = await api.shopping.lists.getAll(1, -1);
    if (data) {
      lists.value = data.items;
      keep(NAME.lists, data.items);
    }
    else if (noAnswer(error) && keeping() && lists.value.length) unanswered.value = true; // the stored lists stay
    else fail();
  }

  /** Loads the lists and opens the one from the address, the last used or the first; with none, READY says so. */
  async function start(fromAddress: string | null) {
    showStored(fromAddress);
    await loadLists();
    const id = pickListId(lists.value.map(entry => entry.id), fromAddress, lastList());
    if (id) await select(id);
    ready.value = true;
    void linkFoods();
  }

  /** The id the server knows an item by: items made offline get theirs when their add has been sent. */
  const serverId = (id: string) => madeIds.get(id) ?? id;

  /** Writes the changed fields on top of the item as the server has it now; no answer, a vanished item or a refusal come back as the outcome. */
  async function sendChange(id: string, changes: Fields): Promise<Outcome> {
    const real = serverId(id);
    if (isLocalId(real)) return "gone";
    const { data: fresh, error } = await api.shopping.items.getOne(real);
    if (!fresh) return noAnswer(error) ? "offline" : "gone";
    const { error: refused } = await api.shopping.items.updateOne(real, { ...fresh, ...changes });
    return refused ? (noAnswer(refused) ? "offline" : "failed") : "done";
  }

  /** Deletes the item; one that is gone already is as good as deleted. */
  async function sendRemove(id: string): Promise<Outcome> {
    const real = serverId(id);
    if (isLocalId(real)) return "gone";
    const { error } = await api.shopping.items.deleteOne(real);
    if (!error) return "done";
    if (noAnswer(error)) return "offline";
    return (error as { response?: { status?: number } }).response?.status === 404 ? "gone" : "failed";
  }

  /** Puts a food on the list as the server has it now: an article already there (open or bought) takes the fields, else a new item. */
  async function sendAdd(op: Extract<QueuedOp, { kind: "add" }>): Promise<Outcome> {
    const { data: fresh, error } = await api.shopping.lists.getOne(op.listId);
    if (!fresh) return noAnswer(error) ? "offline" : "gone";
    // an article the group has no food for yet is made now, by the server
    const { food, error: unmade } = op.foodId
      ? { food: foods.value.find(entry => entry.id === op.foodId), error: null }
      : await makeFood(op.name, op.labelId);
    if (!food) return noAnswer(unmade) ? "offline" : "failed";
    const tile: Tile = { name: food.name, emoji: "", foodId: food.id, labelId: food.labelId };
    const there = existingFor(tile, fresh.listItems, op.fields, units.value);
    if (there) {
      madeIds.set(op.tempId, there.item.id); // later changes of the local item belong to it
      return sendChange(there.item.id, there.changes);
    }
    const position = Math.max(0, ...fresh.listItems.map(entry => entry.position)) + 1;
    const { data, error: refused } = await api.shopping.items.createMany([newItem(op.listId, food, op.fields, position)]);
    if (refused) return noAnswer(refused) ? "offline" : "failed";
    const created = (data as ShoppingListItemsCollectionOut | null)?.createdItems[0];
    if (created) madeIds.set(op.tempId, created.id);
    return "done";
  }

  const sendOp = (op: QueuedOp): Promise<Outcome> =>
    op.kind === "change" ? sendChange(op.itemId, op.changes) : op.kind === "remove" ? sendRemove(op.itemId) : sendAdd(op);

  /** Sends what was changed offline, oldest first, and loads the list again; does nothing while the network is away or a replay runs. */
  async function flush() {
    if (flushing || !queue.value.length || !online.value) return;
    flushing = true;
    try {
      if (await replay({ get: () => queue.value, set: saveQueue }, sendOp)) fail();
    }
    finally {
      flushing = false;
    }
    unanswered.value = queue.value.length > 0;
    if (!queue.value.length) await reload(true);
  }
  watch(online, (now) => {
    if (now) void flush();
  });

  /** Whether a change now only goes into the queue: the network is away, or earlier changes wait or are being sent (the order stays). */
  const queueing = () => keeping() && (flushing || queue.value.length > 0 || !online.value);

  /** Sends OP now, or queues it; with no network the queue takes it, anything else that fails is reported. */
  async function send(op: QueuedOp) {
    if (queueing()) {
      saveQueue(enqueue(queue.value, op));
      return flush();
    }
    const outcome = await sendOp(op);
    unanswered.value = outcome === "offline";
    if (outcome === "offline" && keeping()) saveQueue(enqueue(queue.value, op));
    else if (outcome !== "done") fail();
    await reload(true);
  }

  /**
   * Changes the item on the screen at once, saves it, and loads the list again. The item is read fresh before it is
   * saved, so only the changed fields are written and what others did meanwhile (checked it off, say) stays.
   */
  async function change(item: ShoppingListItemOut, changes: ItemChanges) {
    if (list.value) {
      list.value.listItems = list.value.listItems.map(entry => (entry.id === item.id ? { ...entry, ...changes } : entry));
      saveList();
    }
    await send({ kind: "change", itemId: item.id, changes });
  }

  const check = (item: ShoppingListItemOut) => change(item, { checked: true });
  const uncheck = (item: ShoppingListItemOut) => change(item, { checked: false });

  async function remove(item: ShoppingListItemOut) {
    if (list.value) {
      list.value.listItems = list.value.listItems.filter(entry => entry.id !== item.id);
      saveList();
    }
    await send({ kind: "remove", itemId: item.id });
  }

  /** The food called NAME, made (with LABEL-ID, the department) when the group has none, by the server so that a member without the permission to organize may do it too; the error says why there is none. */
  async function makeFood(name: string, labelId: string | null): Promise<{ food: IngredientFoodOut | null; error: unknown }> {
    const there = foods.value.find(food => foodMatches(food, name));
    if (there) return { food: there, error: null };
    const { data, error } = await shoppingApi.ensureFood(name, labelId);
    if (data && !foods.value.some(entry => entry.id === data.id)) foods.value.push(data);
    return { food: data, error };
  }

  /** makeFood for a caller that tells the person when it fails; null then. */
  async function ensureFood(name: string, labelId: string | null): Promise<IngredientFoodOut | null> {
    return (await makeFood(name, labelId)).food ?? fail();
  }

  /** The unit the group lacks for a quantity chip, made by the server (also for members who may not organize); null when it fails. */
  async function makeUnit(abbreviation: string): Promise<IngredientUnitOut | null> {
    const { data } = await shoppingApi.ensureUnit(abbreviation);
    if (!data) return fail();
    if (!units.value.some(entry => entry.id === data.id)) units.value.push(data);
    return data;
  }

  /** A new item for the list as the server wants it: FOOD with the FIELDS set on top of an empty item. */
  function newItem(listId: string, food: IngredientFoodOut, fields: Fields, position: number): ShoppingListItemCreate {
    return {
      shoppingListId: listId,
      foodId: food.id,
      food,
      unit: null,
      unitId: null,
      note: "",
      labelId: food.labelId,
      quantity: 0,
      checked: false,
      position,
      ...fields,
    };
  }

  /** What an item is wanted for: a food of the group, or just a name (and department) while the group has no such food and the network is away. */
  type Wanted = { name: string; labelId: string | null; food?: IngredientFoodOut };

  /** Puts the article on the screen at once as an item that only exists here, and queues its add for when the network is back. */
  function addHere(current: ShoppingListOut, wanted: Wanted, fields: Fields, position: number): ShoppingListItemOut {
    const now = new Date().toISOString();
    // without a food yet the stand-in carries just the name, which is what the tiles and titles read
    const food = wanted.food ?? ({ id: "", name: wanted.name, labelId: wanted.labelId } as IngredientFoodOut);
    const item = {
      extras: {},
      recipeReferences: [],
      label: null,
      referencedRecipe: null,
      display: "",
      groupId: current.groupId,
      householdId: current.householdId,
      createdAt: now,
      updatedAt: now,
      ...newItem(current.id, food, fields, position),
      foodId: wanted.food?.id ?? null,
      id: newLocalId(),
    } as ShoppingListItemOut;
    current.listItems = [...current.listItems, item];
    saveList();
    saveQueue(enqueue(queue.value, {
      kind: "add", tempId: item.id, listId: current.id, foodId: wanted.food?.id ?? null, name: wanted.name, labelId: wanted.labelId, fields,
    }));
    void flush();
    return item;
  }

  /**
   * Puts an article on the list and returns the item for the detail sheet. An item bought before comes back instead of
   * a second one; an open one just opens. Without network the item appears at once and is sent later.
   */
  async function addItem(
    wanted: Wanted,
    details: { quantity?: number | null; unitId?: string | null; note?: string } = {},
  ) {
    const current = list.value;
    if (!current) return null;
    const tile: Tile = { name: wanted.name, emoji: "", foodId: wanted.food?.id, labelId: wanted.labelId };
    // the unit may be newer than the page's list of units; Mealie only needs its id
    const unit = units.value.find(entry => entry.id === details.unitId) ?? null;
    const unitId = details.unitId ?? null;
    // an article already on the list (or bought before) takes what was typed instead of a second tile
    // an amount typed without a unit ("2 Milch") keeps the unit the item has ("1 L" becomes "2 L")
    const typed: ItemChanges = details.quantity ? { quantity: details.quantity, ...(unitId ? { unit, unitId } : {}) } : {};
    if (details.note) typed.note = details.note;
    const there = existingFor(tile, current.listItems, typed, units.value);
    if (there) {
      if (Object.keys(there.changes).length) await change(there.item, there.changes);
      return there.item;
    }
    const position = Math.max(0, ...current.listItems.map(entry => entry.position)) + 1;
    if (queueing() || !wanted.food) return addHere(current, wanted, typed, position);
    const { data, error } = await api.shopping.items.createMany([newItem(current.id, wanted.food, typed, position)]);
    if (noAnswer(error) && keeping()) {
      unanswered.value = true;
      return addHere(current, wanted, typed, position);
    }
    if (error || !data) {
      fail();
      return null;
    }
    const answer = data as ShoppingListItemsCollectionOut;
    await reload(true);
    return answer.createdItems[0] ?? answer.updatedItems[0] ?? null;
  }

  const addFood = (food: IngredientFoodOut, details: { quantity?: number | null; unitId?: string | null; note?: string } = {}) =>
    addItem({ name: food.name, labelId: food.labelId, food }, details);

  /**
   * Puts a tile on the list (an everyday item becomes a food of the group once) with an amount typed in the search.
   * While the network is away an everyday item is put on the list by name, and its food is made when it is back.
   */
  async function addTile(tile: Tile, amount?: { quantity: number | null; unit: { id: string } | null }) {
    const details = { quantity: amount?.quantity, unitId: amount?.unit?.id };
    let food = tile.foodId ? foods.value.find(entry => entry.id === tile.foodId) : undefined;
    if (!food && !tile.foodId && !queueing()) {
      const made = await makeFood(tile.name, tile.labelId);
      if (!made.food && !(noAnswer(made.error) && keeping())) return fail();
      food = made.food ?? undefined;
    }
    return tile.foodId && !food ? null : addItem({ name: tile.name, labelId: tile.labelId, food }, details);
  }

  /** Reads a typed line on the server ("2 Liter Milch 3,5 %") and puts the article on the list with what it says. */
  async function addTyped(text: string) {
    const { data: line } = await khApi.parseLine(text);
    if (!line) return fail();
    const labelId = departments.value.flatMap(department => department.tiles)
      .find(tile => tile.name.toLowerCase() === line.name.toLowerCase())?.labelId ?? null;
    const food = line.foodId ? (await api.foods.getOne(line.foodId)).data : await ensureFood(line.name, labelId);
    if (!food) return null;
    const unit = !line.unitId && line.unitAbbreviation ? await makeUnit(line.unitAbbreviation) : null;
    if (line.unitAbbreviation && !line.unitId && !unit) return null;
    return addFood(food, { quantity: line.quantity, unitId: line.unitId ?? unit?.id, note: line.note });
  }

  /** Sets the amount of a chip, replacing the old one with its unit; the chosen amount again clears it. */
  async function setQuantity(item: ShoppingListItemOut, chip: string) {
    if (sameAmount(chip, quantityText(item))) return change(item, { quantity: 0, unit: null, unitId: null });
    const { quantity, unitId, createUnit } = applyQuantity(chip, units.value);
    const unit = createUnit ? await makeUnit(createUnit.abbreviation) : (units.value.find(entry => entry.id === unitId) ?? null);
    if (createUnit && !unit) return;
    await change(item, { quantity, unit, unitId: unit?.id ?? null });
  }

  /**
   * Links the open items without a food (a recipe's "ml Milch") to the group's food of that name, once the foods are
   * loaded, so that adding the food again merges with them; a note with an amount or a unit the group lacks stays.
   */
  async function linkFoods() {
    await until(foods).toMatch(known => known.length > 0, { timeout: 5000 });
    for (const item of open.value) {
      const link = foods.value.length && !queueing() ? foodLink(item, foods.value, units.value) : null;
      if (!link || open.value.some(other => other.foodId === link.food.id)) continue;
      await change(item, { foodId: link.food.id, food: link.food, note: link.note, ...(link.unit && { unit: link.unit, unitId: link.unit.id }) });
    }
  }
  /** Whether the household always has the food in the house (D65). */
  const onHand = (foodId: string | null | undefined) => isOnHand(foods.value.find(food => food.id === foodId), householdSlug());

  /** Marks the food as always in the house for the household, or clears it; the server lets every member do it. */
  async function setOnHand(foodId: string, value: boolean) {
    const { data } = await shoppingApi.setOnHand(foodId, value);
    if (!data) return fail();
    const at = foods.value.findIndex(food => food.id === foodId);
    if (at >= 0) foods.value[at] = data;
  }

  /** Makes a list for a store, with the departments in that kind of store's walking order, and opens it. */
  async function createStore(name: string, kind: StoreKind) {
    const { data: created } = await api.shopping.lists.createOne({ name });
    if (!created) return fail();
    const { error } = await api.shopping.lists.updateLabelSettings(created.id, labelSettingsFor(kind, created.id, created.labelSettings));
    if (error) fail();
    await loadLists();
    await select(created.id);
  }

  /**
   * Gives the open list a new name. The fresh list is read first and written back with only the name changed (the
   * update leaves the items alone, they are not part of what it stores); the new name shows in the store chips and the
   * header at once. Needs the connection; a blank name is refused.
   */
  async function rename(raw: string): Promise<boolean> {
    const name = cleanListName(raw);
    if (!list.value || !name || offline.value) return false;
    const { data: fresh } = await api.shopping.lists.getOne(list.value.id);
    const { data, error } = fresh ? await api.shopping.lists.updateOne(fresh.id, { ...fresh, name }) : { data: null, error: null };
    if (!data || error) {
      fail();
      return false;
    }
    list.value = { ...list.value, name: data.name };
    lists.value = lists.value.map(entry => (entry.id === data.id ? { ...entry, name: data.name } : entry));
    saveList();
    keep(NAME.lists, lists.value);
    return true;
  }
  return { rename, lists, list, ready, items, open, recent, recipes, departments, units, offline, start, select, reload, change, check, uncheck, remove, addTile, addTyped, setQuantity, createStore, onHand, setOnHand };
}
