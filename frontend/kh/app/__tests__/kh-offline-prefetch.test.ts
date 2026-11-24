// KH: tests for the background fill of the offline cache: which recipes are loaded, how many at once, when it stops.
import { describe, expect, test, vi } from "vitest";
import { PREFETCH_CONCURRENCY, staleRecipes, stampOf, syncRecipes, weekRanges, type PrefetchRecipe } from "../lib/offline-prefetch";

const cachedYes = async () => true;
const recipe = (slug: string, updatedAt = "t1", image = "v1"): PrefetchRecipe => ({ id: `id-${slug}`, slug, updatedAt, image });

describe("staleRecipes", () => {
  test("new and changed recipes (also a new photo) are stale, unchanged ones are not", () => {
    const list = [recipe("a"), recipe("b", "t2"), recipe("c", "t1", "v2"), recipe("d")];
    const known = { a: stampOf(recipe("a")), b: stampOf(recipe("b")), c: stampOf(recipe("c")) };
    expect(staleRecipes(list, known).map(r => r.slug)).toEqual(["b", "c", "d"]);
  });
});

describe("syncRecipes", () => {
  test("loads the stale ones, remembers them, forgets recipes that are gone", async () => {
    const load = vi.fn().mockResolvedValue(true);
    const known = await syncRecipes([recipe("a"), recipe("b")], { a: stampOf(recipe("a")), gone: "x" }, load, () => false, cachedYes);
    expect(load.mock.calls.map(c => c[0].slug)).toEqual(["b"]);
    expect(known).toEqual({ a: stampOf(recipe("a")), b: stampOf(recipe("b")) });
  });

  test("a known recipe whose saved copy the browser dropped is loaded again", async () => {
    const load = vi.fn().mockResolvedValue(true);
    const cached = vi.fn(async (r: PrefetchRecipe) => r.slug !== "b");
    const list = [recipe("a"), recipe("b")];
    const known = await syncRecipes(list, { a: stampOf(list[0]!), b: stampOf(list[1]!) }, load, () => false, cached);
    expect(load.mock.calls.map(c => c[0].slug)).toEqual(["b"]);
    expect(Object.keys(known).sort()).toEqual(["a", "b"]);
  });

  test("a recipe that failed to load is tried again next time", async () => {
    const load = vi.fn(async (r: PrefetchRecipe) => r.slug !== "b");
    const known = await syncRecipes([recipe("a"), recipe("b")], {}, load, () => false, cachedYes);
    expect(Object.keys(known)).toEqual(["a"]);
  });

  test("never more than a few at once, so the kitchen's Wi-Fi stays usable", async () => {
    let running = 0;
    let most = 0;
    const load = async () => {
      most = Math.max(most, ++running);
      await new Promise(resolve => setTimeout(resolve, 1));
      running--;
      return true;
    };
    const many = Array.from({ length: 12 }, (_, i) => recipe(`r${i}`));
    await syncRecipes(many, {}, load, () => false, cachedYes);
    expect(most).toBe(PREFETCH_CONCURRENCY);
  });

  test("stops asking for more as soon as the server is gone, and keeps what it has", async () => {
    let gone = false;
    const load = vi.fn(async () => {
      gone = true;
      return true;
    });
    const many = Array.from({ length: 10 }, (_, i) => recipe(`r${i}`));
    const known = await syncRecipes(many, {}, load, () => gone, cachedYes);
    expect(load.mock.calls.length).toBeLessThanOrEqual(PREFETCH_CONCURRENCY);
    expect(Object.keys(known).length).toBe(load.mock.calls.length);
  });
});

describe("weekRanges", () => {
  test("this week and the next, from the household's first weekday, as the planner asks for them", () => {
    const wednesday = new Date(2026, 10, 25);
    expect(weekRanges(wednesday, 1)).toEqual([
      { start: "2026-11-23", end: "2026-11-29" },
      { start: "2026-11-30", end: "2026-12-06" },
    ]);
    expect(weekRanges(wednesday, 0)[0]).toEqual({ start: "2026-11-22", end: "2026-11-28" });
  });
});
