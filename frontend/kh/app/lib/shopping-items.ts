// KH: the details of a shopping list item on the shopping page (D60): the chips of the detail sheet, how quantity,
// properties and urgency are stored in Mealie's item fields, and how items are sorted and titled for the tiles.
import { mdiBird, mdiFire, mdiSale } from "@mdi/js";

/** The fields of one of Mealie's list items that this page reads (ShoppingListItemOut fits). */
export interface ShopItem {
  checked: boolean;
  position: number;
  quantity: number;
  unit?: { name: string; abbreviation?: string | null } | null;
  food?: { name: string } | null;
  note: string | null;
  extras?: Record<string, unknown> | null;
  updatedAt: string | null;
  recipeReferences?: { recipeId: string }[];
}

export interface ShopUnit {
  id: string;
  name: string;
  abbreviation?: string | null;
  pluralName?: string | null;
  pluralAbbreviation?: string | null;
}

export type Urgency = "urgent" | "offer" | "whenever";

/** Where the urgency is kept (Mealie's free "extras" of an item), so no migration is needed. */
export const URGENCY_EXTRA = "kh_urgency";

export const QUANTITY_CHIPS = ["1", "2", "3", "4", "6", "10", "100 g", "250 g", "500 g", "1 kg", "1 l"];
export const PROPERTY_CHIPS = ["Bio", "laktosefrei", "vegan", "glutenfrei", "klein", "groß"];

/** The urgency chips: the text is the key of a translation, the icon one of Material Design Icons. */
export const URGENCY: { key: Urgency; labelKey: string; icon: string }[] = [
  { key: "urgent", labelKey: "kh.shopping.urgent", icon: mdiFire },
  { key: "offer", labelKey: "kh.shopping.offer", icon: mdiSale },
  { key: "whenever", labelKey: "kh.shopping.whenever", icon: mdiBird },
];

/** The most tiles "Zuletzt gekauft" shows. */
export const RECENT_LIMIT = 12;

/** What a quantity chip sets: the amount and the unit, which is to be created (CREATE_UNIT) if the group lacks it. */
export interface QuantityChange {
  quantity: number;
  unitId?: string;
  createUnit?: { name: string; abbreviation: string };
}

// The units the quantity chips use, written as a group usually has them; made when missing
const STANDARD_UNITS: Record<string, { name: string; abbreviation: string }> = {
  g: { name: "Gramm", abbreviation: "g" },
  kg: { name: "Kilogramm", abbreviation: "kg" },
  l: { name: "Liter", abbreviation: "l" },
  ml: { name: "Milliliter", abbreviation: "ml" },
};

/** The unit of UNITS named WORD by name, plural, abbreviation or plural abbreviation, ignoring case. */
function findUnit<T extends ShopUnit>(word: string, units: T[]): T | undefined {
  const wanted = word.replace(/\.$/, "").toLowerCase();
  return units.find(unit =>
    [unit.name, unit.pluralName, unit.abbreviation, unit.pluralAbbreviation].some(text => text?.replace(/\.$/, "").toLowerCase() === wanted),
  );
}

/** "250 g" sets 250 and the group's unit "g"; a unit the group lacks (g, kg, l, ml) is to be created. */
export function applyQuantity(chip: string, units: ShopUnit[]): QuantityChange {
  const match = chip.trim().match(/^(\d+(?:[.,]\d+)?)(?:\s+(\S+))?$/);
  if (!match) return { quantity: 1 };
  const quantity = Number(match[1]!.replace(",", "."));
  if (!match[2]) return { quantity };
  const unit = findUnit(match[2], units);
  if (unit) return { quantity, unitId: unit.id };
  const standard = STANDARD_UNITS[match[2].toLowerCase()];
  return standard ? { quantity, createUnit: standard } : { quantity };
}

const AMOUNT = /^\s*(\d+\s+\d+\/\d+|\d+\/\d+|\d+(?:[.,]\d+)?|[¼½¾])\s*/;
const VULGAR: Record<string, number> = { "¼": 0.25, "½": 0.5, "¾": 0.75 };

/** The value of an amount as typed: "1,5", "1/2", "1 1/2" or "½". */
function amountValue(text: string): number {
  if (text in VULGAR) return VULGAR[text]!;
  const mixed = text.match(/^(?:(\d+)\s+)?(\d+)\/(\d+)$/);
  if (mixed) return Number(mixed[1] ?? 0) + Number(mixed[2]) / Number(mixed[3]);
  return Number(text.replace(",", "."));
}

/** A leading amount of TEXT and a unit word the group knows after it; REST is the article. A unit word with nothing after it is the article. */
export function splitLeadingAmount<T extends ShopUnit>(text: string, units: T[]): { quantity: number | null; unit: T | null; rest: string } {
  const amount = text.match(AMOUNT);
  if (!amount) return { quantity: null, unit: null, rest: text.trim() };
  const rest = text.slice(amount[0].length).trim();
  const word = rest.match(/^(\S+)\s+(.+)$/);
  const unit = word ? findUnit(word[1]!, units) : undefined;
  return { quantity: amountValue(amount[1]!), unit: unit ?? null, rest: unit ? word![2]!.trim() : rest };
}

