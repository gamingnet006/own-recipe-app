// KH: tests for the logic of the shopping page (D60): emoji, catalog, store orders, detail chips, sorting and titles.
import { describe, expect, test } from "vitest";
import { BASICS, catalog, filterCatalog, itemForTile, tileEmoji } from "../lib/shopping-tiles";
import { labelOrderFor, labelSettingsFor, STORE_PRESETS } from "../lib/shopping-stores";
import {
  applyQuantity,
  foodLink,
  foodMatches,
  itemDetail,
  itemTitle,
  joinNote,
  lastUsedFirst,
  pickListId,
  quantityText,
  recentItems,
  sameAmount,
  shoppingRedirect,
  sortListItems,
  splitLeadingAmount,
  splitNote,
  splitUnitWord,
  toggleProperty,
  urgencyOf,
  withOwnText,
  type ShopItem,
} from "../lib/shopping-items";

const DEPARTMENTS = [
  "Obst & Gemüse", "Getreide", "Fleisch", "Fleischprodukte", "Meeresfrüchte", "Milchprodukte", "Backwaren", "Konserven",
  "Tiefkühlware", "Würzmittel & Saucen", "Gewürze", "Öle", "Backzutaten", "Süßigkeiten", "Snacks", "Getränke", "Alkohol",
  "Pflanzliche Ersatzprodukte", "Haushalt", "Sonstiges",
];
const labels = DEPARTMENTS.map((name, index) => ({ id: `l${index}`, name }));
const labelId = (name: string) => labels.find(label => label.name === name)!.id;

function item(over: Partial<ShopItem> = {}): ShopItem {
  return { checked: false, position: 0, quantity: 0, note: null, updatedAt: null, ...over };
}

describe("tileEmoji", () => {
  test("finds a food by name, in singular and plural", () => {
    expect(tileEmoji("Zwiebel")).toBe("🧅");
    expect(tileEmoji("Zwiebeln")).toBe("🧅");
    expect(tileEmoji("Ei")).toBe("🥚");
    expect(tileEmoji("Eier")).toBe("🥚");
    expect(tileEmoji("Äpfel")).toBe("🍎");
    expect(tileEmoji("Bananen")).toBe("🍌");
    expect(tileEmoji("MILCH")).toBe("🥛");
  });

  test("finds English foods in singular and plural", () => {
    for (const [name, emoji] of [
      ["milk", "🥛"], ["Butter", "🧈"], ["eggs", "🥚"], ["cheese", "🧀"], ["Bread", "🍞"], ["apples", "🍎"],
      ["banana", "🍌"], ["Tomatoes", "🍅"], ["potatoes", "🥔"], ["onions", "🧅"], ["garlic", "🧄"], ["carrots", "🥕"],
      ["rice", "🍚"], ["pasta", "🍝"], ["coffee", "☕"], ["tea", "🍵"], ["water", "💧"], ["orange juice", "🧃"],
      ["beer", "🍺"], ["wine", "🍷"], ["chicken", "🍗"], ["beef", "🥩"], ["fish", "🐟"], ["strawberries", "🍓"],
      ["toilet paper", "🧻"],
    ]) {
      expect(tileEmoji(name), name).toBe(emoji);
    }
    expect(tileEmoji("Red onion")).toBe("🧅");
  });

  test("falls back to the last or first word of the name", () => {
    expect(tileEmoji("Rote Zwiebel")).toBe("🧅");
    expect(tileEmoji("Tomaten aus der Dose")).toBe("🍅");
  });

  test("falls back to the department, then to nothing", () => {
    expect(tileEmoji("Harissa", "Würzmittel & Saucen")).toBe("🍶");
    expect(tileEmoji("Harissa", "Unbekannt")).toBe("");
    expect(tileEmoji("Harissa")).toBe("");
  });

  test("every German seed department has an emoji", () => {
    for (const name of DEPARTMENTS) expect(tileEmoji("Xyz", name), name).not.toBe("");
  });
});

