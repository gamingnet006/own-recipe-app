// KH: the family cookbook's pure logic (D43): default settings, which recipes go into a book, in what order and
// with which number, photo and servings, and what the editor shows. No Vue, no requests.
import type { KhBookRecipeSettings, KhBookSettings, KhRecipeFlags } from "./api/books";
import type { Recipe } from "~/lib/api/types/recipe";

/** How long after the last change the editor saves the settings. */
export const BOOK_AUTOSAVE_MS = 1000;

/** One recipe as it appears in the book. */
export interface BookEntry {
  number: number;
  recipe: Recipe;
  photo: boolean;
  servings: number;
}

/** The settings of a cookbook nobody has printed yet: its name as title, "<household> · <year>" as subtitle. */
export function defaultBookSettings(cookbookName: string, householdName: string, year: number): KhBookSettings {
  return {
    title: cookbookName,
    subtitle: `${householdName} · ${year}`,
    titlePage: true,
    toc: true,
    order: "category",
    description: true,
    notes: true,
    oven: true,
    recipes: {},
  };
}

/** What SETTINGS say about the recipe SLUG; a recipe they never mention is in, without photo, at its own servings. */
export function recipeSettings(settings: KhBookSettings, slug: string): KhBookRecipeSettings {
  return settings.recipes[slug] ?? { include: true, photo: false, servings: null };
}

const collator = new Intl.Collator("de");
const firstCategory = (recipe: Recipe) => recipe.recipeCategory?.[0]?.name ?? null;

/** Compares by first category (recipes without one last), then by title, in German order. */
function byCategoryThenTitle(a: Recipe, b: Recipe): number {
  const [ca, cb] = [firstCategory(a), firstCategory(b)];
  if (ca !== cb) {
    if (ca === null) return 1;
    if (cb === null) return -1;
    return collator.compare(ca, cb);
  }
  return collator.compare(a.name ?? "", b.name ?? "");
}

/** The entries of the book, numbered from 1. Settings for recipes that are no longer in RECIPES are ignored;
 * a photo needs the setting, the own-photo flag and an image. */
export function bookRecipes(recipes: Recipe[], settings: KhBookSettings, flags: Record<string, KhRecipeFlags>): BookEntry[] {
  const included = recipes.filter(recipe => recipeSettings(settings, recipe.slug ?? "").include);
  const compare = settings.order === "alpha" ? (a: Recipe, b: Recipe) => collator.compare(a.name ?? "", b.name ?? "") : byCategoryThenTitle;
  return [...included].sort(compare).map((recipe, index) => {
    const own = recipeSettings(settings, recipe.slug ?? "");
    return {
      number: index + 1,
      recipe,
      photo: own.photo && !!flags[recipe.slug ?? ""]?.ownPhoto && !!recipe.image,
      servings: own.servings ?? recipe.recipeServings ?? 0,
    };
  });
}

/** What the editor shows: the hint for a cookbook whose filter finds no recipes, else the entries. */
export function editorState(recipes: Recipe[], settings: KhBookSettings, flags: Record<string, KhRecipeFlags>): { empty: boolean; entries: BookEntry[] } {
  return recipes.length === 0 ? { empty: true, entries: [] } : { empty: false, entries: bookRecipes(recipes, settings, flags) };
}

/** Stored settings where the title or subtitle was never set get the defaults for them; the rest stays as stored. */
export function fillDefaults(stored: KhBookSettings, cookbookName: string, householdName: string, year: number): KhBookSettings {
  const defaults = defaultBookSettings(cookbookName, householdName, year);
  return { ...stored, title: stored.title ?? defaults.title, subtitle: stored.subtitle ?? defaults.subtitle };
}

/** SETTINGS with PATCH applied to the recipe SLUG only (a new object, so a v-model sees the change). */
export function withRecipe(settings: KhBookSettings, slug: string, patch: Partial<KhBookRecipeSettings>): KhBookSettings {
  return { ...settings, recipes: { ...settings.recipes, [slug]: { ...recipeSettings(settings, slug), ...patch } } };
}
