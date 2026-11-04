// KH: the open recipe's amounts for every view of it (D39): what /api/kh/amounts answered, read by Mealie's
// ingredient display. Free of the request helpers, so Mealie's display and its tests import no API code.
import { computed, ref } from "vue";
import type { KhAmounts } from "./api/amounts";

/** The last answer for the open recipe; empty until one arrives. */
export const khAmounts = ref<KhAmounts>({ extras: [], stepAmounts: [] });

const extras = computed(() => new Map(khAmounts.value.extras.map(extra => [extra.referenceId, extra])));

/** The range end and fixed mark of an ingredient line of the open recipe, if it has any. */
export function khExtra(referenceId: string | null | undefined): { upper: number | null; fixed: boolean } | undefined {
  const extra = referenceId ? extras.value.get(referenceId) : undefined;
  return extra ? { upper: extra.upper, fixed: extra.fixed } : undefined;
}
