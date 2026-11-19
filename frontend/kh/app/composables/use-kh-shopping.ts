// KH: loading and writing for the shopping page (D60): the household's lists, the open list with its items, and every
// action of the tiles (check off, put back, add, change details, remove, new store) on Mealie's shopping list API.
import { alert } from "~/composables/use-toast";
import { useUserApi } from "~/composables/api";
import { useFoodStore } from "~/composables/store/use-food-store";
import { useLabelStore } from "~/composables/store/use-label-store";
import { useUnitStore } from "~/composables/store/use-unit-store";
import type { IngredientFoodOut, IngredientUnitOut } from "~/lib/api/types/recipe";
import { useRequests } from "~/composables/api/api-client";
import { KhAmountsApi } from "../lib/api/amounts";
import { KhShoppingApi } from "../lib/api/shopping";
import type {
  ShoppingListItemOut,
  ShoppingListItemsCollectionOut,
  ShoppingListOut,
  ShoppingListSummary,
} from "~/lib/api/types/household";
import { applyQuantity, foodMatches, pickListId, quantityText, sameAmount, recentItems, sortListItems } from "../lib/shopping-items";
import { type StoreKind, labelSettingsFor } from "../lib/shopping-stores";
import { type Tile, BASICS, catalog, itemForTile } from "../lib/shopping-tiles";

const LAST_LIST_KEY = "kh-shopping-list";

/** The list used last on this device; localStorage may be blocked or empty, then there is none. */
function lastList(): string | null {
  try {
    return localStorage.getItem(LAST_LIST_KEY);
  }
  catch {
    return null;
  }
}

/** What a change of an item may set: the fields the detail sheet edits. */
export type ItemChanges = Partial<Pick<ShoppingListItemOut, "quantity" | "unit" | "unitId" | "note" | "extras" | "checked">>;