describe("BASICS", () => {
  test("lie in departments of the seed", () => {
    expect(BASICS.length).toBeGreaterThanOrEqual(30);
    for (const basic of BASICS) expect(DEPARTMENTS, basic.name).toContain(basic.department);
  });
});

describe("catalog", () => {
  const foods = [
    { id: "f1", name: "Milch", labelId: labelId("Milchprodukte") },
    { id: "f2", name: "Apfel", labelId: labelId("Obst & Gemüse") },
    { id: "f3", name: "Ei", labelId: labelId("Milchprodukte") },
    { id: "f4", name: "Mysteriös", labelId: null },
  ];
  const basics = [
    { name: "milch", department: "Getränke", emoji: "x" },
    { name: "Toast", department: "Backwaren", emoji: "🍞" },
    { name: "Dings", department: "Gibt es nicht", emoji: "?" },
  ];

  test("follows the list's order, labels without a position last", () => {
    const order = [labelId("Backwaren"), labelId("Milchprodukte")];
    const names = catalog(foods, labels, basics, order).map(department => department.name);
    expect(names.slice(0, 2)).toEqual(["Backwaren", "Milchprodukte"]);
    expect(names.slice(2)).toEqual(["Obst & Gemüse", "Sonstiges"]);
  });

  test("merges foods and basics, a food wins, tiles sorted by name", () => {
    const dairy = catalog(foods, labels, basics, []).find(department => department.name === "Milchprodukte")!;
    expect(dairy.tiles.map(tile => tile.name)).toEqual(["Ei", "Milch"]);
    expect(dairy.tiles[1]!.foodId).toBe("f1");
    const drinks = catalog(foods, labels, basics, []).find(department => department.name === "Getränke");
    expect(drinks).toBeUndefined();
  });

  test("items without a label or department go to Sonstiges, a basic carries its label", () => {
    const other = catalog(foods, labels, basics, []).find(department => department.name === "Sonstiges")!;
    expect(other.tiles.map(tile => tile.name)).toEqual(["Dings", "Mysteriös"]);
    const toast = catalog(foods, labels, basics, []).find(department => department.name === "Backwaren")!.tiles[0]!;
    expect(toast).toMatchObject({ name: "Toast", labelId: labelId("Backwaren") });
    expect(toast.foodId).toBeUndefined();
  });

  test("works with no Sonstiges label at all", () => {
    const some = labels.filter(label => label.name !== "Sonstiges");
    const result = catalog(foods, some, [], []);
    expect(result.at(-1)).toMatchObject({ name: "Sonstiges", labelId: null });
  });
});

describe("filterCatalog and itemForTile", () => {
  const departments = catalog([{ id: "f1", name: "Milch", labelId: labelId("Milchprodukte") }], labels, BASICS, []);

  test("keeps only matching tiles and departments", () => {
    const found = filterCatalog(departments, " mil ");
    expect(found.map(department => department.name)).toEqual(["Milchprodukte"]);
    expect(found[0]!.tiles.map(tile => tile.name)).toEqual(["Milch"]);
    expect(filterCatalog(departments, "")).toBe(departments);
  });

  test("finds the item of a food by id and of an everyday item by its own text", () => {
    const milk = { foodId: "f1", note: null, food: { name: "Milch" } };
    const bread = { foodId: null, note: "Bio, Brot", food: null };
    const butter = { foodId: "f9", note: "", food: { name: "Butter" } };
    expect(itemForTile({ name: "Milch", emoji: "", foodId: "f1", labelId: null }, [bread, milk])).toBe(milk);
    expect(itemForTile({ name: "brot", emoji: "", labelId: null }, [milk, bread])).toBe(bread);
    expect(itemForTile({ name: "Toast", emoji: "", labelId: null }, [milk, bread])).toBeUndefined();
    expect(itemForTile({ name: "butter", emoji: "", labelId: null }, [milk, butter])).toBe(butter); // a basic that became a food
  });
});

