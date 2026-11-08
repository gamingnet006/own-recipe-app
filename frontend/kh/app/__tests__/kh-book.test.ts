// KH: tests for the book's pure logic (D43): which recipes go in, in what order and number, with which photo and
// servings; stale settings; the empty cookbook.
import { describe, expect, test } from "vitest";
import { bookRecipes, defaultBookSettings, recipeSettings } from "../lib/book";
import type { KhBookSettings, KhRecipeFlags } from "../lib/api/books";

const recipe = (slug: string, name: string, category?: string, extra: object = {}) =>
  ({ slug, name, recipeCategory: category ? [{ name: category }] : [], recipeServings: 4, image: "x", ...extra }) as never;
const settings = (over: Partial<KhBookSettings> = {}): KhBookSettings => ({ ...defaultBookSettings("Kuchen", "Muster", 2026), ...over });
const names = (entries: { recipe: { name: string } }[]) => entries.map(entry => entry.recipe.name);

describe("defaults", () => {
  test("title is the cookbook's name, subtitle household and year", () => {
    const d = defaultBookSettings("Kuchen", "Muster", 2026);
    expect(d).toMatchObject({ title: "Kuchen", subtitle: "Muster · 2026", titlePage: true, toc: true, order: "category", recipes: {} });
  });
  test("an unknown recipe has the defaults", () => {
    expect(recipeSettings(settings(), "nix")).toEqual({ include: true, photo: false, servings: null });
  });
});

describe("order and numbers", () => {
  const recipes = [
    recipe("t", "Torte", "Kuchen"), recipe("b", "Brot"), recipe("a", "Apfelkuchen", "Kuchen"), recipe("s", "Suppe", "Alltag"),
  ];
  test("by first category then title, without a category last", () => {
    const entries = bookRecipes(recipes, settings(), {});
    expect(names(entries)).toEqual(["Suppe", "Apfelkuchen", "Torte", "Brot"]);
    expect(entries.map(entry => entry.number)).toEqual([1, 2, 3, 4]);
  });
  test("alpha uses German collation: Äpfel before Birnen", () => {
    const entries = bookRecipes([recipe("b", "Birnen"), recipe("a", "Äpfel")], settings({ order: "alpha" }), {});
    expect(names(entries)).toEqual(["Äpfel", "Birnen"]);
  });
  test("excluded recipes are skipped and the numbers stay continuous", () => {
    const entries = bookRecipes(recipes, settings({ recipes: { a: { include: false, photo: false, servings: null } } }), {});
    expect(names(entries)).toEqual(["Suppe", "Torte", "Brot"]);
    expect(entries.map(entry => entry.number)).toEqual([1, 2, 3]);
  });
  test("a stale slug is ignored; a cookbook without recipes gives no entries", () => {
    const stale = settings({ recipes: { gone: { include: false, photo: true, servings: 9 } } });
    expect(bookRecipes(recipes, stale, {})).toHaveLength(4);
    expect(bookRecipes([], stale, {})).toEqual([]);
  });
});

describe("photo and servings", () => {
  const flags: Record<string, KhRecipeFlags> = { own: { ownPhoto: true } };
  const on = { include: true, photo: true, servings: null };
  const photo = (slug: string, extra: object = {}) =>
    bookRecipes([recipe(slug, slug, undefined, extra)], settings({ recipes: { [slug]: on } }), flags)[0]!.photo;
  test("only with the setting, the flag and an image", () => {
    expect(photo("own")).toBe(true);
    expect(photo("other")).toBe(false);
    expect(photo("own", { image: null })).toBe(false);
    expect(bookRecipes([recipe("own", "x")], settings(), flags)[0]!.photo).toBe(false);
  });
  test("servings default to the recipe's and can be overridden", () => {
    expect(bookRecipes([recipe("a", "A")], settings(), {})[0]!.servings).toBe(4);
    const entries = bookRecipes([recipe("a", "A")], settings({ recipes: { a: { include: true, photo: false, servings: 6 } } }), {});
    expect(entries[0]!.servings).toBe(6);
  });
});
