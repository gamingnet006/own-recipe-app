// KH: the shopping departments (names of Mealie's seed labels) in German and English, so the walking order, the emoji
// and the "Other" department work for either seed. Our own data, matched to Mealie's labels by name.

/** German name, English name: Mealie's seed labels in the order of its seed file. */
const PAIRS: [string, string][] = [
  ["Obst & Gemüse", "Produce"], ["Getreide", "Grains"], ["Fleisch", "Meat"], ["Fleischprodukte", "Meat Products"],
  ["Meeresfrüchte", "Seafood"], ["Milchprodukte", "Dairy Products"], ["Backwaren", "Baked Goods"],
  ["Konserven", "Canned Goods"], ["Tiefkühlware", "Frozen Foods"], ["Würzmittel & Saucen", "Condiments"],
  ["Gewürze", "Spices"], ["Öle", "Oils"], ["Backzutaten", "Baking"], ["Süßigkeiten", "Sweets"], ["Snacks", "Snacks"],
  ["Getränke", "Beverages"], ["Alkohol", "Alcohol"], ["Pflanzliche Ersatzprodukte", "Health Foods"],
  ["Haushalt", "Household"], ["Sonstiges", "Other"],
];

const GERMAN_OF = new Map(PAIRS.flatMap(([de, en]) => [[de.toLowerCase(), de.toLowerCase()], [en.toLowerCase(), de.toLowerCase()]]));

/** The department's name as the German seed writes it (lower case) whichever seed it comes from; a name that is
 * neither seed's (a department of the family's own) stays as it is, lower case. */
export function canonicalDepartment(name: string): string {
  const lower = name.trim().toLowerCase();
  return GERMAN_OF.get(lower) ?? lower;
}

/** The name of the department that takes everything without a label, in the language of LOCALE. */
export function otherDepartment(locale: string): string {
  return locale.startsWith("en") ? "Other" : "Sonstiges";
}

export const OTHER_KEY = canonicalDepartment("Sonstiges");
