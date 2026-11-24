// KH: offline recipes (D42): the Workbox caching rules for the recipes, their lists and photos, and the cleanup that
// removes them (and the offline shopping lists, D63) again when someone signs out (a shared device keeps no recipes).
import type { ModuleOptions } from "@vite-pwa/nuxt";
import { clearStored } from "./shopping-offline";

type RuntimeCaching = NonNullable<NonNullable<ModuleOptions["workbox"]>["runtimeCaching"]>[number];

const DAY_SECONDS = 24 * 3600;

/** The caches and their limits. session: the signed-in user, alone so that no recipe can push it out; recipes: a
 * household's recipes with their amounts, two entries of a few KB each, so 2000 entries serve 1000 recipes; pages: the
 * lists the pages read (recipe lists, meal plan, wishes); images: only each recipe's main photo in the small size, small
 * webp of about 30 to 60 KB, so 1000 of them stay near 30 to 60 MB, and the oldest go first. A recipe waits 4 s for the network before the
 * saved copy answers, so weak Wi-Fi does not leave the page empty. */
export const OFFLINE = {
  session: { name: "kh-session", maxEntries: 3 },
  recipes: { name: "kh-recipes", maxEntries: 2000, networkTimeoutSeconds: 4 },
  pages: { name: "kh-pages", maxEntries: 60 },
  images: { name: "kh-recipe-images", maxEntries: 1000, maxAgeSeconds: 30 * DAY_SECONDS },
};

/** Gives list requests one address in the cache: the random seeds, empty filters and "false" switches the recipe lists
 * add on every call are left out and the rest is sorted, so the start page's list is found again offline. An arrow
 * function with no outside names, because Workbox writes it into the service worker file as text. */
const listKeyPlugin = {
  cacheKeyWillBeUsed: async ({ request }: { request: Request }) => {
    const url = new URL(request.url);
    ["paginationSeed", "searchSeed"].forEach(name => url.searchParams.delete(name));
    [...url.searchParams].forEach(([name, value]) => {
      if (value === "" || value === "false") url.searchParams.delete(name);
    });
    url.searchParams.sort();
    return url.href;
  },
};

/** The caching rules for Mealie's service worker. Workbox tests a RegExp against the whole address and writes the
 * rules into the service worker file, so they are unanchored RegExp values that use no variable of this file. Only
 * GET (Workbox's default) and status 200 are stored. */
export function offlineCaching(): RuntimeCaching[] {
  return [
    {
      // One recipe and its amounts: the network wins, the saved copy answers when there is none.
      urlPattern: /\/api\/(?:recipes\/[^/?]+|kh\/amounts\/.*)$/,
      handler: "NetworkFirst",
      options: {
        cacheName: OFFLINE.recipes.name,
        networkTimeoutSeconds: OFFLINE.recipes.networkTimeoutSeconds,
        expiration: { maxEntries: OFFLINE.recipes.maxEntries },
        cacheableResponse: { statuses: [200] },
      },
    },
    {
      // What the list pages, the week and the wish list read; every variant a person opened (filters, weeks) is kept.
      urlPattern: /\/api\/(?:recipes\?|households\/mealplans\?|kh\/wishes$)/,
      handler: "NetworkFirst",
      options: {
        cacheName: OFFLINE.pages.name,
        networkTimeoutSeconds: OFFLINE.recipes.networkTimeoutSeconds,
        expiration: { maxEntries: OFFLINE.pages.maxEntries },
        plugins: [listKeyPlugin],
        cacheableResponse: { statuses: [200] },
      },
    },
    {
      // Only the recipe's main photo in the small size (min-original; not the big original, not the timeline's extra
      // photos). A photo never changes under its address (the version is in it), so the saved one is used first.
      urlPattern: /\/api\/media\/recipes\/[^/]+\/images\/min-original\.webp/,
      handler: "CacheFirst",
      options: {
        cacheName: OFFLINE.images.name,
        expiration: { maxEntries: OFFLINE.images.maxEntries, maxAgeSeconds: OFFLINE.images.maxAgeSeconds, purgeOnQuotaError: true },
        cacheableResponse: { statuses: [200] },
      },
    },
    {
      // The signed-in user (D63: without it a cold start with no network has no user, so the shopping page could not open
      // its stored lists), in a cache of its own that the recipes cannot fill up.
      urlPattern: /\/api\/users\/self$/,
      handler: "NetworkFirst",
      options: {
        cacheName: OFFLINE.session.name,
        networkTimeoutSeconds: OFFLINE.recipes.networkTimeoutSeconds,
        expiration: { maxEntries: OFFLINE.session.maxEntries },
        cacheableResponse: { statuses: [200] },
      },
    },
  ];
}

/** Deletes all offline caches and what the shopping page kept for offline use (D63); does nothing more where the
 * browser has no cache storage. A failure is only logged, so it can never stop a sign-out. */
export async function clearOfflineCaches(): Promise<void> {
  clearStored();
  if (typeof caches === "undefined") return;
  try {
    await Promise.all(Object.values(OFFLINE).map(cache => caches.delete(cache.name)));
  }
  catch (error) {
    console.warn("Could not clear the offline recipes:", error);
  }
}
