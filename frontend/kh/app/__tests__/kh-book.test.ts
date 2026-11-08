// KH: tests for the book's pure logic (D43): which recipes go in, in what order and number, with which photo and
// servings; stale settings; the empty cookbook.
import { afterEach, describe, expect, test, vi } from "vitest";
import { effectScope, nextTick, ref } from "vue";
import { loadCookbookBook, useBookSaving } from "../composables/use-kh-book";
import { deleteFailureKey, latestRequest, originOf, pairLabel } from "../lib/duplicates";
import { BOOK_AUTOSAVE_MS, bookRecipes, defaultBookSettings, editorState, fillDefaults, recipeSettings, withRecipe } from "../lib/book";
import type { KhBookSettings, KhDuplicatePair, KhRecipeFlags } from "../lib/api/books";

const putMock = vi.hoisted(() => vi.fn());
const getMock = vi.hoisted(() => vi.fn());
const userApi = vi.hoisted(() => ({
  cookbooks: { getOne: vi.fn() },
  recipes: { getAll: vi.fn(), getOne: vi.fn() },
  households: { getCurrentUserHousehold: vi.fn() },
}));
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ put: putMock, get: getMock }) }));
vi.mock("~/composables/api", () => ({ useUserApi: () => userApi }));

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

describe("editor state", () => {
  test("a cookbook that finds no recipes is empty, whatever the settings say", () => {
    expect(editorState([], settings(), {})).toEqual({ empty: true, entries: [] });
  });
  test("otherwise the entries; all recipes switched off is not the empty hint", () => {
    const off = settings({ recipes: { a: { include: false, photo: false, servings: null } } });
    expect(editorState([recipe("a", "A")], off, {})).toEqual({ empty: false, entries: [] });
    expect(editorState([recipe("a", "A")], settings(), {}).entries).toHaveLength(1);
  });
});

describe("settings helpers", () => {
  test("stored settings keep their values; only a missing title or subtitle gets the default", () => {
    const stored = { ...settings(), title: null, subtitle: null, toc: false };
    expect(fillDefaults(stored, "Kuchen", "Muster", 2026)).toMatchObject({ title: "Kuchen", subtitle: "Muster · 2026", toc: false });
    expect(fillDefaults({ ...stored, title: "Mein Buch", subtitle: "" }, "Kuchen", "Muster", 2026)).toMatchObject({ title: "Mein Buch", subtitle: "" });
  });
  test("withRecipe changes one recipe and leaves the others and the original alone", () => {
    const base = settings({ recipes: { a: { include: false, photo: false, servings: 2 } } });
    const next = withRecipe(base, "b", { photo: true });
    expect(next.recipes).toEqual({ a: base.recipes.a, b: { include: true, photo: true, servings: null } });
    expect(base.recipes.b).toBeUndefined();
  });
});

describe("autosave", () => {
  afterEach(() => {
    vi.useRealTimers();
    putMock.mockReset();
  });
  /** The saving in an effect scope, with the settings ref to change. */
  function saving(enabled = true) {
    const model = ref(settings());
    const scope = effectScope();
    const result = scope.run(() => useBookSaving("c1", model, enabled))!;
    return { model, ...result, stop: () => scope.stop() };
  }
  const change = async (model: { value: KhBookSettings }, title: string) => {
    model.value = { ...model.value, title };
    await nextTick();
  };

  test("several quick changes make one save, after the pause", async () => {
    vi.useFakeTimers();
    putMock.mockResolvedValue({ error: null, data: {} });
    const { model, status, stop } = saving();
    await change(model, "A");
    await vi.advanceTimersByTimeAsync(BOOK_AUTOSAVE_MS - 1);
    await change(model, "AB");
    await vi.advanceTimersByTimeAsync(BOOK_AUTOSAVE_MS - 1);
    expect(putMock).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(1);
    expect(putMock).toHaveBeenCalledTimes(1);
    expect(putMock.mock.calls[0]![0]).toBe("/api/kh/cookbooks/c1/print");
    expect(putMock.mock.calls[0]![1]).toMatchObject({ title: "AB" });
    expect(status.value).toBe("saved");
    stop();
  });

  test("a 403 says forbidden, another error says error and a retry saves again", async () => {
    vi.useFakeTimers();
    putMock.mockResolvedValueOnce({ error: { response: { status: 403 } } });
    const { model, status, retry, stop } = saving();
    await change(model, "A");
    await vi.advanceTimersByTimeAsync(BOOK_AUTOSAVE_MS);
    expect(status.value).toBe("forbidden");
    putMock.mockResolvedValueOnce({ error: new Error("offline") });
    await retry();
    expect(status.value).toBe("error");
    putMock.mockResolvedValueOnce({ error: null, data: {} });
    await retry();
    expect(status.value).toBe("saved");
    stop();
  });

  test("a save that is still running is not overtaken: the latest state follows after it, one at a time", async () => {
    vi.useFakeTimers();
    let release!: () => void;
    putMock.mockImplementationOnce(() => new Promise(resolve => (release = () => resolve({ error: null, data: {} }))));
    putMock.mockResolvedValue({ error: null, data: {} });
    const { model, status, stop } = saving();
    await change(model, "A");
    await vi.advanceTimersByTimeAsync(BOOK_AUTOSAVE_MS);
    await change(model, "AB");
    await vi.advanceTimersByTimeAsync(BOOK_AUTOSAVE_MS);
    expect(putMock).toHaveBeenCalledTimes(1);
    release();
    await vi.advanceTimersByTimeAsync(0);
    expect(putMock).toHaveBeenCalledTimes(2);
    expect(putMock.mock.calls[1]![1]).toMatchObject({ title: "AB" });
    expect(status.value).toBe("saved");
    stop();
  });

  test("a change in the last second is saved when the page is left", async () => {
    vi.useFakeTimers();
    putMock.mockResolvedValue({ error: null, data: {} });
    const { model, stop } = saving();
    await change(model, "A");
    stop();
    expect(putMock).toHaveBeenCalledTimes(1);
    expect(putMock.mock.calls[0]![1]).toMatchObject({ title: "A" });
  });

  test("leaving the page without a change saves nothing", async () => {
    vi.useFakeTimers();
    const { stop } = saving();
    stop();
    expect(putMock).not.toHaveBeenCalled();
  });

  test("nothing is saved when saving is not allowed", async () => {
    vi.useFakeTimers();
    const { model, stop } = saving(false);
    await change(model, "A");
    await vi.advanceTimersByTimeAsync(BOOK_AUTOSAVE_MS * 2);
    expect(putMock).not.toHaveBeenCalled();
    stop();
  });
});

