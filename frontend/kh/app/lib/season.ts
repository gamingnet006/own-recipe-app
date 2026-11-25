// KH: a hand-written season calendar for Germany (D80): regional outdoor and storage season of fruit, vegetables and
// herbs, our own data. Pure functions say what is in season in a month and which food names to look for in recipes.

export interface SeasonItem {
  /** The name shown and searched for, then more forms (plural, spellings) that also count */
  names: string[];
  /** The English names and plurals: shown in the English interface and also searched for in every language */
  en: string[];
  /** First and last month (1 to 12); a first month after the last one wraps over New Year, e.g. 11 to 2 */
  from: number;
  to: number;
}

export const SEASON: SeasonItem[] = [
  { names: ["Spargel"], en: ["asparagus"], from: 4, to: 6 },
  { names: ["Rhabarber"], en: ["rhubarb"], from: 4, to: 6 },
  { names: ["Bärlauch"], en: ["wild garlic", "ramsons"], from: 3, to: 5 },
  { names: ["Radieschen"], en: ["radishes", "radish"], from: 4, to: 10 },
  { names: ["Spinat"], en: ["spinach"], from: 4, to: 10 },
  { names: ["Salat", "Kopfsalat", "Feldsalat"], en: ["lettuce", "salad greens"], from: 5, to: 10 },
  { names: ["Erdbeeren", "Erdbeere"], en: ["strawberries", "strawberry"], from: 5, to: 7 },
  { names: ["Kirschen", "Kirsche"], en: ["cherries", "cherry"], from: 6, to: 8 },
  { names: ["Johannisbeeren", "Johannisbeere"], en: ["currants", "currant", "redcurrants"], from: 6, to: 8 },
  { names: ["Himbeeren", "Himbeere"], en: ["raspberries", "raspberry"], from: 6, to: 9 },
  { names: ["Heidelbeeren", "Blaubeeren", "Heidelbeere", "Blaubeere"], en: ["blueberries", "blueberry"], from: 7, to: 9 },
  { names: ["Zucchini"], en: ["zucchini", "courgette", "courgettes"], from: 6, to: 10 },
  { names: ["Gurke", "Gurken"], en: ["cucumber", "cucumbers"], from: 6, to: 9 },
  { names: ["Tomaten", "Tomate"], en: ["tomatoes", "tomato"], from: 7, to: 10 },
  { names: ["Paprika"], en: ["bell pepper", "bell peppers"], from: 7, to: 10 },
  { names: ["Aubergine", "Auberginen"], en: ["eggplant", "eggplants", "aubergine"], from: 7, to: 9 },
  { names: ["Bohnen", "Bohne"], en: ["green beans", "green bean"], from: 7, to: 10 },
  { names: ["Erbsen", "Erbse"], en: ["peas", "pea"], from: 6, to: 8 },
  { names: ["Mais"], en: ["corn", "sweetcorn"], from: 8, to: 10 },
  { names: ["Pflaumen", "Pflaume", "Zwetschgen", "Zwetschge"], en: ["plums", "plum"], from: 8, to: 10 },
  { names: ["Birnen", "Birne"], en: ["pears", "pear"], from: 8, to: 11 },
  { names: ["Äpfel", "Apfel"], en: ["apples", "apple"], from: 8, to: 3 }, // with storage apples until spring
  { names: ["Trauben", "Weintrauben"], en: ["grapes", "grape"], from: 8, to: 10 },
  { names: ["Pilze", "Champignons", "Pfifferlinge", "Steinpilze"], en: ["mushrooms", "mushroom", "chanterelles"], from: 8, to: 10 },
  { names: ["Kürbis", "Kürbisse", "Hokkaido"], en: ["pumpkin", "squash", "butternut squash"], from: 9, to: 11 },
  { names: ["Rote Bete", "Rote Beete"], en: ["beetroot", "beets", "beet"], from: 9, to: 2 },
  { names: ["Blumenkohl"], en: ["cauliflower"], from: 6, to: 11 },
  { names: ["Brokkoli"], en: ["broccoli"], from: 6, to: 10 },
  { names: ["Kohlrabi"], en: ["kohlrabi"], from: 5, to: 10 },
  { names: ["Karotten", "Karotte", "Möhren", "Möhre"], en: ["carrots", "carrot"], from: 6, to: 3 },
  { names: ["Lauch", "Porree"], en: ["leek", "leeks"], from: 9, to: 3 },
  { names: ["Rosenkohl"], en: ["brussels sprouts", "brussels sprout"], from: 10, to: 2 },
  { names: ["Grünkohl"], en: ["kale"], from: 11, to: 2 },
  { names: ["Rotkohl", "Rotkraut"], en: ["red cabbage"], from: 9, to: 3 },
  { names: ["Weißkohl", "Weißkraut"], en: ["cabbage", "white cabbage"], from: 9, to: 3 },
  { names: ["Wirsing"], en: ["savoy cabbage"], from: 10, to: 3 },
  { names: ["Sellerie"], en: ["celeriac", "celery"], from: 9, to: 3 },
  { names: ["Pastinaken", "Pastinake"], en: ["parsnips", "parsnip"], from: 10, to: 3 },
  { names: ["Kartoffeln", "Kartoffel"], en: ["potatoes", "potato"], from: 7, to: 3 },
  { names: ["Zwiebeln", "Zwiebel"], en: ["onions", "onion"], from: 8, to: 3 },
  { names: ["Schwarzwurzeln", "Schwarzwurzel"], en: ["salsify"], from: 10, to: 2 },
  { names: ["Quitten", "Quitte"], en: ["quinces", "quince"], from: 9, to: 11 },
  { names: ["Walnüsse", "Walnuss"], en: ["walnuts", "walnut"], from: 9, to: 12 },
];

/** Whether a month (1 to 12) lies between the item's first and last month, also over New Year. */
function covers(item: SeasonItem, month: number): boolean {
  return item.from <= item.to ? month >= item.from && month <= item.to : month >= item.from || month <= item.to;
}

/** The items in season in MONTH (1 to 12), in the calendar's order. */
export function inSeason(month: number): SeasonItem[] {
  return SEASON.filter(item => covers(item, month));
}

/** All food names, plurals included, of what is in season in MONTH: what the recipe search looks for. */
export function seasonTerms(month: number): string[] {
  return inSeason(month).flatMap(item => [...item.names, ...item.en]);
}

/** The name an item is shown and searched by in LOCALE ("en-US" gives the English one, anything else the German). */
export function seasonName(item: SeasonItem, locale: string): string {
  return (locale.startsWith("en") ? item.en[0] : item.names[0])!;
}

/** The month (1 to 12) of a date. */
export function monthOf(date: Date): number {
  return date.getMonth() + 1;
}
