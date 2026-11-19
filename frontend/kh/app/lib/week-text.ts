// KH: the planned week as plain text for a message (D73): one line per day with entries, e.g. "Mo 24.11.: Lasagne".
import { dayLabel } from "./week-days";

export interface WeekTextDay {
  date: Date;
  meals: { title?: string | null; recipe?: { name: string } | null }[];
}

/** TITLE, a line per day that has entries (several joined with " · ", days without entries left out) and ORIGIN, the
 * site address, as the footer. Entries without a name (notes without title) are skipped. */
export function weekText(days: WeekTextDay[], title: string, origin: string, locale: string): string {
  const lines = days
    .map(day => ({ date: day.date, names: day.meals.map(meal => meal.recipe?.name || meal.title || "").filter(Boolean) }))
    .filter(day => day.names.length)
    .map(day => `${dayLabel(day.date, locale, true)}: ${day.names.join(" · ")}`);
  return lines.length ? [title, "", ...lines, "", origin].join("\n") : "";
}
