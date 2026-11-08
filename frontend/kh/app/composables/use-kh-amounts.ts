// KH: loading a recipe's amounts for its views (D39): made during setup, so Mealie's request helpers have the app.
import { watch } from "vue";
import { useRequests } from "~/composables/api/api-client";
import { KhAmountsApi } from "../lib/api/amounts";
import { khAmounts } from "../lib/amounts-store";

/** Keeps the store on the open RECIPE's amounts: loads them when it opens and again after each save (its dateUpdated
 * changes, and the backend may have moved or dropped links), and drops an answer a newer request overtook. A failed
 * request leaves the views without ranges and links. */
export function useKhAmounts(recipe: () => { id?: string | null; dateUpdated?: string | null }) {
  const api = new KhAmountsApi(useRequests());
  let asked = 0;

  watch(() => [recipe().id, recipe().dateUpdated], async ([id]) => {
    if (!id) return;
    const mine = ++asked;
    const { data } = await api.get(id);
    if (mine === asked) khAmounts.value = data ?? { extras: [], stepAmounts: [] };
  }, { immediate: true });
}