describe("stores", () => {
  test("presets cover the four kinds", () => {
    expect(STORE_PRESETS.find(preset => preset.name === "Lidl")?.kind).toBe("discounter");
    expect(new Set(STORE_PRESETS.map(preset => preset.kind)).size).toBe(4);
  });

  test("a drugstore starts with the household, a market with the produce", () => {
    expect(labelOrderFor("drugstore", labels)[0]).toBe(labelId("Haushalt"));
    expect(labelOrderFor("market", labels)[0]).toBe(labelId("Obst & Gemüse"));
  });

  test("unknown labels keep their relative order at the end, none get lost", () => {
    const extra = [{ id: "x1", name: "Zeitschriften" }, ...labels, { id: "x2", name: "Blumen" }];
    const order = labelOrderFor("supermarket", extra);
    expect(order).toHaveLength(extra.length);
    expect(order.slice(-2)).toEqual(["x1", "x2"]);
    expect(order.indexOf(labelId("Backwaren"))).toBeLessThan(order.indexOf(labelId("Getränke")));
  });
});

describe("labelSettingsFor", () => {
  test("gives each of Mealie's label rows the position of the store's order", () => {
    const rows = labels.map(label => ({ id: `row-${label.id}`, labelId: label.id, label: { name: label.name } }));
    const settings = labelSettingsFor("drugstore", "list-1", rows);
    expect(settings).toHaveLength(labels.length);
    expect(settings.find(row => row.labelId === labelId("Haushalt"))).toEqual(
      { id: `row-${labelId("Haushalt")}`, shoppingListId: "list-1", labelId: labelId("Haushalt"), position: 0 },
    );
    expect(new Set(settings.map(row => row.position)).size).toBe(labels.length);
  });
});

describe("applyQuantity", () => {
  const units = [{ id: "u-g", name: "Gramm", abbreviation: "g" }, { id: "u-kg", name: "Kilogramm", abbreviation: "kg" }];

  test("a plain number is the quantity", () => {
    expect(applyQuantity("6", units)).toEqual({ quantity: 6 });
  });

  test("an amount with a unit the group has sets the unit, by abbreviation or name, ignoring case", () => {
    expect(applyQuantity("250 g", units)).toEqual({ quantity: 250, unitId: "u-g" });
    expect(applyQuantity("1 KG", units)).toEqual({ quantity: 1, unitId: "u-kg" });
  });

  test("a unit the group lacks is to be created, never written into the note", () => {
    expect(applyQuantity("1 l", units)).toEqual({ quantity: 1, createUnit: { name: "Liter", abbreviation: "l" } });
    expect(applyQuantity("1 l", [{ id: "u-l", name: "Liter", abbreviation: "L" }])).toEqual({ quantity: 1, unitId: "u-l" });
    expect(applyQuantity("500 ml", [])).toEqual({ quantity: 500, createUnit: { name: "Milliliter", abbreviation: "ml" } });
  });
});

const liter = { id: "u-l", name: "Liter", pluralName: "Liter", abbreviation: "l" };
const gram = { id: "u-g", name: "Gramm", abbreviation: "g" };
const known = [liter, gram];

describe("splitLeadingAmount", () => {
  test("splits an amount and a unit word the group knows", () => {
    expect(splitLeadingAmount("2 Liter Milch", known)).toEqual({ quantity: 2, unit: liter, rest: "Milch" });
    expect(splitLeadingAmount("250g Mehl", known)).toEqual({ quantity: 250, unit: gram, rest: "Mehl" });
    expect(splitLeadingAmount("1,5 l Milch", known)).toEqual({ quantity: 1.5, unit: liter, rest: "Milch" });
    expect(splitLeadingAmount("1/2 Liter Saft", known)).toEqual({ quantity: 0.5, unit: liter, rest: "Saft" });
  });

  test("an amount without a unit, a word that is no unit, and no amount at all", () => {
    expect(splitLeadingAmount("2 Milch", known)).toEqual({ quantity: 2, unit: null, rest: "Milch" });
    expect(splitLeadingAmount("2 Äpfel", known)).toEqual({ quantity: 2, unit: null, rest: "Äpfel" });
    expect(splitLeadingAmount("Milch 3,5%", known)).toEqual({ quantity: null, unit: null, rest: "Milch 3,5%" });
    expect(splitLeadingAmount("  Toilettenpapier ", known)).toEqual({ quantity: null, unit: null, rest: "Toilettenpapier" });
  });

  test("a unit word with nothing after it is the article", () => {
    expect(splitLeadingAmount("2 Liter", known)).toEqual({ quantity: 2, unit: null, rest: "Liter" });
  });
});

