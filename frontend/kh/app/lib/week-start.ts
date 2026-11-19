// KH: the first day of the planner's week (D76). Mealie stores 0 (Sunday) for every household that never chose one, which
// is wrong in German-speaking homes, so there the default is Monday.

/** The weekday the week starts with (0 = Sunday, 1 = Monday): the household's choice, else the language's habit. */
export function firstDayOfWeek(chosen: number | null | undefined, locale: string): number {
  // ponytail: 0 cannot be told from "never chosen", so a German household cannot pick Sunday; store null by default if it matters
  return chosen || (locale.startsWith("de") ? 1 : 0);
}
