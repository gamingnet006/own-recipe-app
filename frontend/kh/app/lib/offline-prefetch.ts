// KH: filling the offline cache in the background: which of the household's recipes still need loading (new or
// changed since the last time), how they are loaded without flooding a weak connection, and the weeks to fill.
import { addDays, format, startOfWeek, type Day } from "date-fns";

/** The parts of a recipe summary the check needs. */
export interface PrefetchRecipe {
  id: string;
  slug: string;
  image?: string | null;
  updatedAt?: string | null;
  dateUpdated?: string | null;
}

/** What was loaded when: recipe slug to its stamp. */
export type Known = Record<string, string>;

/** How many recipes load at the same time. */
export const PREFETCH_CONCURRENCY = 3;

/** Changes whenever the recipe or its photo changes. */
export const stampOf = (recipe: PrefetchRecipe): string => `${recipe.updatedAt ?? recipe.dateUpdated ?? ""}|${recipe.image ?? ""}`;

/** The recipes of LIST that are new or changed since KNOWN. */
export function staleRecipes(list: PrefetchRecipe[], known: Known): PrefetchRecipe[] {
  return list.filter(recipe => known[recipe.slug] !== stampOf(recipe));
}

/**
 * Loads the stale recipes with LOAD (which answers whether it worked) a few at a time and stops starting new ones when
 * STOP says so (the server went away). A recipe that is known but whose saved copy CACHED no longer finds (the browser
 * dropped it) counts as stale too. Returns the new KNOWN: recipes no longer in LIST are forgotten, failed ones are left
 * out so the next run tries them again.
 */
export async function syncRecipes(
  list: PrefetchRecipe[],
  known: Known,
  load: (recipe: PrefetchRecipe) => Promise<boolean>,
  stop: () => boolean,
  cached: (recipe: PrefetchRecipe) => Promise<boolean>,
): Promise<Known> {
  const next: Known = Object.fromEntries(list.filter(recipe => recipe.slug in known).map(recipe => [recipe.slug, known[recipe.slug] as string]));
  const fresh = list.filter(recipe => known[recipe.slug] === stampOf(recipe));
  const dropped = (await Promise.all(fresh.map(async recipe => ((await cached(recipe)) ? null : recipe)))).filter(recipe => recipe !== null);
  const queue = [...staleRecipes(list, known), ...dropped];
  const worker = async () => {
    for (let recipe = queue.shift(); recipe && !stop(); recipe = queue.shift()) {
      if (await load(recipe)) next[recipe.slug] = stampOf(recipe);
    }
  };
  await Promise.all(Array.from({ length: PREFETCH_CONCURRENCY }, worker));
  return next;
}

/** This week and the next as the planner asks for them (`yyyy-MM-dd`), the weeks starting on FIRST_DAY (0 = Sunday). */
export function weekRanges(today: Date, firstDay: number): { start: string; end: string }[] {
  const monday = startOfWeek(today, { weekStartsOn: firstDay as Day });
  return [0, 7].map(offset => ({
    start: format(addDays(monday, offset), "yyyy-MM-dd"),
    end: format(addDays(monday, offset + 6), "yyyy-MM-dd"),
  }));
}