describe("foodMatches", () => {
  test("finds a food by name or plural, in any case and number", () => {
    const egg = { name: "Ei", pluralName: "Eier" };
    expect(foodMatches(egg, "eier")).toBe(true);
    expect(foodMatches({ name: "Zwiebel", pluralName: null }, "Zwiebeln")).toBe(true);
    expect(foodMatches({ name: "Zwiebeln", pluralName: null }, "zwiebel")).toBe(true);
    expect(foodMatches(egg, "Milch")).toBe(false);
  });
});

describe("notes", () => {
  test("splits properties from the own text", () => {
    expect(splitNote("Bio, vegan, die große Packung")).toEqual({ properties: ["Bio", "vegan"], own: "die große Packung" });
    expect(splitNote("bio")).toEqual({ properties: ["Bio"], own: "" });
    expect(splitNote("Vollkorn, Bio")).toEqual({ properties: [], own: "Vollkorn, Bio" });
    expect(splitNote(null)).toEqual({ properties: [], own: "" });
  });

  test("toggles a property, properties first and own text after", () => {
    expect(toggleProperty("Brot", "Bio")).toBe("Bio, Brot");
    expect(toggleProperty("Bio, Brot", "vegan")).toBe("Bio, vegan, Brot");
    expect(toggleProperty("Bio, Brot", "Bio")).toBe("Brot");
    expect(toggleProperty(null, "klein")).toBe("klein");
    expect(toggleProperty("klein", "klein")).toBe("");
  });

  test("replaces the own text and keeps the properties", () => {
    expect(withOwnText("Bio, alt", "neu")).toBe("Bio, neu");
    expect(withOwnText("Bio", "")).toBe("Bio");
  });
});

