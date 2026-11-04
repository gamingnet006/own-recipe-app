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
  plural: boolean; // the unit reads in the plural: more than one is shown ("1 Prise" stays one at any factor)
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
function singleText(value: number, unit: KhUnit | null | undefined, locale: string): Pick<KhAmountText, "quantity" | "unit"> {
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
  return { quantity, unit: shown.unit, plural: (upper ?? value) > 1, eggTip };
}

// The three ways to scale (A3) and the hint on times (A5). Each factor is null when the input is no usable number,
// so the sheet keeps the old factor instead of showing NaN.

export type KhPan = { shape: "round"; diameter: number } | { shape: "rect"; length: number; width: number };

const NUMBER = String.raw`(\d+(?:[.,]\d+)?)`;
const RECT_PAN = new RegExp(`${NUMBER}\\s*[x×]\\s*${NUMBER}`, "i");
const ROUND_PAN = [
  new RegExp(`Ø\\s*${NUMBER}`, "i"), // "Springform Ø 26 cm"
  new RegExp(`${NUMBER}\\s*er\\s+(?:Spring|Tarte|Back)?form`, "i"), // "26er Springform"
  new RegExp(`(?:Springform|Tarteform|rund)\\D*${NUMBER}\\s*cm`, "i"), // "Springform 26 cm"
  // Mealie's import moves a yield's number in front of its text: "26" and "Springform Ø cm" joined
  new RegExp(`${NUMBER}\\s+(?:Spring|Tarte|Back)?form`, "i"),
];

/** A positive, finite number, else null. */
function usable(value: number): number | null {
  return Number.isFinite(value) && value > 0 ? value : null;
}

/** The factor for NEW servings of a recipe made for BASE. */
export function servingsFactor(servings: number, base: number): number | null {
  const s = usable(servings);
  const b = usable(base);
  return s && b ? s / b : null;
}

/** The factor when only HAVE of an ingredient the recipe wants BASE of is there: 300 g of 250 g → 1.2. */
export function haveOnlyFactor(have: number, base: number): number | null {
  return servingsFactor(have, base);
}

/** A pan's area in square centimetres, null for a side that is not positive. */
function panArea(pan: KhPan): number | null {
  if (pan.shape === "round") {
    const d = usable(pan.diameter);
    return d ? Math.PI * (d / 2) ** 2 : null;
  }
  const l = usable(pan.length);
  const w = usable(pan.width);
  return l && w ? l * w : null;
}

/** The factor from one pan to another: new area ÷ old area (Ø 26 → Ø 20 cm gives 0.59). */
export function panFactor(from: KhPan, to: KhPan): number | null {
  const old = panArea(from);
  const area = panArea(to);
  return old && area ? area / old : null;
}

/** The pan a yield names, such as "Springform Ø 26 cm", "26er Springform" or "24 x 30 cm"; null for anything else. */
export function parsePan(text: string | null | undefined): KhPan | null {
  const number = (value: string) => Number(value.replace(",", "."));
  const rect = text?.match(RECT_PAN);
  if (rect) return { shape: "rect", length: number(rect[1]!), width: number(rect[2]!) };
  const round = ROUND_PAN.map(pattern => text?.match(pattern)).find(Boolean);
  return round ? { shape: "round", diameter: number(round[1]!) } : null;
}

/** Whether times may change noticeably: the amount more than doubled or less than halved. */
export function timeHint(scale: number): boolean {
  return scale > 2 || scale < 0.5;
}

// The review's view of a step's links (A2): which pieces of the text are linked places.

/** A step's text in pieces: plain text, and each linked place with its index in LINKS. A link whose text no longer
 * stands at its place, or that overlaps an earlier one, is left out, so a stale link never changes the text. */
export function stepSegments(
  text: string,
  links: { start: number; end: number; text: string }[],
): { text: string; link: number | null }[] {
  const valid = links
    .map((link, index) => ({ ...link, index }))
    .filter(link => text.slice(link.start, link.end) === link.text)
    .sort((a, b) => a.start - b.start);
  const segments: { text: string; link: number | null }[] = [];
  let at = 0;
  for (const link of valid) {
    if (link.start < at) continue; // overlaps the one before
    if (link.start > at) segments.push({ text: text.slice(at, link.start), link: null });
    segments.push({ text: link.text, link: link.index });
    at = link.end;
  }
  if (at < text.length) segments.push({ text: text.slice(at), link: null });
  return segments;
}

// Linked amounts in the step text at the view's factor (A2); the text itself stays as saved (D19).

/** A link from a step's text to an ingredient, as /api/kh/amounts sends it; STEP is the step's place, from 0. */
export interface KhStepLink {
  step: number;
  start: number;
  end: number;
  text: string;
  referenceId: string;
  fraction: number;
}

// the number a link's text starts with, as the backend's QUANTITY reads it in a step
const LEADING_NUMBER = /^(?:\d+\s+\d+\/[1-9]\d*|\d+\/[1-9]\d*|(?:\d+ ?)?[¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|\d+(?:[.,]\d+)?)/;

/** The step's text at SCALE: each linked amount whose text still stands at its place becomes its ingredient's amount
 * times the link's fraction, shown like the ingredient list; the unit stays as written unless it changes (kg).
 * Replaced from the end, so earlier places stay right; at scale 1 the text stays word for word. */
export function scaleStepText(
  text: string,
  links: KhStepLink[],
  ingredients: Map<string, KhAmount>,
  scale: number,
  locale: string,
): string {
  if (scale === 1) return text;
  const valid = links.filter(link => text.slice(link.start, link.end) === link.text).sort((a, b) => b.start - a.start);
  let result = text;
  let limit = text.length; // a link reaching past the one replaced after it overlaps it
  for (const link of valid) {
    const amount = ingredients.get(link.referenceId);
    if (!amount || link.end > limit) continue;
    const shown = formatAmount({ ...amount, quantity: amount.quantity * link.fraction, upper: null }, scale, locale);
    const number = link.text.match(LEADING_NUMBER)?.[0] ?? "";
    const unit = shown.unit ? ` ${shown.unit}` : link.text.slice(number.length);
    result = result.slice(0, link.start) + shown.quantity + unit + result.slice(link.end);
    limit = link.start;
  }
  return result;
}
