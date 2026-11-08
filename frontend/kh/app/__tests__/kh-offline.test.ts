// KH: tests for the offline recipes (D42): which addresses are saved, the limits, and the cleanup at sign-out.
import { afterEach, describe, expect, test, vi } from "vitest";
import { clearOfflineCaches, OFFLINE, offlineCaching } from "../lib/offline";

const ORIGIN = "https://kueche.example";
const rules = offlineCaching();
const [recipeRule, imageRule] = rules as [(typeof rules)[number], (typeof rules)[number]];
const matches = (rule: (typeof rules)[number], path: string) => (rule.urlPattern as RegExp).test(ORIGIN + path);

afterEach(() => vi.unstubAllGlobals());

describe("offlineCaching", () => {
  test("saves one recipe and its amounts, not the list or other parts of a recipe", () => {
    expect(matches(recipeRule, "/api/recipes/pfannkuchen")).toBe(true);
    expect(matches(recipeRule, "/api/kh/amounts/abc")).toBe(true);
    expect(matches(recipeRule, "/api/recipes")).toBe(false);
    expect(matches(recipeRule, "/api/recipes/x/comments")).toBe(false);
  });

  test("saves recipe photos", () => {
    expect(matches(imageRule, "/api/media/recipes/1/images/original.webp")).toBe(true);
    expect(matches(imageRule, "/api/media/users/1/profile.webp")).toBe(false);
    expect(matches(imageRule, "/api/media/recipes/1/assets/file.pdf")).toBe(false);
  });

  test("uses the strategies, caches and limits, status 200 only", () => {
    expect(recipeRule).toMatchObject({
      handler: "NetworkFirst",
      options: { cacheName: "kh-recipes", expiration: { maxEntries: 30 }, cacheableResponse: { statuses: [200] } },
    });
    expect(imageRule).toMatchObject({
      handler: "CacheFirst",
      options: {
        cacheName: "kh-recipe-images",
        expiration: { maxEntries: 150, maxAgeSeconds: 30 * 24 * 3600 },
        cacheableResponse: { statuses: [200] },
      },
    });
  });
});

describe("clearOfflineCaches", () => {
  test("deletes both caches", async () => {
    const remove = vi.fn().mockResolvedValue(true);
    vi.stubGlobal("caches", { delete: remove });
    await clearOfflineCaches();
    expect(remove.mock.calls.map(c => c[0]).sort()).toEqual([OFFLINE.images.name, OFFLINE.recipes.name].sort());
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
