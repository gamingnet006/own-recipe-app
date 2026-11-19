// KH: offline recipes (D42): the Workbox caching rules for the last recipes and their photos, and the cleanup that
// removes them (and the offline shopping lists, D63) again when someone signs out (a shared device keeps no recipes).
import type { ModuleOptions } from "@vite-pwa/nuxt";
import { clearStored } from "./shopping-offline";

type RuntimeCaching = NonNullable<NonNullable<ModuleOptions["workbox"]>["runtimeCaching"]>[number];

const DAY_SECONDS = 24 * 3600;

/** The caches and their limits: the last 30 recipes, 150 photos for 30 days; a recipe waits 4 s for the network
 * before the saved copy answers, so weak Wi-Fi does not leave the page empty. */
export const OFFLINE = {
  recipes: { name: "kh-recipes", maxEntries: 30, networkTimeoutSeconds: 4 },
  images: { name: "kh-recipe-images", maxEntries: 150, maxAgeSeconds: 30 * DAY_SECONDS },
};

/** The caching rules for Mealie's service worker. Workbox tests a RegExp against the whole address and writes the
 * rules into the service worker file, so they are unanchored RegExp values that use no variable of this file. Only
 * GET (Workbox's default) and status 200 are stored. */
export function offlineCaching(): RuntimeCaching[] {
  return [
    {
      // One recipe and its amounts, and the signed-in user (D63: without it a cold start with no network has no user, so
      // the shopping page could not open its stored lists): the network wins, the saved copy answers when there is none.
      urlPattern: /\/api\/(?:recipes\/[^/?]+|kh\/amounts\/.*|users\/self)$/,
      handler: "NetworkFirst",
      options: {
        cacheName: OFFLINE.recipes.name,
        networkTimeoutSeconds: OFFLINE.recipes.networkTimeoutSeconds,
        expiration: { maxEntries: OFFLINE.recipes.maxEntries },
        cacheableResponse: { statuses: [200] },
      },
    },
    {
      // A photo never changes under its address, so the saved one is used first.
      urlPattern: /\/api\/media\/recipes\/[^/]+\/images\//,
      handler: "CacheFirst",
      options: {
        cacheName: OFFLINE.images.name,
        expiration: { maxEntries: OFFLINE.images.maxEntries, maxAgeSeconds: OFFLINE.images.maxAgeSeconds },
        cacheableResponse: { statuses: [200] },
      },
    },
  ];
}

/** Deletes both offline caches and what the shopping page kept for offline use (D63); does nothing more where the
 * browser has no cache storage. A failure is only logged, so it can never stop a sign-out. */
export async function clearOfflineCaches(): Promise<void> {
  clearStored();
  if (typeof caches === "undefined") return;
  try {
    await Promise.all([caches.delete(OFFLINE.recipes.name), caches.delete(OFFLINE.images.name)]);
  }
  catch (error) {
    console.warn("Could not clear the offline recipes:", error);
  }
}
