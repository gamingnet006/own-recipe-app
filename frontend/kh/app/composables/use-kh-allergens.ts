// KH: the warning marks of the recipe cards (D44, A2): one request per page load, shared by every card, and a refresh
// for when the intolerances or a correction change.
import { ref } from "vue";
import { useRequests } from "~/composables/api/api-client";
import { KhAllergensApi, type KhAllergenKey } from "../lib/api/allergens";

const warnings = ref<Record<string, KhAllergenKey[]>>({});
// Made during the first card's setup, so Mealie's request helpers have the app; later refreshes (a click) reuse it.
let api: KhAllergensApi | null = null;

/** Asks the server again and updates every card; does nothing while no card has asked yet (the next one asks). */
export async function refreshKhAllergenWarnings(): Promise<void> {
  if (!api) return;
  const answer = await api.getWarnings();
  if (answer.error) {
    api = null; // the next card asks again instead of every card showing no marks until a reload
    return;
  }
  warnings.value = answer.data ?? {};
}

/** The recipe slugs with an allergen somebody in the household does not tolerate, to the allergens. The first caller
 * starts the one request; a failed one leaves no marks and is retried by the next card. */
export function useKhAllergenWarnings() {
  if (!api) {
    api = new KhAllergensApi(useRequests());
    void refreshKhAllergenWarnings();
  }
  return { warnings };
}