/** The unit a word names: one of the group's units, else g, kg, l or ml (by abbreviation or name); null for any other word. */
function unitWord(word: string, units: ShopUnit[]): Pick<ShopUnit, "name" | "abbreviation"> | null {
  const lower = word.toLowerCase();
  return findUnit(word, units) ?? STANDARD_UNITS[lower] ?? Object.values(STANDARD_UNITS).find(unit => unit.name.toLowerCase() === lower) ?? null;
}

/** A leading unit word of TEXT ("ml Milch") and the rest; null when the text does not start with a unit followed by an article. */
export function splitUnitWord(text: string, units: ShopUnit[] = []): { unit: Pick<ShopUnit, "name" | "abbreviation">; rest: string } | null {
  const word = text.trim().match(/^(\S+)\s+(.+)$/);
  const unit = word && unitWord(word[1]!, units);
  return unit ? { unit, rest: word![2]!.trim() } : null;
}

/**
 * The first words of a note-only line (made elsewhere) as article, amount and extra: "2 Liter Milch 3,5 %" has the
 * article Milch, 2 Liter and 3,5 %. A recipe's ingredient without a food comes as the note "ml Milch" with the amount
 * in the item's own quantity; its leading unit word is the unit then, not part of the article.
 */
function splitOldLine(own: string, units: ShopUnit[]) {
  const lead = splitLeadingAmount(own, units);
  const loose = lead.quantity === null ? splitUnitWord(lead.rest, units) : null;
  const rest = loose?.rest ?? lead.rest;
  const unit: Pick<ShopUnit, "name" | "abbreviation"> | null = loose?.unit ?? lead.unit;
  const extra = rest.match(/^(.*\S)\s+(\d[\d,.]*)\s?%$/);
  return { title: extra ? extra[1]! : rest, quantity: lead.quantity, unit, extra: extra ? `${extra[2]} %` : "" };
}

const ENDINGS = ["en", "er", "e", "n", "s"];

const cutEnding = (word: string) => {
  const ending = ENDINGS.find(candidate => word.endsWith(candidate) && word.length - candidate.length >= 2);
  return ending ? word.slice(0, -ending.length) : word;
};

/** Whether a food is the one called NAME: by its name or plural, ignoring case and singular or plural. */
export function foodMatches(food: { name: string; pluralName?: string | null }, name: string): boolean {
  const wanted = name.trim().toLowerCase();
  const forms = [wanted, cutEnding(wanted)];
  return [food.name, food.pluralName].some((text) => {
    const form = text?.trim().toLowerCase();
    return !!form && (forms.includes(form) || forms.includes(cutEnding(form)));
  });
}

/** Quantity and unit as the chips write them ("250 g", "2"); "" when the item has no amount. */
export function quantityText(item: Pick<ShopItem, "quantity" | "unit">): string {
  if (!item.quantity || item.quantity <= 0) return "";
  const amount = String(Math.round(item.quantity * 100) / 100).replace(".", ",");
  const unit = item.unit ? (item.unit.abbreviation || item.unit.name) : "";
  return unit ? `${amount} ${unit}` : amount;
}

/** Whether two amounts as written are the same, ignoring case ("1 L" is "1 l"). */
export const sameAmount = (a: string, b: string): boolean => !!a && a.toLowerCase() === b.toLowerCase();

/** The leading property words of a note and the rest of it, the person's own text. */
export function splitNote(note: string | null): { properties: string[]; own: string } {
  const properties: string[] = [];
  let rest = note ?? "";
  for (;;) {
    const match = rest.match(/^\s*([^,]+?)\s*(?:,|$)/);
    const property = match && PROPERTY_CHIPS.find(chip => chip.toLowerCase() === match[1]!.toLowerCase());
    if (!match || !property) break;
    properties.push(property);
    rest = rest.slice(match[0].length);
  }
  return { properties, own: rest.trim() };
}

/** A note from properties (first, comma-separated) and the own text. */
export function joinNote(properties: string[], own: string): string {
  return [...properties, own.trim()].filter(Boolean).join(", ");
}

/** The note with PROP added, or removed when it is there. */
export function toggleProperty(note: string | null, property: string): string {
  const { properties, own } = splitNote(note);
  return joinNote(properties.includes(property) ? properties.filter(p => p !== property) : [...properties, property], own);
}

/** The note with its own text replaced. */
export function withOwnText(note: string | null, own: string): string {
  return joinNote(splitNote(note).properties, own);
}

