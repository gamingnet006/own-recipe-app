// KH: the amounts' display (D39, phase 3, A4): one function for recipe, cook mode, print and shopping list. Fractions
// instead of decimals, grams rounded by size and shown in kg from 1000, halves of pieces, 3 TL as 1 EL, ranges at
// both ends, and amounts that never scale. Plain text with fraction characters, no HTML. Testable without Vue.

export interface KhUnit {
  name?: string | null;
  pluralName?: string | null;
  abbreviation?: string | null;
  pluralAbbreviation?: string | null;
  useAbbreviation?: boolean | null;
}

export interface KhAmount {
  quantity: number;
  upper?: number | null; // upper end of a range ("2–3 EL")
  fixed?: boolean; // never scaled
  unit?: KhUnit | null;
  food?: string | null; // the food's name, for the egg tip
}

export interface KhAmountText {
  quantity: string;
  unit: string | null; // null: Mealie's unit text stays
  eggTip: boolean; // half an egg: "whisk one egg and use half"
}

const FRACTIONS: [number, string][] = [[1 / 4, "¼"], [1 / 3, "⅓"], [1 / 2, "½"], [2 / 3, "⅔"], [3 / 4, "¾"]];
const NEAR = 0.05; // how far a value may be from a fraction or a whole number to be shown as it
const GRAMS = ["g", "gramm", "gram", "grams"];
const MILLILITRES = ["ml", "milliliter", "millilitre", "milliliters", "millilitres"];
const PIECES = ["stuck", "stk", "piece", "pieces"];
const PINCHES = ["prise", "prisen", "messerspitze", "messerspitzen", "msp", "pinch", "pinches"];
const EGGS = ["ei", "eier", "egg", "eggs"];
const SPOONS = [
  { from: ["tl", "teeloffel"], abbreviation: "EL", name: "Esslöffel", plural: "Esslöffel" },
  { from: ["tsp", "teaspoon", "teaspoons"], abbreviation: "tbsp", name: "tablespoon", plural: "tablespoons" },
];

/** A name in the form units are compared in: without accents and punctuation, in lower case ("Stück" → "stuck"). */
function plain(text: string | null | undefined): string {
  return (text ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^\p{L}\p{N}]+/gu, " ").trim().toLowerCase();
}

/** Whether the unit goes by one of NAMES, in any of its four forms. */
function unitIs(unit: KhUnit | null | undefined, names: string[]): boolean {
  const forms = [unit?.name, unit?.pluralName, unit?.abbreviation, unit?.pluralAbbreviation];
  return forms.some(form => form && names.includes(plain(form)));
}

/** A number with at most DIGITS decimals in the reader's way of writing them. */
function decimal(value: number, locale: string, digits: number): string {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: digits, useGrouping: false }).format(value);
}

/** A whole number or a fraction character when the value is close to one, else one decimal: 1.5 → "1½". */
function fractionText(value: number, locale: string): string {
  const whole = Math.floor(value + NEAR); // 1.97 counts as 2
  const part = value - whole;
  if (whole > 0 && Math.abs(part) <= NEAR) return String(whole);
  const fraction = FRACTIONS.find(([share]) => Math.abs(part - share) <= NEAR);
  return fraction ? `${whole || ""}${fraction[1]}` : decimal(value, locale, 1);
}

/** Grams or millilitres rounded by size: under 10 to a tenth, up to 99 whole, then to 5, from 500 to 10. */
function roundMetric(value: number): number {
  if (value < 10) return Math.round(value * 10) / 10;
  if (value < 100) return Math.round(value);
  if (value < 500) return Math.round(value / 5) * 5;
  return value < 1000 ? Math.round(value / 10) * 10 : value;
}

/** Pieces in halves, at least half a piece. */
function halves(value: number): number {
  return Math.max(0.5, Math.round(value * 2) / 2);
}

/** One end of an amount by its unit's rules, without changing the unit. */
function endText(value: number, unit: KhUnit | null | undefined, locale: string): string {
  if (unitIs(unit, GRAMS) || unitIs(unit, MILLILITRES)) return decimal(roundMetric(value), locale, 1);
  if (!unit || unitIs(unit, PIECES)) return fractionText(halves(value), locale);
  return fractionText(value, locale);
}

/** A single amount, where the unit may change: grams to kg and millilitres to l from 1000, 3 TL to 1 EL. */
function singleText(value: number, unit: KhUnit | null | undefined, locale: string): Omit<KhAmountText, "eggTip"> {
  const metric = unitIs(unit, GRAMS) ? "kg" : unitIs(unit, MILLILITRES) ? "l" : null;
  if (metric && roundMetric(value) >= 1000) return { quantity: decimal(roundMetric(value) / 1000, locale, 2), unit: metric };
  const spoon = SPOONS.find(spoon => unitIs(unit, spoon.from));
  const spoons = value / 3;
  if (spoon && spoons >= 1 && Math.abs(spoons - Math.round(spoons)) < 0.01) {
    const name = unit?.useAbbreviation ? spoon.abbreviation : spoons > 1 ? spoon.plural : spoon.name;
    return { quantity: fractionText(spoons, locale), unit: name };
  }
  return { quantity: endText(value, unit, locale), unit: null };
}

/** The amount at SCALE as the reader sees it. Fixed amounts (by mark or a pinch unit) never scale; a range scales at
 * both ends and keeps its unit; a positive amount never shows as 0. */
export function formatAmount(amount: KhAmount, scale: number, locale: string): KhAmountText {
  const factor = amount.fixed || unitIs(amount.unit, PINCHES) ? 1 : scale;
  const value = amount.quantity * factor;
  const upper = amount.upper ? amount.upper * factor : null;
  const shown = upper
    ? { quantity: `${endText(value, amount.unit, locale)}–${endText(upper, amount.unit, locale)}`, unit: null }
    : singleText(value, amount.unit, locale);
  const quantity = value > 0 && /^0$/.test(shown.quantity) ? `< ${decimal(0.1, locale, 1)}` : shown.quantity;
  const pieces = !amount.unit || unitIs(amount.unit, PIECES);
  const eggTip = !upper && pieces && EGGS.includes(plain(amount.food)) && halves(value) % 1 !== 0;
  return { quantity, unit: shown.unit, eggTip };
}
