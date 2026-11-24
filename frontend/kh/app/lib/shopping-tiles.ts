// KH: the tiles of the shopping page (D60): which emoji a food gets, the everyday items Mealie's recipe foods lack, and
// the catalog of tiles grouped by department in the order of the list.
import { itemTitle, type ShopUnit } from "./shopping-items";

export interface TileFood {
  id: string;
  name: string;
  labelId: string | null;
  /** The slugs of the households that always have this food in the house (D65) */
  householdsWithIngredientFood?: string[];
}

export interface TileLabel {
  id: string;
  name: string;
}

export interface Basic {
  name: string;
  department: string;
  emoji: string;
}

/** One tile of the catalog: a food of the group (foodId) or an everyday item written down as a note. */
export interface Tile {
  name: string;
  emoji: string;
  foodId?: string;
  labelId: string | null;
  /** Always in the house for this household (D65): a house badge, at the end of its department */
  onHand?: boolean;
}

export interface Department {
  labelId: string | null;
  name: string;
  tiles: Tile[];
}

/** Whether the household (by slug) always has the food in the house. */
export const isOnHand = (food: Pick<TileFood, "householdsWithIngredientFood"> | undefined, householdSlug: string): boolean =>
  !!householdSlug && !!food?.householdsWithIngredientFood?.includes(householdSlug);

/** The department that takes every item without a label, as in Mealie's seed. */
export const OTHER_DEPARTMENT = "Sonstiges";

// Emoji by food name (German here, English below), lower case; plural forms are found by tileEmoji's suffix rules, only umlaut plurals are listed.
const GERMAN_EMOJI: Record<string, string> = {
  // fruit and vegetables
  apfel: "🍎", äpfel: "🍎", birne: "🍐", banane: "🍌", orange: "🍊", mandarine: "🍊", zitrone: "🍋", limette: "🍋",
  erdbeere: "🍓", weintraube: "🍇", traube: "🍇", wassermelone: "🍉", melone: "🍈", pfirsich: "🍑", kirsche: "🍒",
  ananas: "🍍", mango: "🥭", kiwi: "🥝", kokosnuss: "🥥", avocado: "🥑", tomate: "🍅", kirschtomate: "🍅",
  aubergine: "🍆", kartoffel: "🥔", süßkartoffel: "🍠", karotte: "🥕", möhre: "🥕", mais: "🌽", zuckermais: "🌽",
  chili: "🌶️", chilischote: "🌶️", paprika: "🫑", gurke: "🥒", brokkoli: "🥦", salat: "🥬", spinat: "🥬",
  knoblauch: "🧄", zwiebel: "🧅", schalotte: "🧅", lauch: "🧅", pilz: "🍄", champignon: "🍄", kürbis: "🎃",
  zucchini: "🥒", blumenkohl: "🥦", rucola: "🥬", ingwer: "🫚", erbse: "🫛", bohne: "🫘", kichererbse: "🫘",
  linse: "🫘", rosine: "🍇", beere: "🫐", blaubeere: "🫐", himbeere: "🍓", pflaume: "🍑",
  // dairy, eggs, meat, fish
  milch: "🥛", butter: "🧈", ei: "🥚", käse: "🧀", joghurt: "🥣", quark: "🥣", sahne: "🥛",
  schmand: "🥣", frischkäse: "🧀", mozzarella: "🧀", parmesan: "🧀", hackfleisch: "🥩", steak: "🥩", rindfleisch: "🥩",
  schweinefleisch: "🥩", fleisch: "🥩", hähnchen: "🍗", hähnchenbrust: "🍗", huhn: "🍗", pute: "🍗", putenbrust: "🍗",
  speck: "🥓", schinken: "🥓", wurst: "🌭", salami: "🌭", aufschnitt: "🥓", lachs: "🐟", fisch: "🐟",
  thunfisch: "🐟", garnele: "🦐", krabbe: "🦀", tintenfisch: "🦑", muschel: "🦪",
  // bread, grain, pasta
  brot: "🍞", toast: "🍞", brötchen: "🥖", baguette: "🥖", croissant: "🥐", brezel: "🥨", bagel: "🥯", reis: "🍚",
  nudel: "🍝", spaghetti: "🍝", pasta: "🍝", penne: "🍝", mehl: "🌾", grieß: "🌾", haferflocken: "🌾", müsli: "🥣",
  // pantry, sweets, snacks
  zucker: "🍬", salz: "🧂", pfeffer: "🧂", öl: "🫒", olivenöl: "🫒", olive: "🫒", essig: "🍶", honig: "🍯",
  marmelade: "🍯", ketchup: "🍅", senf: "🌭", mayonnaise: "🥚", sojasauce: "🍶", tomatenmark: "🍅", brühe: "🍲",
  suppe: "🍲", schokolade: "🍫", keks: "🍪", kuchen: "🍰", eis: "🍦", eiscreme: "🍦", bonbon: "🍬",
  chips: "🥔", kartoffelchip: "🥔", cracker: "🍘", popcorn: "🍿", nuss: "🥜", nüsse: "🥜", erdnuss: "🥜",
  mandel: "🌰", walnuss: "🥜", pizza: "🍕", pommes: "🍟", hefe: "🥣", backpulver: "🧂", kakao: "🍫",
  // drinks
  wasser: "💧", mineralwasser: "💧", sprudel: "💧", saft: "🧃", orangensaft: "🧃", apfelsaft: "🧃", cola: "🥤",
  limonade: "🥤", kaffee: "☕", espresso: "☕", tee: "🍵", bier: "🍺", wein: "🍷", rotwein: "🍷", weißwein: "🥂",
  sekt: "🍾", champagner: "🍾", whisky: "🥃", wodka: "🍸", gin: "🍸", rum: "🥃", hafermilch: "🥛", sojamilch: "🥛",
  kokosmilch: "🥥",
  // household
  toilettenpapier: "🧻", küchenrolle: "🧻", taschentücher: "🤧", spülmittel: "🧴", spülmaschinentabs: "🧼",
  waschmittel: "🧺", müllbeutel: "🗑️", zahnpasta: "🪥", zahnbürste: "🪥", duschgel: "🧴", shampoo: "🧴", seife: "🧼",
  batterie: "🔋", alufolie: "📦", frischhaltefolie: "📦", katzenfutter: "🐱", hundefutter: "🐶",
  deo: "🧴", kerze: "🕯️", glühbirne: "💡",
};

