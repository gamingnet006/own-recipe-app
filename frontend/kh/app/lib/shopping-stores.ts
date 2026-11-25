// KH: the stores of the shopping page's picker (D60) and the walking order of departments in each kind of store.
import { canonicalDepartment } from "./departments";

export type StoreKind = "supermarket" | "discounter" | "drugstore" | "market";

export interface StorePreset {
  name: string;
  kind: StoreKind;
}

const presets = (kind: StoreKind, names: string[]): StorePreset[] => names.map(name => ({ name, kind }));

/** The choices of the picker, grouped by kind; "another store" takes a free name and the supermarket order. */
export const STORE_PRESETS: StorePreset[] = [
  ...presets("supermarket", ["Rewe", "Edeka", "Kaufland", "Globus"]),
  ...presets("discounter", ["Aldi Süd", "Aldi Nord", "Lidl", "Penny", "Netto"]),
  ...presets("drugstore", ["dm", "Rossmann", "Müller"]),
  ...presets("market", ["Wochenmarkt", "Bäcker", "Metzger"]),
];

export const STORE_KINDS: StoreKind[] = ["supermarket", "discounter", "drugstore", "market"];

// The departments (names of the German seed labels; the English seed's names count the same) of each kind in walking order; what is not listed keeps its order at the end.
const ORDER: Record<StoreKind, string[]> = {
  supermarket: [
    "Obst & Gemüse", "Backwaren", "Fleisch", "Fleischprodukte", "Meeresfrüchte", "Milchprodukte",
    "Pflanzliche Ersatzprodukte", "Konserven", "Getreide", "Backzutaten", "Würzmittel & Saucen", "Gewürze", "Öle",
    "Süßigkeiten", "Snacks", "Tiefkühlware", "Getränke", "Alkohol", "Haushalt", "Sonstiges",
  ],
  discounter: [
    "Obst & Gemüse", "Backwaren", "Getränke", "Alkohol", "Konserven", "Getreide", "Backzutaten", "Würzmittel & Saucen",
    "Gewürze", "Öle", "Süßigkeiten", "Snacks", "Milchprodukte", "Pflanzliche Ersatzprodukte", "Fleisch",
    "Fleischprodukte", "Meeresfrüchte", "Tiefkühlware", "Haushalt", "Sonstiges",
  ],
  drugstore: ["Haushalt", "Süßigkeiten", "Snacks", "Getränke", "Sonstiges"],
  market: ["Obst & Gemüse", "Backwaren", "Fleisch", "Fleischprodukte", "Meeresfrüchte", "Milchprodukte", "Sonstiges"],
};

/** The ids of LABELS in the walking order of a kind of store; labels the order does not know follow in their own order. */
export function labelOrderFor(kind: StoreKind, labels: { id: string; name: string }[]): string[] {
  const rank = (name: string) => {
    const index = ORDER[kind].findIndex(entry => canonicalDepartment(entry) === canonicalDepartment(name));
    return index < 0 ? ORDER[kind].length : index;
  };
  return [...labels].sort((a, b) => rank(a.name) - rank(b.name)).map(label => label.id);
}

/** The label settings of a list (Mealie's rows of label and position) with the positions of a kind of store's walking order. */
export function labelSettingsFor(
  kind: StoreKind,
  shoppingListId: string,
  settings: { id: string; labelId: string; label: { name: string } }[],
): { id: string; shoppingListId: string; labelId: string; position: number }[] {
  const order = labelOrderFor(kind, settings.map(setting => ({ id: setting.labelId, name: setting.label.name })));
  return settings.map(setting => ({
    id: setting.id,
    shoppingListId,
    labelId: setting.labelId,
    position: order.indexOf(setting.labelId),
  }));
}
