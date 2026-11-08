// KH: the text of a step as the views show it (D41, D42): the amount of an ingredient in parentheses behind its name,
// and every recognized time wrapped in a span that can be tapped. The stored text never changes.
import { parseTimes, type KhTime } from "./times";
import { khAmounts, khStepText } from "./amounts-store";
import { useIngredientTextParser } from "~/composables/recipes/use-recipe-ingredients";
import type { Recipe, RecipeStep } from "~/lib/api/types/recipe";

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

/** The one entry point for every view: step STEP at place PLACE of RECIPE at SCALE, with the amounts of
 * Phase 3 scaled first, then amounts and times added. */
export function khStepDisplay(place: number, step: RecipeStep, recipe: Recipe, scale: number): { html: string; times: KhTime[] } {
  const { useParsedIngredientText } = useIngredientTextParser();
  const lines = recipe.recipeIngredient ?? [];
  const ingredients = lines.flatMap((line): KhStepIngredient[] => {
    if (!line.referenceId || !line.food) return [];
    const { quantity, unit } = useParsedIngredientText(line, scale, false);
    return [{
      referenceId: line.referenceId,
      names: [line.food.name, line.food.pluralName ?? ""],
      amount: quantity ? `${quantity} ${unit ?? ""}`.trim() : null,
    }];
  });
  const linkedIds = new Set(khAmounts.value.stepAmounts.filter(link => link.step === place).map(link => link.referenceId));
  return stepDisplay(place, khStepText(place, step.text, lines, scale), ingredients, recipe.recipeInstructions ?? [], linkedIds);
}
