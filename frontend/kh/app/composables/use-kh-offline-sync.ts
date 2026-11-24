// KH: fills the offline cache in the background: after sign-in and whenever the server is back, the household's recipes
// (text, amounts, the one small main photo) that are new or changed are loaded once, so they open without a network.
import { KhAmountsApi } from "../lib/api/amounts";
import { KhWishesApi } from "../lib/api/wishes";
import { syncRecipes, weekRanges, type Known, type PrefetchRecipe } from "../lib/offline-prefetch";
import { firstDayOfWeek } from "../lib/week-start";
import { readStored, writeStored } from "../lib/shopping-offline";
import { khAddons } from "./use-kh-addons";
import { onKhReconnect, useKhOnline } from "./use-kh-connection";
import { useRequests, useUserApi } from "~/composables/api/api-client";
import { useStaticRoutes } from "~/composables/api";
import { useHouseholdSelf } from "~/composables/use-households";

const KNOWN = "recipes-known";
const START_DELAY_MS = 3000; // let the page the person opened load first

/** Starts the background fill for the signed-in user; call it once from the layout. */
export function useKhOfflineSync(): void {
  const auth = useMealieAuth();
  const online = useKhOnline();
  const api = useUserApi();
  const amounts = new KhAmountsApi(useRequests());
  const wishes = new KhWishesApi(useRequests());
  const { recipeSmallImage } = useStaticRoutes();
  const { household } = useHouseholdSelf();
  const i18n = useI18n();
  let running = false;

  /** Whether the saved copy of the recipe (its text, amounts and photo) is still in the browser's caches. */
  async function cached(recipe: PrefetchRecipe): Promise<boolean> {
    if (typeof caches === "undefined") return true; // nothing to check where there is no cache storage
    const urls = [api.recipes.itemRoute(recipe.slug), `/api/kh/amounts/${recipe.id}`];
    if (recipe.image) urls.push(recipeSmallImage(recipe.id, recipe.image));
    return (await Promise.all(urls.map(url => caches.match(url)))).every(Boolean);
  }

  /** Loads one recipe, its amounts and its photo through the service worker, which keeps them. */
  async function load(recipe: PrefetchRecipe): Promise<boolean> {
    const [detail, extra] = await Promise.all([api.recipes.getOne(recipe.slug), amounts.get(recipe.id)]);
    if (recipe.image) await fetch(recipeSmallImage(recipe.id, recipe.image)).catch(() => null);
    return !!detail.data && !!extra.data;
  }

  /** Loads what the start page, the planner and the wish list open with, so that their first look works offline too. */
  async function loadLists() {
    const first = firstDayOfWeek(household.value?.preferences?.firstDayOfWeek, i18n.locale.value);
    // the start page's default view: newest first, 32 recipes, and the double call it makes on its first load
    const list = (perPage: number) => api.recipes.getAll(1, perPage, { orderBy: "created_at", orderDirection: "desc", orderByNullPosition: "last" });
    const weeks = weekRanges(new Date(), first).map(({ start, end }) =>
      api.mealplans.getAll(1, -1, { start_date: start, end_date: end, include_week_entries: true }));
    await Promise.all([list(32), list(64), wishes.list(), ...weeks]);
  }

  async function run() {
    const userId = auth.user.value?.id;
    // the add-ons are loaded for this user first, so that "offline" switched off by the household is respected
    if (running || !userId || khAddons.userId !== userId || !khAddons.enabled.offline || !online.value) return;
    running = true;
    try {
      const { data } = await api.recipes.getAll(1, -1);
      if (!data) return;
      const known = await syncRecipes(data.items, readStored<Known>(userId, KNOWN, {}), load, () => !online.value, cached);
      writeStored(userId, KNOWN, known);
      await loadLists();
    }
    finally {
      running = false;
    }
  }

  const start = () => setTimeout(() => void run(), START_DELAY_MS);
  onKhReconnect(start);
  watch(() => [auth.user.value?.id, khAddons.userId, khAddons.enabled.offline], start, { immediate: true });
}
