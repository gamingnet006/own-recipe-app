// KH: the open recipe's amounts for every view of it (D39): what /api/kh/amounts answered, read by Mealie's
// ingredient display and its steps. Free of the request helpers, so Mealie's display and its tests import no API code.
import { computed, ref } from "vue";
import type { KhAmounts } from "./api/amounts";
import { scaleStepText, type KhAmount } from "./amounts";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import type { RecipeIngredient } from "~/lib/api/types/recipe";

/** The last answer for the open recipe; empty until one arrives. */
export const khAmounts = ref<KhAmounts>({ extras: [], stepAmounts: [] });

const extras = computed(() => new Map(khAmounts.value.extras.map(extra => [extra.referenceId, extra])));

/** The range end and fixed mark of an ingredient line of the open recipe, if it has any. */
export function khExtra(referenceId: string | null | undefined): { upper: number | null; fixed: boolean } | undefined {
  const extra = referenceId ? extras.value.get(referenceId) : undefined;
  return extra ? { upper: extra.upper, fixed: extra.fixed } : undefined;
}

/** A step's text for the views at SCALE, its linked amounts scaled; PLACE is the step's place in the recipe, from 0.
 * Without links, or at scale 1, the text as saved. */
export function khStepText(place: number, text: string, ingredients: RecipeIngredient[], scale: number): string {
  const links = khAmounts.value.stepAmounts.filter(link => link.step === place);
  if (!links.length) return text;
  const lines = new Map<string, KhAmount>();
  for (const line of ingredients) {
    if (line.referenceId && line.quantity) {
      lines.set(line.referenceId, { quantity: line.quantity, unit: line.unit, food: line.food?.name, ...khExtra(line.referenceId), upper: null });
    }
  }
  return scaleStepText(text, links, lines, scale, useGlobalI18n().locale.value);
}
