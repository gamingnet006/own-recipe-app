// KH: the text of a step as the views show it (D41, D42): the amount of an ingredient in parentheses behind its name,
// and every recognized time wrapped in a span that can be tapped. The stored text never changes.
import { parseTimes, type KhTime } from "./times";
import { ovenBrackets, type Oven } from "./oven";
import { khAmounts, khStepText } from "./amounts-store";
import { useIngredientTextParser } from "~/composables/recipes/use-recipe-ingredients";
import type { Recipe, RecipeIngredient, RecipeStep } from "~/lib/api/types/recipe";

/** An ingredient of the recipe as a step needs it; AMOUNT is html-safe, e.g. "200 g" at the current factor.
 * SHAREAMOUNT gives the amount of a FRACTION (0 to 1) of it in the same format. */
export interface KhStepIngredient {
  referenceId: string;
  names: string[];
  amount: string | null;
  shareAmount?: (fraction: number) => string | null;
}

type StepReferences = { text?: string; ingredientReferences?: { referenceId?: string | null }[] };

/** Whether STEP references the ingredient REFERENCEID. */
function references(step: StepReferences | undefined, referenceId: string): boolean {
  return !!step?.ingredientReferences?.some(r => r.referenceId === referenceId);
}

/** The place of the one step that references REFERENCEID; null if no step or several do (then no amount is
 * shown, since the whole amount would not fit one step). */
export function onlyStepOf(referenceId: string, steps: StepReferences[]): number | null {
  const places = steps.flatMap((step, place) => (references(step, referenceId) ? [place] : []));
  return places.length === 1 ? places[0]! : null;
}

/** A pattern for the first whole-word, case-insensitive appearance of one of NAMES; longer names first, so
 * "Eier" wins over "Ei". */
