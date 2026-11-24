// KH: tests for the offline recipes (D42): which addresses are saved, the limits, and the cleanup at sign-out.
import { afterEach, describe, expect, test, vi } from "vitest";
import { clearOfflineCaches, OFFLINE, offlineCaching } from "../lib/offline";

const ORIGIN = "https://kueche.example";
const rules = offlineCaching();
const [recipeRule, pagesRule, imageRule, sessionRule] = rules as [(typeof rules)[number], (typeof rules)[number], (typeof rules)[number], (typeof rules)[number]];
const matches = (rule: (typeof rules)[number], path: string) => (rule.urlPattern as RegExp).test(ORIGIN + path);

afterEach(() => vi.unstubAllGlobals());

describe("offlineCaching", () => {
  test("saves one recipe and its amounts, not the list or other parts of a recipe", () => {
    expect(matches(recipeRule, "/api/recipes/pfannkuchen")).toBe(true);
    expect(matches(recipeRule, "/api/kh/amounts/abc")).toBe(true);
    expect(matches(recipeRule, "/api/recipes")).toBe(false);
    expect(matches(recipeRule, "/api/recipes/x/comments")).toBe(false);
  });

  test("saves the signed-in user in a cache of its own, so that a start without network still has one (D63) and the recipes can never push it out", () => {
    expect(matches(sessionRule, "/api/users/self")).toBe(true);
    expect(matches(sessionRule, "/api/users/self/favorites")).toBe(false);
    expect(matches(sessionRule, "/api/users/abc")).toBe(false);
    expect(matches(recipeRule, "/api/users/self")).toBe(false);
    expect(sessionRule).toMatchObject({ handler: "NetworkFirst", options: { cacheName: "kh-session" } });
    expect(OFFLINE.session.name).not.toBe(OFFLINE.recipes.name);
  });

  test("saves only the one main photo of a recipe, in the small size", () => {
    expect(matches(imageRule, "/api/media/recipes/1/images/min-original.webp?rnd=1&version=2")).toBe(true);
    expect(matches(imageRule, "/api/media/recipes/1/images/original.webp")).toBe(false); // too big for a phone cache
    expect(matches(imageRule, "/api/media/recipes/1/images/timeline/9/min-original.webp")).toBe(false); // extra photos
    expect(matches(imageRule, "/api/media/users/1/profile.webp")).toBe(false);
    expect(matches(imageRule, "/api/media/recipes/1/assets/file.pdf")).toBe(false);
  });

  test("saves the lists the pages read: recipe lists, the meal plan and the wishes, but not writes' addresses", () => {
    expect(matches(pagesRule, "/api/recipes?page=1&perPage=30")).toBe(true);
    expect(matches(pagesRule, "/api/households/mealplans?start_date=2026-11-23&end_date=2026-11-29")).toBe(true);
    expect(matches(pagesRule, "/api/kh/wishes")).toBe(true);
    expect(matches(pagesRule, "/api/kh/wishes/abc/plan")).toBe(false);
    expect(matches(pagesRule, "/api/households/mealplans/random")).toBe(false);
  });

  test("uses the strategies, caches and limits, status 200 only", () => {
    expect(recipeRule).toMatchObject({
      handler: "NetworkFirst",
      options: {
        cacheName: "kh-recipes",
        networkTimeoutSeconds: 4, // weak kitchen Wi-Fi: the saved copy answers after 4 s (v1.1)
        expiration: { maxEntries: OFFLINE.recipes.maxEntries },
        cacheableResponse: { statuses: [200] },
      },
    });
    expect(pagesRule).toMatchObject({ handler: "NetworkFirst", options: { cacheName: "kh-pages" } });
    expect(imageRule).toMatchObject({
      handler: "CacheFirst",
      options: {
        cacheName: "kh-recipe-images",
        // the oldest photos go first when the cap is reached, and everything goes when the device's storage is full
        expiration: { maxEntries: OFFLINE.images.maxEntries, maxAgeSeconds: 30 * 24 * 3600, purgeOnQuotaError: true },
        cacheableResponse: { statuses: [200] },
      },
    });
  });
});

describe("list cache key", () => {
  const keyOf = async (url: string) => {
    const plugin = (pagesRule.options as { plugins: { cacheKeyWillBeUsed: (arg: { request: Request }) => Promise<string> }[] }).plugins[0]!;
    return plugin.cacheKeyWillBeUsed({ request: new Request(ORIGIN + url) });
  };

  test("the start page's list is found again although its random seed changes and its empty filters differ", async () => {
    const first = await keyOf("/api/recipes?page=1&perPage=32&orderBy=created_at&search=&requireAllTags=false&paginationSeed=111&searchSeed=111");
    const second = await keyOf("/api/recipes?orderBy=created_at&perPage=32&page=1&paginationSeed=222&tags=");
    expect(first).toBe(second);
  });

  test("real differences stay different", async () => {
    expect(await keyOf("/api/recipes?page=1&perPage=32")).not.toBe(await keyOf("/api/recipes?page=2&perPage=32"));
    expect(await keyOf("/api/recipes?search=cake")).not.toBe(await keyOf("/api/recipes?search="));
  });
});

describe("clearOfflineCaches", () => {
  test("the caches hold every recipe of a big household (two entries each) without evicting on the first fill", () => {
    expect(OFFLINE.recipes.maxEntries).toBe(2000);
    expect(OFFLINE.images.maxEntries).toBe(1000);
  });

  test("deletes all caches", async () => {
    const remove = vi.fn().mockResolvedValue(true);
    vi.stubGlobal("caches", { delete: remove });
    await clearOfflineCaches();
    expect(remove.mock.calls.map(c => c[0]).sort()).toEqual([OFFLINE.images.name, OFFLINE.pages.name, OFFLINE.recipes.name, OFFLINE.session.name].sort());
  });

  test("a failing cache cannot stop the sign-out", async () => {
    vi.stubGlobal("caches", { delete: vi.fn().mockRejectedValue(new Error("no")) });
    vi.spyOn(console, "warn").mockImplementation(() => {});
    await expect(clearOfflineCaches()).resolves.toBeUndefined();
  });

  test("does nothing without cache storage", async () => {
    vi.stubGlobal("caches", undefined);
    await expect(clearOfflineCaches()).resolves.toBeUndefined();
  });
});
