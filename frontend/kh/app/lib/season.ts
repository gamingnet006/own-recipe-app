// KH: a hand-written season calendar for Germany (D80): regional outdoor and storage season of fruit, vegetables and
// herbs, our own data. Pure functions say what is in season in a month and which food names to look for in recipes.

interface SeasonItem {
  /** The name shown and searched for, then more forms (plural, spellings) that also count */
  names: string[];
  /** First and last month (1 to 12); a first month after the last one wraps over New Year, e.g. 11 to 2 */
  from: number;
  to: number;
}

export const SEASON: SeasonItem[] = [
  { names: ["Spargel"], from: 4, to: 6 },
  { names: ["Rhabarber"], from: 4, to: 6 },
  { names: ["Bärlauch"], from: 3, to: 5 },
  { names: ["Radieschen"], from: 4, to: 10 },
  { names: ["Spinat"], from: 4, to: 10 },
  { names: ["Salat", "Kopfsalat", "Feldsalat"], from: 5, to: 10 },
  { names: ["Erdbeeren", "Erdbeere"], from: 5, to: 7 },
  { names: ["Kirschen", "Kirsche"], from: 6, to: 8 },
  { names: ["Johannisbeeren", "Johannisbeere"], from: 6, to: 8 },
  { names: ["Himbeeren", "Himbeere"], from: 6, to: 9 },
  { names: ["Heidelbeeren", "Blaubeeren", "Heidelbeere", "Blaubeere"], from: 7, to: 9 },
  { names: ["Zucchini"], from: 6, to: 10 },
  { names: ["Gurke", "Gurken"], from: 6, to: 9 },
  { names: ["Tomaten", "Tomate"], from: 7, to: 10 },
  { names: ["Paprika"], from: 7, to: 10 },
  { names: ["Aubergine", "Auberginen"], from: 7, to: 9 },
  { names: ["Bohnen", "Bohne"], from: 7, to: 10 },
  { names: ["Erbsen", "Erbse"], from: 6, to: 8 },
  { names: ["Mais"], from: 8, to: 10 },
  { names: ["Pflaumen", "Pflaume", "Zwetschgen", "Zwetschge"], from: 8, to: 10 },
  { names: ["Birnen", "Birne"], from: 8, to: 11 },
  { names: ["Äpfel", "Apfel"], from: 8, to: 3 }, // with storage apples until spring
  { names: ["Trauben", "Weintrauben"], from: 8, to: 10 },
  { names: ["Pilze", "Champignons", "Pfifferlinge", "Steinpilze"], from: 8, to: 10 },
  { names: ["Kürbis", "Kürbisse", "Hokkaido"], from: 9, to: 11 },
  { names: ["Rote Bete", "Rote Beete"], from: 9, to: 2 },
  { names: ["Blumenkohl"], from: 6, to: 11 },
  { names: ["Brokkoli"], from: 6, to: 10 },
  { names: ["Kohlrabi"], from: 5, to: 10 },
  { names: ["Karotten", "Karotte", "Möhren", "Möhre"], from: 6, to: 3 },
  { names: ["Lauch", "Porree"], from: 9, to: 3 },
  { names: ["Rosenkohl"], from: 10, to: 2 },
  { names: ["Grünkohl"], from: 11, to: 2 },
  { names: ["Rotkohl", "Rotkraut"], from: 9, to: 3 },
  { names: ["Weißkohl", "Weißkraut"], from: 9, to: 3 },
  { names: ["Wirsing"], from: 10, to: 3 },
  { names: ["Sellerie"], from: 9, to: 3 },
  { names: ["Pastinaken", "Pastinake"], from: 10, to: 3 },
  { names: ["Kartoffeln", "Kartoffel"], from: 7, to: 3 },
  { names: ["Zwiebeln", "Zwiebel"], from: 8, to: 3 },
  { names: ["Schwarzwurzeln", "Schwarzwurzel"], from: 10, to: 2 },
  { names: ["Quitten", "Quitte"], from: 9, to: 11 },
  { names: ["Walnüsse", "Walnuss"], from: 9, to: 12 },
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
  return inSeason(month).flatMap(item => item.names);
}

/** The month (1 to 12) of a date. */
export function monthOf(date: Date): number {
  return date.getMonth() + 1;
}