function wholeWord(names: string[]): RegExp {
  const escaped = names.filter(Boolean).sort((a, b) => b.length - a.length).map(n => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  return new RegExp(`(?<![\\p{L}\\d])(?:${escaped.join("|")})(?![\\p{L}\\d])`, "iu");
}

// Words that name a part of an ingredient right before its name (German and English), as regex sources.
const FRACTION_PHRASES: [string, number][] = [
  ["drei viertel|three quarters?", 3 / 4],
  ["zwei drittel|two thirds?", 2 / 3],
  ["ein drittel|a third", 1 / 3],
  ["ein viertel|a quarter", 1 / 4],
  ["(?:die )?hälfte|half|½|1/2", 1 / 2],
  ["⅓|1/3", 1 / 3],
  ["⅔|2/3", 2 / 3],
  ["¼|1/4", 1 / 4],
  ["¾|3/4", 3 / 4],
];
const REMAINDER_WORDS = "rest|restliche[nmrs]?|übrige[nmrs]?|remaining";
/** How many words may stand between such a phrase and the ingredient name ("die Hälfte vom Mehl"). */
const PHRASE_GAP_WORDS = 3;
/** Marks "the rest" in place of a fraction. */
const REST = "rest";

/** NAMES plus their genitive forms ("Mehl" gives "Mehls", "Mehles"). */
function withGenitive(names: string[]): string[] {
  return names.filter(Boolean).flatMap(n => [n, `${n}s`, `${n}es`]);
}

/** What the text right before the first appearance of one of NAMES in TEXT says about the part: a fraction of the
 * whole, REST, or null; END is where the name ends. Null if the name does not appear. */
function partNamed(text: string, names: string[]): { part: number | typeof REST | null; end: number } | null {
  const match = wholeWord(withGenitive(names)).exec(text);
  if (!match) return null;
  const before = text.slice(0, match.index);
  const gap = `(?:\\s+\\p{L}+){0,${PHRASE_GAP_WORDS}}\\s+$`;
  const ends = (words: string) => new RegExp(`(?<![\\p{L}\\d])(?:${words})${gap}`, "iu").test(before);
  const phrase = FRACTION_PHRASES.find(([words]) => ends(words));
  return { part: phrase ? phrase[1] : ends(REMAINDER_WORDS) ? REST : null, end: match.index + match[0].length };
}

/** The fraction of an ingredient that step PLACE (text TEXT) names and the end of its name there; null if the
 * step names none, or the rest after earlier steps that did not all name their share. */
function namedShare(
  referenceId: string,
  names: string[],
  place: number,
  text: string,
  steps: StepReferences[],
): { fraction: number; end: number } | null {
  let used: number | null = 0; // null once an earlier step named no share, so the rest is unknown
  for (let i = 0; i < place; i++) {
    if (!references(steps[i], referenceId)) continue;
    const part = partNamed(steps[i]!.text ?? "", names)?.part ?? null;
    used = part === null || used === null ? null : used + (part === REST ? 1 - used : part);
  }
  const named = partNamed(text, names);
  if (!named || named.part === null) return null;
  const fraction = named.part === REST ? (used === null ? 0 : 1 - used) : named.part;
  return fraction > 0 ? { fraction, end: named.end } : null;
}

/** Where in TEXT (step PLACE) INGREDIENT's amount goes and which: the whole amount for an ingredient of this step
 * only, the share the text names for one of several steps; null if none applies. */
function amountSpot(ingredient: KhStepIngredient, place: number, text: string, steps: StepReferences[]): { end: number; amount: string } | null {
  if (onlyStepOf(ingredient.referenceId, steps) === place) {
    const match = wholeWord(ingredient.names).exec(text);
    return match && ingredient.amount ? { end: match.index + match[0].length, amount: ingredient.amount } : null;
  }
  if (!references(steps[place], ingredient.referenceId)) return null;
  const share = namedShare(ingredient.referenceId, ingredient.names, place, text, steps);
  const amount = share && ingredient.shareAmount?.(share.fraction);
  return share && amount ? { end: share.end, amount } : null;
}

/** TEXT (already scaled) of step PLACE for display: HTML-wrapped times (TIMES[i] belongs to the i-th
 * "kh-time" span), the bracket for the reader's OVEN behind each oven temperature (none for null), and amounts behind the names of ingredients that only this step uses and that have no
 * step amount (LINKEDIDS) in it already. An ingredient of several steps gets an amount where the text
 * names its share ("die Hälfte des Mehls"). Markdown stays as written. */
export function stepDisplay(
  place: number,
  text: string,
  ingredients: KhStepIngredient[],
  steps: StepReferences[],
  linkedIds: Set<string>,
  oven: Oven | null = null,
): { html: string; times: KhTime[] } {
  const times = parseTimes(text);
  const inserts: [number, string][] = times.flatMap(t => [[t.start, "<span class=\"kh-time\">"], [t.end, "</span>"]] as [number, string][]);
  for (const ingredient of ingredients) {
    if (!ingredient.amount || !ingredient.names.length || linkedIds.has(ingredient.referenceId)) continue;
    const spot = amountSpot(ingredient, place, text, steps);
    if (spot) inserts.push([spot.end, ` <span class="kh-amount">(${spot.amount})</span>`]);
  }
  if (oven) {
    for (const { at, text: bracket } of ovenBrackets(text, oven)) inserts.push([at, ` <span class="kh-amount">${bracket.trimStart()}</span>`]);
  }
  // From the end, so earlier offsets stay valid; the sort is stable, so equal offsets keep their order.
  let html = text;
  for (const [offset, insert] of inserts.sort((a, b) => b[0] - a[0])) html = html.slice(0, offset) + insert + html.slice(offset);
  return { html, times };
}

/** The index of the time (among the ".kh-time" elements of CONTAINER) that TARGET lies in; -1 if it lies in none. */
export function timeIndex(target: EventTarget | null, container: HTMLElement): number {
  if (!(target instanceof Node)) return -1;
  return [...container.querySelectorAll(".kh-time")].findIndex(span => span.contains(target));
}

const LABEL_WORDS = 4;

/** The name of a timer started in step PLACE (0-based): its number and the first words of TEXT, Markdown marks removed. */
export function timerLabel(place: number, text: string): string {
  const plain = text.replace(/\]\([^)]*\)/g, "").replace(/[*_`#>[\]]/g, "");
  return `${place + 1}. ${plain.split(/\s+/).filter(Boolean).slice(0, LABEL_WORDS).join(" ")}`;
}

/** An ingredient as the step view lists it under "Du brauchst:". */
export interface KhNeed {
  referenceId: string;
  name: string;
  names: string[];
  amount: string | null;
  shareAmount?: (fraction: number) => string | null;
}

/** The entries of the "Du brauchst:" line of step PLACE ("Butter 200 g"): the ingredients the step references, with
 * the amount for those no other step uses, or the share the step text names ("Mehl 125 g"); else the name alone
 * (the whole amount would not fit one of several steps). */
export function stepNeeds(place: number, step: StepReferences, needs: KhNeed[], steps: StepReferences[]): string[] {
  const referenced = new Set(step.ingredientReferences?.map(r => r.referenceId));
  return needs
    .filter(need => referenced.has(need.referenceId))
    .map((need) => {
      if (onlyStepOf(need.referenceId, steps) === place) return need.amount ? `${need.name} ${need.amount}` : need.name;
      const share = namedShare(need.referenceId, need.names, place, step.text ?? "", steps);
      const amount = share && need.shareAmount?.(share.fraction);
      return amount ? `${need.name} ${amount}` : need.name;
    });
}

/** The shown amount ("200 g") of ingredient LINE at SCALE; null without a quantity. */
function lineAmount(line: RecipeIngredient, scale: number): string | null {
  const { quantity, unit } = useIngredientTextParser().useParsedIngredientText(line, scale, false);
  return quantity ? `${quantity} ${unit ?? ""}`.trim() : null;
}

/** The "Du brauchst:" entries of step STEP at place PLACE of RECIPE at SCALE. */
export function khStepNeeds(place: number, step: RecipeStep, recipe: Recipe, scale: number): string[] {
  const needs = (recipe.recipeIngredient ?? []).flatMap((line): KhNeed[] => {
    const name = line.food?.name ?? line.note;
    if (!line.referenceId || !name) return [];
    return [{ referenceId: line.referenceId, name, names: [name, line.food?.pluralName ?? ""], amount: lineAmount(line, scale), shareAmount: fraction => lineAmount(line, scale * fraction) }];
  });
  return stepNeeds(place, step, needs, recipe.recipeInstructions ?? []);
}

/** The times of step PLACE in the order its text shows them, matching khStepDisplay's times. Needs no Vuetify locale,
 * so a click handler can call it (the display's amount text can only be built while a component renders). */
export function khStepTimes(place: number, step: RecipeStep, recipe: Recipe, scale: number): KhTime[] {
  return parseTimes(khStepText(place, step.text, recipe.recipeIngredient ?? [], scale));
}

/** The one entry point for every view: step STEP at place PLACE of RECIPE at SCALE, with the amounts of
 * Phase 3 scaled first, then amounts, times and the OVEN's temperature brackets added (OVEN null: no brackets).
 * Call it while a component renders only: the amount text needs Vuetify's locale. */
export function khStepDisplay(place: number, step: RecipeStep, recipe: Recipe, scale: number, oven: Oven | null = null): { html: string; times: KhTime[] } {
  const lines = recipe.recipeIngredient ?? [];
  const ingredients = lines.flatMap((line): KhStepIngredient[] => {
    if (!line.referenceId || !line.food) return [];
    return [{
      referenceId: line.referenceId,
      names: [line.food.name, line.food.pluralName ?? ""],
      amount: lineAmount(line, scale),
      shareAmount: fraction => lineAmount(line, scale * fraction),
    }];
  });
  const linkedIds = new Set(khAmounts.value.stepAmounts.filter(link => link.step === place).map(link => link.referenceId));
  return stepDisplay(place, khStepText(place, step.text, lines, scale), ingredients, recipe.recipeInstructions ?? [], linkedIds, oven);
}
