// KH: tests for editing a draft in its preview and choosing where it goes (D55): the edit request's body, the step
// links that follow an edit, which cookbooks count as one-category cookbooks, and the texts.
import { describe, expect, test } from "vitest";
import { cookbookFilter, editBody, findByName, oneCategoryCookbooks, remapLinked } from "../lib/draft-edit";
import de from "../../lang/de-DE.json";
import en from "../../lang/en-US.json";

const link = (step: number, referenceId: string, text: string) => ({ step, referenceId, text });

describe("editBody", () => {
  test("builds one edit per kind from the trimmed text", () => {
    expect(editBody({ kind: "name" }, "  Kuchen ")).toEqual({ name: "Kuchen" });
    expect(editBody({ kind: "ingredient", index: 2 }, "250 g Mehl")).toEqual({ ingredient: { index: 2, text: "250 g Mehl" } });
    expect(editBody({ kind: "step", index: 0 }, "Rühren.")).toEqual({ step: { index: 0, text: "Rühren." } });
  });

  test("gives nothing for an empty text", () => {
    expect(editBody({ kind: "name" }, "   ")).toBeNull();
  });
});

describe("remapLinked", () => {
  const before = [link(0, "a", "250 g"), link(0, "b", "2 EL"), link(1, "a", "50 g")];

  test("keeps the indices of links that are still there, at their new place", () => {
    const after = [link(0, "a", "250 g"), link(1, "a", "50 g")];
    expect(remapLinked(before, after, [0, 1, 2])).toEqual([0, 1]);
    expect(remapLinked(before, after, [2])).toEqual([1]);
  });

  test("drops the index of a link that is gone, and keeps unlinked ones unlinked", () => {
    expect(remapLinked(before, [link(0, "b", "2 EL"), link(1, "a", "50 g")], [0, 2])).toEqual([1]);
    expect(remapLinked(before, before, [1])).toEqual([1]);
  });

  test("tells two equal links apart by their order", () => {
    const twice = [link(0, "a", "1 EL"), link(0, "a", "1 EL")];
    expect(remapLinked(twice, [link(0, "a", "1 EL")], [1])).toEqual([]);
    expect(remapLinked(twice, [link(0, "a", "1 EL")], [0])).toEqual([0]);
  });
});

describe("one-category cookbooks", () => {
  const book = (id: string, queryFilterString: string) => ({ id, name: id, queryFilterString });
  const id = "11111111-2222-3333-4444-555555555555";

  test("the filter a new cookbook gets reads back as its category", () => {
    expect(oneCategoryCookbooks([book("k", cookbookFilter(id))])).toEqual([{ cookbook: book("k", cookbookFilter(id)), categoryId: id }]);
  });

  test("a filter with several categories or other conditions is not offered", () => {
    const other = "22222222-2222-3333-4444-555555555555";
    const several = `recipe_category.id IN ["${id}", "${other}"]`;
    const mixed = `recipe_category.id IN ["${id}"] AND recipe_tag.id IN ["${other}"]`;
    expect(oneCategoryCookbooks([book("a", several), book("b", mixed), book("c", ""), book("d", "name = x")])).toEqual([]);
  });

  test("accepts the older CONTAINS ALL form with one category", () => {
    expect(oneCategoryCookbooks([book("e", `recipe_category.id CONTAINS ALL ["${id}"]`)])[0]?.categoryId).toBe(id);
  });
});

describe("findByName", () => {
  const items = [{ name: "Kuchen" }, { name: "Suppen" }];

  test("finds a name whatever its case and spaces", () => {
    expect(findByName(items, "  kuchen ")).toBe(items[0]);
    expect(findByName(items, "Brot")).toBeUndefined();
  });
});

describe("texts", () => {
  test("German and English have the same edit and where keys", () => {
    expect(Object.keys(de.kh.drafts.edit).sort()).toEqual(Object.keys(en.kh.drafts.edit).sort());
    expect(Object.keys(de.kh.drafts.where).sort()).toEqual(Object.keys(en.kh.drafts.where).sort());
    expect(Object.keys(en.kh.drafts.where).length).toBeGreaterThan(0);
  });
});