// The same in English (singular; plurals by the suffix rules, "berries" is listed)
const ENGLISH_EMOJI: Record<string, string> = {
  "milk": "🥛",
  "apple": "🍎", "pear": "🍐", "banana": "🍌", "lemon": "🍋", "lime": "🍋", "strawberry": "🍓", "strawberries": "🍓", "grape": "🍇",
  "watermelon": "🍉", "melon": "🍈", "peach": "🍑", "cherry": "🍒", "cherries": "🍒", "pineapple": "🍍", "coconut": "🥥",
  "tomato": "🍅", "eggplant": "🍆", "potato": "🥔", "sweet potato": "🍠", "carrot": "🥕", "corn": "🌽", "pepper": "🫑",
  "cucumber": "🥒", "broccoli": "🥦", "lettuce": "🥬", "spinach": "🥬", "garlic": "🧄", "onion": "🧅", "leek": "🧅", "mushroom": "🍄",
  "pumpkin": "🎃", "cauliflower": "🥦", "arugula": "🥬", "ginger": "🫚", "pea": "🫛", "chickpea": "🫘", "lentil": "🫘",
  "raisin": "🍇", "berry": "🫐", "berries": "🫐", "blueberry": "🫐", "blueberries": "🫐", "raspberry": "🍓", "raspberries": "🍓",
  "plum": "🍑",
  "egg": "🥚", "cheese": "🧀", "yogurt": "🥣", "yoghurt": "🥣", "cream": "🥛", "sour cream": "🥣", "cream cheese": "🧀",
  "ground beef": "🥩", "beef": "🥩", "pork": "🥩", "meat": "🥩", "chicken": "🍗", "turkey": "🍗", "bacon": "🥓", "ham": "🥓",
  "sausage": "🌭", "salmon": "🐟", "fish": "🐟", "tuna": "🐟", "shrimp": "🦐", "crab": "🦀", "squid": "🦑", "mussel": "🦪",
  "bread": "🍞", "bun": "🥖", "roll": "🥖", "pretzel": "🥨", "rice": "🍚", "noodle": "🍝", "flour": "🌾", "semolina": "🌾",
  "oat": "🌾", "oats": "🌾", "cereal": "🥣", "muesli": "🥣",
  "sugar": "🍬", "salt": "🧂", "black pepper": "🧂", "oil": "🫒", "olive oil": "🫒", "olive": "🫒", "vinegar": "🍶", "honey": "🍯",
  "jam": "🍯", "mustard": "🌭", "mayo": "🥚", "soy sauce": "🍶", "tomato paste": "🍅", "broth": "🍲", "stock": "🍲", "soup": "🍲",
  "chocolate": "🍫", "cookie": "🍪", "biscuit": "🍪", "cake": "🍰", "ice cream": "🍦", "candy": "🍬", "chip": "🥔",
  "crisps": "🥔", "cracker": "🍘", "nut": "🥜", "peanut": "🥜", "almond": "🌰", "walnut": "🥜", "fries": "🍟", "yeast": "🥣",
  "baking powder": "🧂", "cocoa": "🍫",
  "water": "💧", "sparkling water": "💧", "juice": "🧃", "orange juice": "🧃", "apple juice": "🧃", "soda": "🥤",
  "lemonade": "🥤", "coffee": "☕", "tea": "🍵", "beer": "🍺", "wine": "🍷", "red wine": "🍷", "white wine": "🥂",
  "champagne": "🍾", "vodka": "🍸", "oat milk": "🥛", "soy milk": "🥛", "coconut milk": "🥥",
  "toilet paper": "🧻", "paper towel": "🧻", "tissue": "🤧", "dish soap": "🧴", "detergent": "🧺", "trash bag": "🗑️",
  "toothpaste": "🪥", "toothbrush": "🪥", "shower gel": "🧴", "soap": "🧼", "battery": "🔋", "aluminum foil": "📦",
  "plastic wrap": "📦", "cat food": "🐱", "dog food": "🐶", "deodorant": "🧴", "candle": "🕯️", "light bulb": "💡",
};

