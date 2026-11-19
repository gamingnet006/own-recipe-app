// KH: the pure parts of "Woche vorschlagen" (D70): which days still lack a dinner, what a row holds, and the entries
// that get created for the ticked rows.
import { format, isBefore, isSameDay, parseISO, startOfDay } from "date-fns";
import type { KhSuggestedRecipe } from "./api/week-suggestion";

export interface SuggestionRow {
  /** The day as yyyy-MM-dd. */
  date: string;
  recipe: KhSuggestedRecipe;
  checked: boolean;
}

/** The meal-plan entry as the planner holds it, reduced to what is needed here. */
export interface PlannedMeal {
  date: string;
  endDate?: string | null;
  entryType: string;
}

/** The days (not in the past) of DAYS that have no dinner entry yet; week entries belong to no day. */
export function daysWithoutDinner(days: Date[], meals: PlannedMeal[], today: Date = new Date()): string[] {
  const dinners = meals.filter(meal => meal.entryType === "dinner" && !meal.endDate).map(meal => parseISO(meal.date));
  return days
    .filter(day => !isBefore(day, startOfDay(today)) && !dinners.some(dinner => isSameDay(dinner, day)))
    .map(day => format(day, "yyyy-MM-dd"));
}

/** One row per free day, each with the next suggestion; rows stay short when the suggestions run out. */
export function buildRows(dates: string[], recipes: KhSuggestedRecipe[]): SuggestionRow[] {
  return dates.slice(0, recipes.length).map((date, i) => ({ date, recipe: recipes[i]!, checked: true }));
}

/** The dinner entries to create for the ticked rows. */
export function entriesToCreate(rows: SuggestionRow[]) {
  return rows.filter(row => row.checked).map(row => ({ date: row.date, entryType: "dinner" as const, recipeId: row.recipe.id }));
}

/** A short day label for a phone, "Do 20.11." (D76): weekday, day and month without the commas and dots of the locale. */
export function dayLabel(date: string, locale: string): string {
  const parts = new Intl.DateTimeFormat(locale, { weekday: "short", day: "numeric", month: "numeric" }).format(parseISO(date));
  return parts.replace(/[.,]+\s/, " ");
}
