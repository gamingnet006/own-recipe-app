// KH: short day names for the planner's chips and the shared week text (D72, D73): "Mo 24." and "Mo 24.11.".
import { format, isBefore, startOfDay } from "date-fns";

/** The day as "Mo 24." (or "Mo 24.11." with MONTH); the weekday follows LOCALE, the order of day and month is German. */
export function dayLabel(date: Date, locale: string, month = false): string {
  const weekday = new Intl.DateTimeFormat(locale, { weekday: "short" }).format(date).replace(/\.$/, "");
  return `${weekday} ${format(date, month ? "dd.MM." : "d.")}`;
}

/** The days from TODAY on as chips: yyyy-MM-dd and a short label each. */
export function dayChips(days: Date[], locale: string, today: Date = new Date()): { date: string; label: string }[] {
  return days
    .filter(day => !isBefore(day, startOfDay(today)))
    .map(day => ({ date: format(day, "yyyy-MM-dd"), label: dayLabel(day, locale) }));
}