/** The urgency stored on an item; "" for none or an unknown value. */
export function urgencyOf(item: Pick<ShopItem, "extras">): Urgency | "" {
  const value = item.extras?.[URGENCY_EXTRA];
  return URGENCY.some(entry => entry.key === value) ? (value as Urgency) : "";
}

const URGENCY_RANK: Record<Urgency | "", number> = { "urgent": 0, "": 1, "offer": 1, "whenever": 2 };

/** The open items, urgent first, "whenever" last, otherwise in the order of their position. */
export function sortListItems<T extends ShopItem>(items: T[]): T[] {
  return items
    .filter(item => !item.checked)
    .sort((a, b) => URGENCY_RANK[urgencyOf(a)] - URGENCY_RANK[urgencyOf(b)] || a.position - b.position);
}

/** The bought items, the newest first, at most RECENT_LIMIT. */
export function recentItems<T extends ShopItem>(items: T[]): T[] {
  return items
    .filter(item => item.checked)
    .sort((a, b) => (b.updatedAt ?? "").localeCompare(a.updatedAt ?? ""))
    .slice(0, RECENT_LIMIT);
}

/** The name on a tile: the food, or for an old note-only item its text without amount, unit and extras. */
export function itemTitle(item: Pick<ShopItem, "food" | "note">, units: ShopUnit[]): string {
  return item.food?.name ?? splitOldLine(splitNote(item.note).own, units).title;
}

/**
 * The small line on a tile: amount, properties and own text (for an old note-only item the amount and extras of its
 * text); when there is none and the item came from a recipe, FROM_RECIPE's text for the first recipe's name.
 * RECIPES maps recipe ids to names.
 */
export function itemDetail(
  item: ShopItem,
  units: ShopUnit[],
  recipes: Record<string, string>,
  fromRecipe: (name: string) => string,
): string {
  const { properties, own } = splitNote(item.note);
  const old = splitOldLine(own, units);
  const amount = quantityText({ quantity: item.quantity > 0 ? item.quantity : (old.quantity ?? 0), unit: item.unit ?? old.unit });
  const parts = item.food ? [quantityText(item), ...properties, own] : [amount, ...properties, old.extra];
  const line = parts.filter(Boolean).join(" · ");
  if (line) return line;
  const name = recipes[item.recipeReferences?.[0]?.recipeId ?? ""];
  return name ? fromRecipe(name) : "";
}

const LAST_LIST_KEY = "kh-shopping-list";

/** The list used last on this device; localStorage may be blocked or empty, then there is none. */
export function lastList(): string | null {
  try {
    return localStorage.getItem(LAST_LIST_KEY);
  }
  catch {
    return null;
  }
}

/** Remembers the list used last on this device; a blocked localStorage only loses the convenience. */
export function rememberList(id: string): void {
  try {
    localStorage.setItem(LAST_LIST_KEY, id);
  }
  catch {
    // storing the choice is a convenience only
  }
}

/** The lists with the one used last (LAST) first, the others in their order. */
export function lastUsedFirst<T extends { id: string }>(lists: T[], last: string | null): T[] {
  return [...lists].sort((a, b) => Number(b.id === last) - Number(a.id === last));
}

/** The list to open: the one in the address, else the last used on this device, else the first. */
export function pickListId(ids: string[], fromAddress: string | null, lastUsed: string | null): string | null {
  return [fromAddress, lastUsed].find(id => id && ids.includes(id)) ?? ids[0] ?? null;
}

/** Where Mealie's list pages lead instead: the tile page, with the list in the address; null for the classic view (?klassisch). */
export function shoppingRedirect(path: string, query: Record<string, unknown>): { path: string; query: { liste?: string } } | null {
  const match = path.match(/^\/shopping-lists(?:\/([^/]+))?\/?$/);
  if (!match || "klassisch" in query) return null;
  return { path: "/einkauf", query: match[1] ? { liste: match[1] } : {} };
}

/** What linking an item without a food to the group's food of its name sets (food, unit and a cleaned note), or null. */
export function foodLink<F extends { id: string; name: string; pluralName?: string | null }, U extends ShopUnit>(
  item: Pick<ShopItem, "food" | "note" | "unit">,
  foods: F[],
  units: U[],
): { food: F; unit: U | null; note: string } | null {
  if (item.food) return null;
  const { properties, own } = splitNote(item.note);
  const old = splitOldLine(own, units);
  // exact only: this write runs unattended, so no singular/plural guessing (Eis is not Ei)
  const wanted = old.title.trim().toLowerCase();
  const food = foods.find(entry => [entry.name, entry.pluralName].some(text => text?.trim().toLowerCase() === wanted));
  const word = old.unit && findUnit(old.unit.name, units);
  // a unit the group lacks (g, l ...) or a typed amount stay in the note: only whole, simple notes are linked
  if (!food || old.quantity !== null || old.extra || (old.unit && (!word || item.unit))) return null;
  return { food, unit: word ?? null, note: joinNote(properties, "") };
}
