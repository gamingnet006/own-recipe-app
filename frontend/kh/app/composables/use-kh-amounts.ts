// KH: loading a recipe's amounts for its views (D39): made during setup, so Mealie's request helpers have the app.
import { useRequests } from "~/composables/api/api-client";
import { KhAmountsApi } from "../lib/api/amounts";
import { khAmounts } from "../lib/amounts-store";

/** The loader for the open recipe's amounts; a failed request leaves the views without ranges and links. */
export function useKhAmounts() {
  const api = new KhAmountsApi(useRequests());

  async function loadKhAmounts(recipeId: string) {
    const { data } = await api.get(recipeId);
    khAmounts.value = data ?? { extras: [], stepAmounts: [] };
  }

  return { loadKhAmounts };
}