const NAME_EMOJI = { ...GERMAN_EMOJI, ...ENGLISH_EMOJI };

// The emoji of a department, for a food that has none of its own; keyed by the names of Mealie's German seed labels.
const DEPARTMENT_EMOJI: Record<string, string> = {
  "obst & gemüse": "🥬", "getreide": "🌾", "fleisch": "🥩", "fleischprodukte": "🥓", "meeresfrüchte": "🐟",
  "milchprodukte": "🥛", "backwaren": "🥖", "konserven": "🥫", "tiefkühlware": "🧊", "würzmittel & saucen": "🍶",
  "gewürze": "🧂", "öle": "🫒", "backzutaten": "🧁", "süßigkeiten": "🍬", "snacks": "🥨", "getränke": "🥤", "alkohol": "🍷",
  "pflanzliche ersatzprodukte": "🌱", "haushalt": "🧺", "sonstiges": "🛒",
};

const PLURAL_ENDINGS = ["", "n", "en", "e", "er", "s", "es"]; // "es": tomatoes, peaches

/** The emoji for a plural or singular form of a word, or "" when the name map has none. */
function wordEmoji(word: string): string {
  for (const ending of PLURAL_ENDINGS) {
    if (ending && !word.endsWith(ending)) continue;
    const emoji = NAME_EMOJI[ending ? word.slice(0, -ending.length) : word];
    if (emoji) return emoji;
  }
  return "";
}

/**
 * The emoji of a tile: by the food's name (whole name, then its last and first word, so "Rote Zwiebel" and "Tomaten
 * aus der Dose" are found), else by its department, else "" (the tile then shows the first letter).
 */
export function tileEmoji(name: string, departmentName = ""): string {
  const lower = name.trim().toLowerCase();
  const words = lower.split(/\s+/);
  for (const candidate of [lower, words[words.length - 1], words[0]]) {
    const emoji = wordEmoji(candidate ?? "");
    if (emoji) return emoji;
  }
  return DEPARTMENT_EMOJI[departmentName.trim().toLowerCase()] ?? "";
}

/** Everyday items Mealie's recipe foods lack; the department names are those of the seed labels. */
export const BASICS: Basic[] = [
  { name: "Brötchen", department: "Backwaren", emoji: "🥖" },
  { name: "Toast", department: "Backwaren", emoji: "🍞" },
  { name: "Croissants", department: "Backwaren", emoji: "🥐" },
  { name: "Brot", department: "Backwaren", emoji: "🍞" },
  { name: "Joghurt", department: "Milchprodukte", emoji: "🥣" },
  { name: "Quark", department: "Milchprodukte", emoji: "🥣" },
  { name: "Aufschnitt", department: "Fleischprodukte", emoji: "🥓" },
  { name: "Wasser", department: "Getränke", emoji: "💧" },
  { name: "Mineralwasser", department: "Getränke", emoji: "💧" },
  { name: "Saft", department: "Getränke", emoji: "🧃" },
  { name: "Cola", department: "Getränke", emoji: "🥤" },
  { name: "Chips", department: "Snacks", emoji: "🥔" },
  { name: "Kekse", department: "Süßigkeiten", emoji: "🍪" },
  { name: "Eis", department: "Tiefkühlware", emoji: "🍦" },
  { name: "Tiefkühlpizza", department: "Tiefkühlware", emoji: "🍕" },
  { name: "Pommes", department: "Tiefkühlware", emoji: "🍟" },
  { name: "Fischstäbchen", department: "Tiefkühlware", emoji: "🐟" },
  { name: "Toilettenpapier", department: "Haushalt", emoji: "🧻" },
  { name: "Küchenrolle", department: "Haushalt", emoji: "🧻" },
  { name: "Taschentücher", department: "Haushalt", emoji: "🤧" },
  { name: "Spülmittel", department: "Haushalt", emoji: "🧴" },
  { name: "Spülmaschinentabs", department: "Haushalt", emoji: "🧼" },
  { name: "Waschmittel", department: "Haushalt", emoji: "🧺" },
  { name: "Müllbeutel", department: "Haushalt", emoji: "🗑️" },
  { name: "Zahnpasta", department: "Haushalt", emoji: "🪥" },
  { name: "Duschgel", department: "Haushalt", emoji: "🧴" },
  { name: "Shampoo", department: "Haushalt", emoji: "🧴" },
  { name: "Batterien", department: "Haushalt", emoji: "🔋" },
  { name: "Alufolie", department: "Haushalt", emoji: "📦" },
  { name: "Frischhaltefolie", department: "Haushalt", emoji: "📦" },
  { name: "Katzenfutter", department: "Haushalt", emoji: "🐱" },
  { name: "Hundefutter", department: "Haushalt", emoji: "🐶" },
];

