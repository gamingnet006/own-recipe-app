// KH: the words and numbers of the nutrition block (D44): how a value is written, the order of its rows, the per-device
// switch for showing it, and the order of the mapping page.
import { ref, watch } from "vue";
import type { KhFoodMapping, KhNutrientKey } from "./api/nutrition";

/** The rows of the table in order; DEPENDENT rows are "of which" parts of the one above. */
export const NUTRIENT_ROWS: { key: KhNutrientKey; dependent: boolean }[] = [
  { key: "kcal", dependent: false },
  { key: "fat", dependent: false },
  { key: "saturated", dependent: true },
  { key: "carbs", dependent: false },
  { key: "sugar", dependent: true },
  { key: "protein", dependent: false },
  { key: "fiber", dependent: false },
  { key: "salt", dependent: false },
];

const STORAGE_KEY = "kh-show-nutrition";

/** "320 kcal", "16 g", "0,2 g" in the number format of LOCALE; "–" for a value that was not counted. The server
 * has already rounded. */
export function formatNutrient(key: KhNutrientKey, value: number | null, locale: string): string {
  if (value === null) return "–";
  const number = new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(value);
  return `${number} ${key === "kcal" ? "kcal" : "g"}`;
}

/** The stored switch; anything but an explicit "false" is the standard (on). */
function loadShow(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) !== "false";
  }
  catch {
    return true;
  }
}

// The app runs without server rendering, so module state is shared by all users of the setting.
const show = ref(loadShow());
watch(show, value => localStorage.setItem(STORAGE_KEY, String(value)), { flush: "sync" });

/** Whether the nutrition block shows on the recipe page ("Nährwerte zeigen"), kept on the device. */
export function useKhNutritionSetting() {
  return show;
}

/** The mapping page's order: the foods still open first, each group in the order the server sent. */
export function openFirst(foods: KhFoodMapping[]): KhFoodMapping[] {
  return [...foods.filter(food => !food.confirmed), ...foods.filter(food => food.confirmed)];
}

/** The piece weight typed into the field: null when empty, the grams (comma or point), "invalid" for zero, a negative
 * number or text. */
export function parsePieceGrams(text: string): number | null | "invalid" {
  const trimmed = text.trim();
  if (!trimmed) return null;
  const grams = Number(trimmed.replace(",", "."));
  return grams > 0 ? grams : "invalid";
}