describe("duplicate pairs", () => {
  const ref = (slug: string) => ({ slug, name: slug, orgUrl: null, tags: [] });
  const pair = (kind: KhDuplicatePair["kind"], similarity: number): KhDuplicatePair => ({ a: ref("a"), b: ref("b"), kind, similarity });
  const t = (key: string) => `[${key}]`;
  test("the similarity in whole percent and the kind in words", () => {
    expect(pairLabel(pair("similar_title", 0.846), t)).toBe("[kh.duplicates.similar_title] · 85 %");
    expect(pairLabel(pair("duplicate_link", 1), t)).toBe("[kh.duplicates.duplicate_link] · 100 %");
    expect(pairLabel(pair("similar_ingredients", 0.004), t)).toBe("[kh.duplicates.similar_ingredients] · 0 %");
  });
  test("the origin is the site, nothing for a recipe typed in or a broken link", () => {
    expect(originOf("https://www.example.com/rezept/1")).toBe("example.com");
    expect(originOf(null)).toBeNull();
    expect(originOf("kein link")).toBeNull();
  });
});

describe("loading a cookbook", () => {
  const stale = { include: false, photo: false, servings: 12 };
  const stored = (over: Partial<KhBookSettings> = {}) => ({ ...defaultBookSettings("Kuchen", "Muster", 2026), recipes: { gone: stale, a: stale }, ...over });
  /** Answers the book's GETs: SETTINGS for the print route (null: fails), flags empty. */
  function serve(settingsAnswer: KhBookSettings | null, failing: string[] = []) {
    userApi.cookbooks.getOne.mockResolvedValue({ data: { id: "c1", name: "Kuchen", householdId: "h1" } });
    userApi.recipes.getAll.mockResolvedValue({ data: { items: [{ slug: "a" }, { slug: "b" }] } });
    userApi.recipes.getOne.mockImplementation(async (slug: string) => (failing.includes(slug) ? { data: null } : { data: { slug, name: slug } }));
    userApi.households.getCurrentUserHousehold.mockResolvedValue({ data: { name: "Muster" } });
    getMock.mockImplementation(async (url: string) => (url.includes("/print") ? (settingsAnswer ? { data: settingsAnswer } : { data: null, error: new Error("down") }) : { data: {} }));
  }
  const load = async () => (await loadCookbookBook("kuchen", "h1")) as Exclude<Awaited<ReturnType<typeof loadCookbookBook>>, null | "error">;

  test("settings that cannot be read give an error, never the defaults to save over them", async () => {
    serve(null);
    expect(await loadCookbookBook("kuchen", "h1")).toBe("error");
  });

  test("recipes that cannot be read are counted, the others stay", async () => {
    serve(stored(), ["b"]);
    const book = await load();
    expect(book.failedRecipes).toBe(1);
    expect(book.recipes.map(recipe => recipe.slug)).toEqual(["a"]);
  });

  test("when every recipe loaded, settings of recipes no longer in the cookbook are dropped", async () => {
    serve(stored());
    const book = await load();
    expect(book.failedRecipes).toBe(0);
    expect(Object.keys(book.settings.recipes)).toEqual(["a"]);
  });

  test("when a recipe failed, nothing is dropped", async () => {
    serve(stored(), ["b"]);
    expect(Object.keys((await load()).settings.recipes).sort()).toEqual(["a", "gone"]);
  });
});

describe("duplicate report helpers", () => {
  test("only the newest request counts as current", () => {
    const start = latestRequest();
    const first = start();
    const second = start();
    expect(first()).toBe(false);
    expect(second()).toBe(true);
  });
  test("deleting somebody else's recipe (403) has its own message", () => {
    expect(deleteFailureKey(403)).toBe("kh.duplicates.delete-forbidden");
    expect(deleteFailureKey(500)).toBe("kh.duplicates.failed");
    expect(deleteFailureKey(undefined)).toBe("kh.duplicates.failed");
  });
});
