// KH: offline recipes (D42): the Workbox caching rules for the last recipes and their photos, and the cleanup that
// removes them again when someone signs out (a shared device keeps no recipes).
import type { ModuleOptions } from "@vite-pwa/nuxt";

type RuntimeCaching = NonNullable<NonNullable<ModuleOptions["workbox"]>["runtimeCaching"]>[number];

const DAY_SECONDS = 24 * 3600;

/** The caches and their limits: the last 30 recipes, 150 photos for 30 days. */
export const OFFLINE = {
  recipes: { name: "kh-recipes", maxEntries: 30 },
  images: { name: "kh-recipe-images", maxEntries: 150, maxAgeSeconds: 30 * DAY_SECONDS },
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
        expiration: { maxEntries: OFFLINE.recipes.maxEntries },
        cacheableResponse: { statuses: [200] },
      },
    },
    {
      // A photo never changes under its address, so the saved one is used first.
      urlPattern: /\/api\/media\/recipes\//,
      handler: "CacheFirst",
      options: {
        cacheName: OFFLINE.images.name,
        expiration: { maxEntries: OFFLINE.images.maxEntries, maxAgeSeconds: OFFLINE.images.maxAgeSeconds },
        cacheableResponse: { statuses: [200] },
      },
    },
  ];
}

/** Deletes both offline caches; does nothing where the browser has no cache storage. */
export async function clearOfflineCaches(): Promise<void> {
  if (typeof caches === "undefined") return;
  await Promise.all([caches.delete(OFFLINE.recipes.name), caches.delete(OFFLINE.images.name)]);
}