export function useKhShopping() {
  const api = useUserApi();
  const khApi = new KhAmountsApi(useRequests());
  const shoppingApi = new KhShoppingApi(useRequests());
  const i18n = useI18n();
  const { store: foods } = useFoodStore();
  const { store: labels } = useLabelStore();
  const { store: units } = useUnitStore();

  const lists = ref<ShoppingListSummary[]>([]);
  const list = ref<ShoppingListOut | null>(null);
  const ready = ref(false);

  /** Says in the person's language that something failed; the null it returns lets the caller stop. */
  function fail(): null {
    alert.error(i18n.t("kh.shopping.failed"));
    return false;
  }

  const items = computed(() => list.value?.listItems ?? []);
  const open = computed(() => sortListItems(items.value));
  const recent = computed(() => recentItems(items.value));
  const recipes = computed(() =>
    Object.fromEntries((list.value?.recipeReferences ?? []).map(ref => [ref.recipeId, ref.recipe.name])),
  );
  const departments = computed(() => {
    const order = [...(list.value?.labelSettings ?? [])].sort((a, b) => a.position - b.position).map(setting => setting.labelId);
    return catalog(foods.value, labels.value, BASICS, order);
  });

  // Answers can arrive out of order (a slow refresh after a quick tap); only the newest request counts.
  let asked = 0;

  /** Loads the list's items again; QUIET keeps the periodic refresh from nagging when the network is away. */
  async function reload(quiet = false) {
    if (!list.value) return;
    const mine = ++asked;
    const { data } = await api.shopping.lists.getOne(list.value.id);
    if (mine !== asked) return;
    if (data) list.value = data;
    else if (!quiet) fail();
  }

  /** Opens a list and remembers it for the next visit on this device. */
  async function select(id: string) {
    const mine = ++asked;
    const { data } = await api.shopping.lists.getOne(id);
    if (mine !== asked) return;
    if (!data) return fail();
    list.value = data;
    try {
      localStorage.setItem(LAST_LIST_KEY, id);
    }
    catch {
      // storing the choice is a convenience only
    }
  }

  async function loadLists() {
    const { data } = await api.shopping.lists.getAll(1, -1);
    if (data) lists.value = data.items;
    else fail();
  }

  /** Loads the lists and opens the one from the address, the last used or the first; with none, READY says so. */
  async function start(fromAddress: string | null) {
    await loadLists();
    const id = pickListId(lists.value.map(entry => entry.id), fromAddress, lastList());
    if (id) await select(id);
    ready.value = true;
  }

  /**
   * Changes the item on the screen at once, saves it, and loads the list again. The item is read fresh before it is
   * saved, so only the changed fields are written and what others did meanwhile (checked it off, say) stays.
   */
  async function change(item: ShoppingListItemOut, changes: ItemChanges) {
    if (list.value) {
      list.value.listItems = list.value.listItems.map(entry => (entry.id === item.id ? { ...entry, ...changes } : entry));
    }
    const { data: fresh } = await api.shopping.items.getOne(item.id);
    if (fresh) {
      const { error } = await api.shopping.items.updateOne(item.id, { ...fresh, ...changes });
      if (error) fail();
    }
    else {
      fail();
    }
    await reload(true);
  }

  const check = (item: ShoppingListItemOut) => change(item, { checked: true });
  const uncheck = (item: ShoppingListItemOut) => change(item, { checked: false });

  async function remove(item: ShoppingListItemOut) {
    if (list.value) list.value.listItems = list.value.listItems.filter(entry => entry.id !== item.id);
    const { error } = await api.shopping.items.deleteOne(item.id);
    if (error) fail();
    await reload(true);
  }

  /** The food called NAME, made (with LABEL-ID, the department) when the group has none, by the server so that a member without the permission to organize may do it too; null when it fails. */
  async function ensureFood(name: string, labelId: string | null): Promise<IngredientFoodOut | null> {
    const there = foods.value.find(food => foodMatches(food, name));
    if (there) return there;
    const { data } = await shoppingApi.ensureFood(name, labelId);
    if (!data) return fail();
    if (!foods.value.some(entry => entry.id === data.id)) foods.value.push(data);
    return data;
  }

  /** The unit the group lacks for a quantity chip, made by the server (also for members who may not organize); null when it fails. */
  async function makeUnit(abbreviation: string): Promise<IngredientUnitOut | null> {
    const { data } = await shoppingApi.ensureUnit(abbreviation);
    if (!data) return fail();
    if (!units.value.some(entry => entry.id === data.id)) units.value.push(data);
    return data;
  }

  /**
   * Puts a food on the list and returns the item for the detail sheet. An item bought before comes back instead of
   * a second one; an open one just opens.
   */
  async function addFood(
    food: IngredientFoodOut,
    details: { quantity?: number | null; unitId?: string | null; note?: string } = {},
  ) {
    const current = list.value;
    if (!current) return null;
    const tile: Tile = { name: food.name, emoji: "", foodId: food.id, labelId: food.labelId };
    // the unit may be newer than the page's list of units; Mealie only needs its id
    const unit = units.value.find(entry => entry.id === details.unitId) ?? null;
    const unitId = details.unitId ?? null;
    // an article already on the list (or bought before) takes what was typed instead of a second tile
    const typed: ItemChanges = details.quantity ? { quantity: details.quantity, unit, unitId } : {};
    if (details.note) typed.note = details.note;
    const there = itemForTile(tile, current.listItems.filter(entry => !entry.checked));
    if (there) {
      if (Object.keys(typed).length) await change(there, typed);
      return there;
    }
    const bought = itemForTile(tile, current.listItems.filter(entry => entry.checked));
    if (bought) {
      await change(bought, { ...typed, checked: false });
      return bought;
    }
    const position = Math.max(0, ...current.listItems.map(entry => entry.position)) + 1;
    const { data, error } = await api.shopping.items.createMany([{
      shoppingListId: current.id,
      foodId: food.id,
      food,
      unit,
      unitId,
      note: details.note ?? "",
      labelId: food.labelId,
      quantity: details.quantity ?? 0,
      checked: false,
      position,
    }]);
    if (error || !data) {
      fail();
      return null;
    }
    const answer = data as ShoppingListItemsCollectionOut;
    await reload(true);
    return answer.createdItems[0] ?? answer.updatedItems[0] ?? null;
  }

  /** Puts a tile on the list (an everyday item becomes a food of the group once) with an amount typed in the search. */
  async function addTile(tile: Tile, amount?: { quantity: number | null; unit: { id: string } | null }) {
    const food = tile.foodId ? foods.value.find(entry => entry.id === tile.foodId) : await ensureFood(tile.name, tile.labelId);
    return food ? addFood(food, { quantity: amount?.quantity, unitId: amount?.unit?.id }) : null;
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

  /** Makes a list for a store, with the departments in that kind of store's walking order, and opens it. */
  async function createStore(name: string, kind: StoreKind) {
    const { data: created } = await api.shopping.lists.createOne({ name });
    if (!created) return fail();
    const { error } = await api.shopping.lists.updateLabelSettings(created.id, labelSettingsFor(kind, created.id, created.labelSettings));
    if (error) fail();
    await loadLists();
    await select(created.id);
  }

  return { lists, list, ready, items, open, recent, recipes, departments, units, start, select, reload, change, check, uncheck, remove, addTile, addTyped, setQuantity, createStore };
}
