// KH: the recipe view's arithmetic (D38): the times shown as tiles, what the amount stepper starts from and when it is
// offered, a step of one whole piece or serving as Mealie's scale, and the words after the amount. Testable without Vue.
import { recipeTimeDisplay } from "~/composables/recipes/use-recipe-time";

export type KhTimeKey = "prep" | "perform" | "total";

interface Times {
  prepTime?: string | null;
  performTime?: string | null;
  totalTime?: string | null;
  prepTimeSeconds?: number | null;
  performTimeSeconds?: number | null;
  totalTimeSeconds?: number | null;
}

interface Amount {
  recipeYieldQuantity?: number | null;
  recipeYield?: string | null;
  recipeServings?: number | null;
}

/** The recipe's times in the order of the tiles, only those it has, written out as Mealie does. */
export function recipeTimes(recipe: Times, locale: string): { key: KhTimeKey; value: string }[] {
  const times: [KhTimeKey, number | null | undefined, string | null | undefined][] = [
    ["prep", recipe.prepTimeSeconds, recipe.prepTime],
    ["perform", recipe.performTimeSeconds, recipe.performTime],
    ["total", recipe.totalTimeSeconds, recipe.totalTime],
  ];
  return times
    .map(([key, seconds, text]) => ({ key, value: recipeTimeDisplay(seconds, text, locale) }))
    .filter(time => time.value);
}

/** What the amount stepper starts from: the yield ("12 pieces"), else the servings, else 0 for no stepper. */
export function scaleBase(recipe: Amount): number {
  return recipe.recipeYieldQuantity || recipe.recipeServings || 0;
}

/** Whether scaling changes anything: imported ingredients stay text without an amount until they are parsed. */
export function scalesAmounts(recipe: { recipeIngredient?: { quantity?: number | null }[] }): boolean {
  return (recipe.recipeIngredient ?? []).some(ingredient => !!ingredient.quantity);
}

/** Mealie's scale for one whole piece or serving more (+1) or less (-1) than shown now, never below one. */
export function stepScale(base: number, scale: number, delta: 1 | -1): number {
  const shown = Number((base * scale).toFixed(3)); // rounded like Mealie's display, so 6.9999… counts as 7
  const next = delta > 0 ? Math.floor(shown) + 1 : Math.ceil(shown) - 1;
  return Math.max(next, 1) / base;
}

/** The words after the amount: the yield's own ("pieces"), else serving(s) for AMOUNT and a yield text without number. */
export function scaleLabel(recipe: Amount, amount: number, t: (key: string, count: number) => string): string {
  const text = recipe.recipeYield?.trim() ?? "";
  if (recipe.recipeYieldQuantity || !recipe.recipeServings) return text;
  return [t("kh.recipe.servings", amount), text].filter(Boolean).join(" · ");
}
