// KH: what the text export dialogs need from the running app (D61): Mealie's own ingredient display and the amounts
// of the recipe, made during setup (the display needs Vuetify's locale), plus sharing, copying and saving a file.
import { KhAmountsApi } from "../lib/api/amounts";
import { KhNotesApi } from "../lib/api/notes";
import { khAmounts, khStepText } from "../lib/amounts-store";
import { recipeText } from "../lib/recipe-text";
import { useRequests } from "~/composables/api/api-client";
import { useIngredientTextParser } from "~/composables/recipes/use-recipe-ingredients";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import type { RecipeOut } from "~/lib/api/types/recipe";

/** Reads recipes as text the way their page shows them. Call it while a component is set up. */
export function useRecipeText() {
  const requests = useRequests();
  const api = new KhAmountsApi(requests);
  const notes = new KhNotesApi(requests);
  let familyNote = ""; // the household's note of the recipe loaded last (D82)
  const { parseIngredientText } = useIngredientTextParser();
  const locale = useGlobalI18n().locale;

  /** Makes the store hold RECIPE's amounts (ranges, fixed lines, step links), as its page does, and loads the household's
   * note for text() (none after a failed request); a failed request
   * leaves it empty, never the amounts of another recipe. Returns what the store held before, so a caller that must
   * not change the open recipe's view can put it back. */
  async function loadAmounts(recipe: RecipeOut) {
    const before = khAmounts.value;
    const { data } = recipe.id ? await api.get(recipe.id) : { data: null };
    khAmounts.value = data ?? { extras: [], stepAmounts: [] };
    familyNote = recipe.id ? ((await notes.get(recipe.id)).data?.text ?? "") : "";
    return before;
  }

  /** RECIPE at SCALE as text; the store must hold its amounts and note (loadAmounts). */
  function text(recipe: RecipeOut, scale: number): string {
    return recipeText(recipe, scale, locale.value, {
      ingredient: (line, factor) => parseIngredientText(line, factor, false),
      step: (place, step, factor) => khStepText(place, step.text ?? "", recipe.recipeIngredient ?? [], factor),
    }, familyNote);
  }

  return { loadAmounts, text };
}

/** Gives TEXT to the device's share menu; false if there is none or it failed (the caller then copies). Closing the
 * menu without sharing is no failure. */
export async function shareText(title: string, text: string): Promise<boolean> {
  if (!navigator.share) return false;
  try {
    await navigator.share({ title, text });
    return true;
  }
  catch (error) {
    return error instanceof DOMException && error.name === "AbortError";
  }
}

/** Puts TEXT on the clipboard; false if the browser refuses. */
export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  }
  catch {
    return false;
  }
}

/** Lets the browser save DATA as the file NAME. */
export function saveFile(name: string, data: BlobPart, type: string): void {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([data], { type }));
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 60_000); // iOS Safari asks before it saves; the address must live until then
}