describe("items", () => {
  test("quantityText writes amount and unit like the chips", () => {
    expect(quantityText({ quantity: 250, unit: { name: "Gramm", abbreviation: "g" } })).toBe("250 g");
    expect(quantityText({ quantity: 1.5, unit: { name: "Liter", abbreviation: "" } })).toBe("1,5 Liter");
    expect(quantityText({ quantity: 2, unit: null })).toBe("2");
    expect(quantityText({ quantity: 0, unit: null })).toBe("");
  });

  test("urgency comes from the extras, unknown values count as none", () => {
    expect(urgencyOf(item({ extras: { kh_urgency: "urgent" } }))).toBe("urgent");
    expect(urgencyOf(item({ extras: { kh_urgency: "bogus" } }))).toBe("");
    expect(urgencyOf(item({ extras: null }))).toBe("");
  });

  test("sorts open items: urgent first, whenever last, else by position", () => {
    const a = item({ position: 3, note: "a" });
    const b = item({ position: 1, note: "b", extras: { kh_urgency: "whenever" } });
    const c = item({ position: 2, note: "c", extras: { kh_urgency: "urgent" } });
    const d = item({ position: 0, note: "d", checked: true });
    const e = item({ position: 0, note: "e", extras: { kh_urgency: "offer" } });
    expect(sortListItems([a, b, c, d, e]).map(entry => entry.note)).toEqual(["c", "e", "a", "b"]);
  });

  test("recent items are the bought ones, newest first, at most 12", () => {
    const bought = Array.from({ length: 14 }, (_, index) =>
      item({ checked: true, note: `n${index}`, updatedAt: `2026-11-${String(index + 1).padStart(2, "0")}T10:00:00` }));
    const recent = recentItems([item({ note: "open" }), ...bought]);
    expect(recent).toHaveLength(12);
    expect(recent[0]!.note).toBe("n13");
  });

  test("the title is the food, or for an old note-only item its text without amount and unit", () => {
    expect(itemTitle(item({ food: { name: "Milch" }, note: "Bio" }), known)).toBe("Milch");
    expect(itemTitle(item({ note: "Bio, Brot" }), known)).toBe("Brot");
    expect(itemTitle(item({ note: "2 Liter Milch" }), known)).toBe("Milch");
    expect(itemTitle(item({ note: "Milch 3,5%" }), known)).toBe("Milch");
  });

  test("the detail lists amount, properties and own text, else the recipe", () => {
    const from = (name: string) => `Aus ${name}`;
    const milk = item({ food: { name: "Milch" }, quantity: 2, unit: liter, note: "Bio, 3,5 %" });
    expect(itemDetail(milk, known, {}, from)).toBe("2 l · Bio · 3,5 %");
    expect(itemDetail(item({ food: { name: "Milch" }, quantity: 2, note: "" }), known, {}, from)).toBe("2");
    const plain = item({ food: { name: "Ei" }, recipeReferences: [{ recipeId: "r1" }] });
    expect(itemDetail(plain, known, { r1: "Pudding" }, from)).toBe("Aus Pudding");
    expect(itemDetail(plain, known, {}, from)).toBe("");
  });

  test("old note-only items show amount and extras small, the article big", () => {
    const from = (name: string) => name;
    expect(itemDetail(item({ note: "2 Liter Milch 3,5 %" }), known, {}, from)).toBe("2 l · 3,5 %");
    expect(itemDetail(item({ note: "2 Milch" }), known, {}, from)).toBe("2");
    expect(itemDetail(item({ note: "Milch 3,5%" }), known, {}, from)).toBe("3,5 %");
    expect(itemDetail(item({ note: "Bio, Brot" }), known, {}, from)).toBe("Bio");
    expect(itemTitle(item({ note: "2 Liter Milch 3,5 %" }), known)).toBe("Milch");
  });
});

