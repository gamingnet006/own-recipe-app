// KH: the text of a step as the views show it (D41, D42): the amount of an ingredient in parentheses behind its name,
// and every recognized time wrapped in a span that can be tapped. The stored text never changes.
import { parseTimes, type KhTime } from "./times";
import { khAmounts, khStepText } from "./amounts-store";
import { useIngredientTextParser } from "~/composables/recipes/use-recipe-ingredients";
import type { Recipe, RecipeIngredient, RecipeStep } from "~/lib/api/types/recipe";

/** An ingredient of the recipe as a step needs it; AMOUNT is html-safe, e.g. "200 g" at the current factor. */
export interface KhStepIngredient {
  referenceId: string;
  names: string[];
  amount: string | null;
}

type StepReferences = { ingredientReferences?: { referenceId?: string | null }[] };

/** The place of the one step that references REFERENCEID; null if no step or several do (then no amount is
 * shown, since the whole amount would not fit one step). */
export function onlyStepOf(referenceId: string, steps: StepReferences[]): number | null {
  const places = steps.flatMap((step, place) => (step.ingredientReferences?.some(r => r.referenceId === referenceId) ? [place] : []));
  return places.length === 1 ? places[0]! : null;
}

/** A pattern for the first whole-word, case-insensitive appearance of one of NAMES; longer names first, so
 * "Eier" wins over "Ei". */
function wholeWord(names: string[]): RegExp {
  const escaped = names.filter(Boolean).sort((a, b) => b.length - a.length).map(n => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  return new RegExp(`(?<![\\p{L}\\d])(?:${escaped.join("|")})(?![\\p{L}\\d])`, "iu");
}

/** TEXT (already scaled) of step PLACE for display: HTML-wrapped times (TIMES[i] belongs to the i-th
 * "kh-time" span) and amounts behind the names of ingredients that only this step uses and that have no
 * step amount (LINKEDIDS) in it already. Markdown stays as written. */
export function stepDisplay(
  place: number,
  text: string,
  ingredients: KhStepIngredient[],
  steps: StepReferences[],
  linkedIds: Set<string>,
): { html: string; times: KhTime[] } {
  const times = parseTimes(text);
  const inserts: [number, string][] = times.flatMap(t => [[t.start, "<span class=\"kh-time\">"], [t.end, "</span>"]] as [number, string][]);
  for (const ingredient of ingredients) {
    if (!ingredient.amount || !ingredient.names.length || linkedIds.has(ingredient.referenceId)) continue;
    if (onlyStepOf(ingredient.referenceId, steps) !== place) continue;
    const match = wholeWord(ingredient.names).exec(text);
    if (match) inserts.push([match.index + match[0].length, ` <span class="kh-amount">(${ingredient.amount})</span>`]);
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
  amount: string | null;
}

/** The entries of the "Du brauchst:" line of step PLACE ("Butter 200 g"): the ingredients the step references, with
 * the amount only for those no other step uses (the whole amount would not fit one of several steps). */
export function stepNeeds(place: number, step: StepReferences, needs: KhNeed[], steps: StepReferences[]): string[] {
  const referenced = new Set(step.ingredientReferences?.map(r => r.referenceId));
  return needs
    .filter(need => referenced.has(need.referenceId))
    .map(need => (need.amount && onlyStepOf(need.referenceId, steps) === place ? `${need.name} ${need.amount}` : need.name));
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
    return line.referenceId && name ? [{ referenceId: line.referenceId, name, amount: lineAmount(line, scale) }] : [];
  });
  return stepNeeds(place, step, needs, recipe.recipeInstructions ?? []);
}

/** The times of step PLACE in the order its text shows them, matching khStepDisplay's times. Needs no Vuetify locale,
 * so a click handler can call it (the display's amount text can only be built while a component renders). */
export function khStepTimes(place: number, step: RecipeStep, recipe: Recipe, scale: number): KhTime[] {
  return parseTimes(khStepText(place, step.text, recipe.recipeIngredient ?? [], scale));
}

/** The one entry point for every view: step STEP at place PLACE of RECIPE at SCALE, with the amounts of
 * Phase 3 scaled first, then amounts and times added. */
export function khStepDisplay(place: number, step: RecipeStep, recipe: Recipe, scale: number): { html: string; times: KhTime[] } {
  const lines = recipe.recipeIngredient ?? [];
  const ingredients = lines.flatMap((line): KhStepIngredient[] => {
    if (!line.referenceId || !line.food) return [];
    return [{ referenceId: line.referenceId, names: [line.food.name, line.food.pluralName ?? ""], amount: lineAmount(line, scale) }];
  });
  const linkedIds = new Set(khAmounts.value.stepAmounts.filter(link => link.step === place).map(link => link.referenceId));
  return stepDisplay(place, khStepText(place, step.text, lines, scale), ingredients, recipe.recipeInstructions ?? [], linkedIds);
}
