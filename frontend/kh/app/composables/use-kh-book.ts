// KH: what the book pages need from the server (D43): the cookbook's recipes in full with their flags and print
// settings, a single recipe for the card, and the automatic saving of the settings a second after the last change.
import { onScopeDispose, ref, watch, type Ref } from "vue";
import { KhBooksApi, type KhBookSettings, type KhRecipeFlags } from "../lib/api/books";
import { BOOK_AUTOSAVE_MS, defaultBookSettings, fillDefaults, withRecipe, withoutRecipesOutside } from "../lib/book";
import { useRequests } from "~/composables/api/api-client";
import { useUserApi } from "~/composables/api";
import type { ReadCookBook } from "~/lib/api/types/cookbook";
import type { Recipe } from "~/lib/api/types/recipe";

export type BookSaveStatus = "idle" | "saving" | "saved" | "forbidden" | "error";

/** How many full recipes are fetched at once, so a big cookbook does not open hundreds of requests together. */
const FETCH_AT_ONCE = 6;

/** Saves SETTINGS of the cookbook COOKBOOKID BOOK_AUTOSAVE_MS after the last change (only if ENABLED), one save at a
 * time (a change during a save is saved right after it, the latest state wins), and a pending change when the page is
 * left. STATUS says how the last save went; RETRY saves again at once. */
export function useBookSaving(cookbookId: string, settings: Ref<KhBookSettings>, enabled: boolean) {
  const api = new KhBooksApi(useRequests());
  const status = ref<BookSaveStatus>("idle");
  let running = false;
  let dirty = false;
  let timer: ReturnType<typeof setTimeout> | undefined;

  async function save() {
    dirty = true;
    if (running) return;
    running = true;
    while (dirty) {
      dirty = false;
      status.value = "saving";
      const { error } = await api.putPrint(cookbookId, settings.value);
      status.value = !error ? "saved" : error.response?.status === 403 ? "forbidden" : "error";
    }
    running = false;
  }

  if (enabled) {
    watch(settings, () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        timer = undefined;
        void save();
      }, BOOK_AUTOSAVE_MS);
    }, { deep: true });
    onScopeDispose(() => {
      if (timer) {
        clearTimeout(timer);
        void save();
      }
    });
  }
  return { status, retry: save };
}

/** The recipes with SLUGS in full (ingredients and steps), a few at a time; FAILED counts those that cannot be read
 * (left out of RECIPES), so the caller can say the book is incomplete. */
async function fullRecipes(slugs: string[]): Promise<{ recipes: Recipe[]; failed: number }> {
  const api = useUserApi();
  const recipes: Recipe[] = [];
  for (let from = 0; from < slugs.length; from += FETCH_AT_ONCE) {
    const answers = await Promise.all(slugs.slice(from, from + FETCH_AT_ONCE).map(slug => api.recipes.getOne(slug)));
    for (const { data } of answers) if (data) recipes.push(data);
  }
  return { recipes, failed: slugs.length - recipes.length };
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
 * cookbook for this user, "error" if the stored settings cannot be read (the defaults must never be saved over them).
 * CANSAVE: the cookbook belongs to the user's own household. FAILEDRECIPES: how many recipes could not be read. When
 * all were read, settings of recipes no longer in the cookbook are dropped, so a recipe added again starts fresh. */
export async function loadCookbookBook(cookbookSlug: string, userHouseholdId: string | undefined): Promise<(KhBookData & { cookbook: ReadCookBook; canSave: boolean; failedRecipes: number }) | "error" | null> {
  const api = useUserApi();
  const books = new KhBooksApi(useRequests());
  const { data: cookbook } = await api.cookbooks.getOne(cookbookSlug);
  if (!cookbook) return null;
  const list = (await api.recipes.getAll(1, -1, { cookbook: cookbookSlug, orderBy: "name", orderDirection: "asc" })).data?.items ?? [];
  const slugs = list.map(recipe => recipe.slug).filter((slug): slug is string => !!slug);
  const { recipes, failed } = await fullRecipes(slugs);
  const [flags, stored, household] = await Promise.all([
    recipes.length ? books.getFlags(recipes.map(recipe => recipe.slug ?? "")) : { data: {} },
    books.getPrint(cookbook.id),
    householdName(),
  ]);
  if (!stored.data) return "error";
  const year = new Date().getFullYear();
  const filled = fillDefaults(stored.data, cookbook.name, household, year);
  const settings = failed ? filled : withoutRecipesOutside(filled, slugs);
  return { cookbook, recipes, flags: flags.data ?? {}, settings, canSave: cookbook.householdId === userHouseholdId, failedRecipes: failed };
}

/** One recipe for the card: no title page, no table of contents, the servings SERVINGS (null: the recipe's own). */
export async function loadRecipeCard(slug: string, servings: number | null): Promise<KhBookData | null> {
  const books = new KhBooksApi(useRequests());
  const [recipe] = (await fullRecipes([slug])).recipes;
  if (!recipe) return null;
  const base = { ...defaultBookSettings(recipe.name ?? "", "", new Date().getFullYear()), titlePage: false, toc: false };
  const settings = servings && servings > 0 ? withRecipe(base, slug, { servings }) : base;
  return { recipes: [recipe], flags: (await books.getFlags([slug])).data ?? {}, settings };
}