describe("recipe items without a food", () => {
  const from = (name: string) => name;
  const milk = item({ note: "ml Milch", quantity: 200 });

  test("the unit word leaves the title and joins the amount", () => {
    expect(itemTitle(milk, known)).toBe("Milch");
    expect(itemDetail(milk, known, {}, from)).toBe("200 ml");
    expect(itemTitle(item({ note: "g Mehl", quantity: 250 }), [])).toBe("Mehl");
    expect(itemDetail(item({ note: "g Mehl", quantity: 250 }), [], {}, from)).toBe("250 g");
    expect(itemTitle(item({ note: "Dose Tomaten", quantity: 1 }), [{ id: "u", name: "Dose" }])).toBe("Tomaten");
  });

  test("a standard unit name counts even when the group lacks the unit", () => {
    expect(itemTitle(item({ note: "Liter Milch 3.5%", quantity: 2 }), [])).toBe("Milch");
    expect(itemDetail(item({ note: "Liter Milch 3.5%", quantity: 2 }), [], {}, from)).toBe("2 l · 3.5 %");
  });

  test("foodLink links only an exact name or plural, never a fuzzy match", () => {
    const f = (name: string, pluralName: string | null = null) => ({ id: name, name, pluralName });
    expect(foodLink(item({ note: "Eis", quantity: 1 }), [f("Ei"), f("Eis")], known)?.food.id).toBe("Eis");
    expect(foodLink(item({ note: "Eis", quantity: 1 }), [f("Ei")], known)).toBeNull();
    expect(foodLink(item({ note: "Butter", quantity: 1 }), [f("Butt")], known)).toBeNull();
    expect(foodLink(item({ note: " milch ", quantity: 1 }), [f("Kuh", "Milch")], known)?.food.id).toBe("Kuh");
  });

  test("splitUnitWord takes a leading unit word off", () => {
    expect(splitUnitWord("g Zucker")).toEqual({ unit: { name: "Gramm", abbreviation: "g" }, rest: "Zucker" });
    expect(splitUnitWord("Zucker")).toBeNull();
    expect(splitUnitWord("Zucker braun")).toBeNull();
  });

  test("a lone word that is a unit stays the article", () => {
    expect(itemTitle(item({ note: "Liter" }), known)).toBe("Liter");
  });

  test("the item is the one of the Milch tile", () => {
    const tile = { name: "Milch", emoji: "", labelId: null };
    expect(itemForTile(tile, [{ foodId: null, note: "ml Milch", food: null }])).toBeDefined();
    expect(itemForTile(tile, [{ foodId: null, note: "ml Milch", food: null }, { foodId: null, note: "Mehl", food: null }])?.note).toBe("ml Milch");
  });

  test("foodLink finds the food and cleans the note", () => {
    const foods = [{ id: "f1", name: "Milch", pluralName: null }];
    const milliliter = { id: "u-ml", name: "Milliliter", abbreviation: "ml" };
    expect(foodLink(milk, foods, [...known, milliliter])).toEqual({ food: foods[0], unit: milliliter, note: "" });
    expect(foodLink(milk, foods, known)).toBeNull(); // the group has no unit ml: the note keeps it
    expect(foodLink(item({ note: "Milch", quantity: 1 }), foods, known)?.food.id).toBe("f1");
    expect(foodLink(item({ note: "2 Liter Milch" }), foods, known)).toBeNull();
    expect(foodLink(item({ note: "ml Käse" }), foods, known)).toBeNull();
    expect(foodLink(item({ note: "ml Milch", food: { name: "Milch" } }), foods, known)).toBeNull();
  });
});

describe("lastUsedFirst", () => {
  test("puts the list used last first and keeps the order of the rest", () => {
    const lists = [{ id: "a" }, { id: "b" }, { id: "c" }];
    expect(lastUsedFirst(lists, "c").map(list => list.id)).toEqual(["c", "a", "b"]);
    expect(lastUsedFirst(lists, null).map(list => list.id)).toEqual(["a", "b", "c"]);
  });
});

describe("pickListId", () => {
  test("prefers the address, then the last used, then the first", () => {
    const ids = ["a", "b", "c"];
    expect(pickListId(ids, "b", "c")).toBe("b");
    expect(pickListId(ids, "zzz", "c")).toBe("c");
    expect(pickListId(ids, null, "zzz")).toBe("a");
    expect(pickListId([], "a", "b")).toBeNull();
  });
});

describe("shoppingRedirect", () => {
  test("sends Mealie's list pages to the tile page, with the list in the address", () => {
    expect(shoppingRedirect("/shopping-lists", {})).toEqual({ path: "/einkauf", query: {} });
    expect(shoppingRedirect("/shopping-lists/abc-1", {})).toEqual({ path: "/einkauf", query: { liste: "abc-1" } });
  });

  test("leaves the classic view and other pages alone", () => {
    expect(shoppingRedirect("/shopping-lists/abc", { klassisch: "1" })).toBeNull();
    expect(shoppingRedirect("/einkauf", {})).toBeNull();
    expect(shoppingRedirect("/shopping-lists/abc/extra", {})).toBeNull();
  });
});

describe("amount and note helpers", () => {
  test("sameAmount ignores case but never matches an empty amount", () => {
    expect(sameAmount("1 L", "1 l")).toBe(true);
    expect(sameAmount("250 g", "500 g")).toBe(false);
    expect(sameAmount("", "")).toBe(false);
  });

  test("joinNote puts properties first and drops empty parts", () => {
    expect(joinNote(["Bio", "vegan"], " große Packung ")).toBe("Bio, vegan, große Packung");
    expect(joinNote([], "")).toBe("");
    expect(joinNote(["Bio"], "")).toBe("Bio");
  });
});