/**
 * The tiles by department: departments in the list's order (LABEL_ORDER holds label ids; labels without a position
 * follow, items without a label go to "Sonstiges"), foods and basics merged without duplicates (by name, ignoring
 * case; a food wins over a basic), tiles by name, the ones always in the house (for HOUSEHOLD-SLUG) after the others.
 * Departments without a tile are left out.
 */
export function catalog(
  foods: TileFood[],
  labels: TileLabel[],
  basics: Basic[],
  labelOrder: string[],
  householdSlug = "",
): Department[] {
  const position = (id: string) => (labelOrder.includes(id) ? labelOrder.indexOf(id) : labelOrder.length);
  const ordered = [...labels].sort((a, b) => position(a.id) - position(b.id)); // stable: the rest keeps its order
  const other = labels.find(label => label.name.toLowerCase() === OTHER_DEPARTMENT.toLowerCase());
  const known = new Set(labels.map(label => label.id));
  const byId = new Map<string | null, Department>(ordered.map(label => [label.id, { labelId: label.id, name: label.name, tiles: [] }]));
  if (!other) byId.set(null, { labelId: null, name: OTHER_DEPARTMENT, tiles: [] });
  const target = (labelId: string | null) => byId.get(labelId && known.has(labelId) ? labelId : (other?.id ?? null))!;

  const seen = new Set<string>();
  const add = (tile: Tile) => {
    const key = tile.name.trim().toLowerCase();
    if (!key || seen.has(key)) return;
    seen.add(key);
    target(tile.labelId).tiles.push(tile);
  };
  for (const food of foods) {
    const label = labels.find(candidate => candidate.id === food.labelId);
    add({ name: food.name, emoji: tileEmoji(food.name, label?.name), foodId: food.id, labelId: food.labelId, onHand: isOnHand(food, householdSlug) });
  }
  for (const basic of basics) {
    const label = labels.find(candidate => candidate.name.toLowerCase() === basic.department.toLowerCase());
    add({ name: basic.name, emoji: basic.emoji, labelId: label?.id ?? null });
  }
  const departments = [...byId.values()].filter(department => department.tiles.length);
  departments.forEach(department => department.tiles.sort((a, b) => Number(!!a.onHand) - Number(!!b.onHand) || a.name.localeCompare(b.name, "de")));
  return departments;
}

/** The departments with only the tiles whose name contains QUERY (ignoring case); an empty query keeps all. */
export function filterCatalog(departments: Department[], query: string): Department[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return departments;
  return departments
    .map(department => ({ ...department, tiles: department.tiles.filter(tile => tile.name.toLowerCase().includes(needle)) }))
    .filter(department => department.tiles.length);
}

/** The list item a tile stands for: the same food or one of that name, or an old note-only item with its name. */
export function itemForTile<T extends { foodId: string | null; note: string | null; food?: { name: string } | null }>(
  tile: Tile,
  items: T[],
  units: ShopUnit[] = [],
): T | undefined {
  const name = tile.name.trim().toLowerCase();
  return items.find(item =>
    (tile.foodId && item.foodId === tile.foodId)
    || (item.food ? item.food.name.toLowerCase() === name : itemTitle(item, units).toLowerCase() === name),
  );
}

/**
 * What a tile written down again meets on the list: an open item of that article (it takes TYPED, what was typed
 * with it), else a bought one (it is put back, with TYPED too); undefined when the article is not there at all.
 */
export function existingFor<T extends { checked: boolean; foodId: string | null; note: string | null; food?: { name: string } | null }>(
  tile: Tile,
  items: T[],
  typed: Record<string, unknown>,
  units: ShopUnit[] = [],
): { item: T; changes: Record<string, unknown> } | undefined {
  const open = itemForTile(tile, items.filter(item => !item.checked), units);
  if (open) return { item: open, changes: typed };
  const bought = itemForTile(tile, items.filter(item => item.checked), units);
  return bought ? { item: bought, changes: { ...typed, checked: false } } : undefined;
}
