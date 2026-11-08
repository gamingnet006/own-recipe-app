// KH: what the book pages need from the server (D43): the cookbook's recipes in full with their flags and print
// settings, a single recipe for the card, and the automatic saving of the settings a second after the last change.
import { watchDebounced } from "@vueuse/core";
import { ref, type Ref } from "vue";
import { KhBooksApi, type KhBookSettings, type KhRecipeFlags } from "../lib/api/books";
import { BOOK_AUTOSAVE_MS, defaultBookSettings, fillDefaults, withRecipe } from "../lib/book";
import { useRequests } from "~/composables/api/api-client";
import { useUserApi } from "~/composables/api";
import type { ReadCookBook } from "~/lib/api/types/cookbook";
import type { Recipe } from "~/lib/api/types/recipe";

export type BookSaveStatus = "idle" | "saving" | "saved" | "forbidden" | "error";

/** How many full recipes are fetched at once, so a big cookbook does not open hundreds of requests together. */
const FETCH_AT_ONCE = 6;

/** Saves SETTINGS of the cookbook COOKBOOKID BOOK_AUTOSAVE_MS after the last change (only if ENABLED). STATUS says how
 * the last save went; RETRY saves again at once. */
export function useBookSaving(cookbookId: string, settings: Ref<KhBookSettings>, enabled: boolean) {
  const api = new KhBooksApi(useRequests());
  const status = ref<BookSaveStatus>("idle");

  async function save() {
    status.value = "saving";
    const { error } = await api.putPrint(cookbookId, settings.value);
    status.value = !error ? "saved" : error.response?.status === 403 ? "forbidden" : "error";
  }

  if (enabled) watchDebounced(settings, save, { deep: true, debounce: BOOK_AUTOSAVE_MS });
  return { status, retry: save };
}

/** The recipes with SLUGS in full (ingredients and steps), a few at a time; one that cannot be read is left out. */
async function fullRecipes(slugs: string[]): Promise<Recipe[]> {
  const api = useUserApi();
  const found: Recipe[] = [];
  for (let from = 0; from < slugs.length; from += FETCH_AT_ONCE) {
    const answers = await Promise.all(slugs.slice(from, from + FETCH_AT_ONCE).map(slug => api.recipes.getOne(slug)));
    for (const { data } of answers) if (data) found.push(data);
  }
  return found;
}

/** The household's name for the default subtitle. */
async function householdName(): Promise<string> {
  return (await useUserApi().households.getCurrentUserHousehold()).data?.name ?? "";
}

export interface KhBookData {
  recipes: Recipe[];
  flags: Record<string, KhRecipeFlags>;
  settings: KhBookSettings;
}

/** The cookbook with the slug COOKBOOKSLUG, its recipes in full and its print settings; null if there is no such
 * cookbook for this user. CANSAVE: the cookbook belongs to the user's own household. */
export async function loadCookbookBook(cookbookSlug: string, userHouseholdId: string | undefined): Promise<(KhBookData & { cookbook: ReadCookBook; canSave: boolean }) | null> {
  const api = useUserApi();
  const books = new KhBooksApi(useRequests());
  const { data: cookbook } = await api.cookbooks.getOne(cookbookSlug);
  if (!cookbook) return null;
  const list = (await api.recipes.getAll(1, -1, { cookbook: cookbookSlug, orderBy: "name", orderDirection: "asc" })).data?.items ?? [];
  const recipes = await fullRecipes(list.map(recipe => recipe.slug).filter((slug): slug is string => !!slug));
  const [flags, stored, household] = await Promise.all([
    recipes.length ? books.getFlags(recipes.map(recipe => recipe.slug ?? "")) : { data: {} },
    books.getPrint(cookbook.id),
    householdName(),
  ]);
  const year = new Date().getFullYear();
  const settings = fillDefaults(stored.data ?? defaultBookSettings(cookbook.name, household, year), cookbook.name, household, year);
  return { cookbook, recipes, flags: flags.data ?? {}, settings, canSave: cookbook.householdId === userHouseholdId };
}

/** One recipe for the card: no title page, no table of contents, the servings SERVINGS (null: the recipe's own). */
export async function loadRecipeCard(slug: string, servings: number | null): Promise<KhBookData | null> {
  const books = new KhBooksApi(useRequests());
  const [recipe] = await fullRecipes([slug]);
  if (!recipe) return null;
  const base = { ...defaultBookSettings(recipe.name ?? "", "", new Date().getFullYear()), titlePage: false, toc: false };
  const settings = servings && servings > 0 ? withRecipe(base, slug, { servings }) : base;
  return { recipes: [recipe], flags: (await books.getFlags([slug])).data ?? {}, settings };
}
