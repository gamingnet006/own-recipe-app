// KH: tests for the review's tag chips and the confirmation of tag proposals.
import { describe, expect, it } from "vitest";
import { confirmedItems, recognizedTags, withTag } from "../lib/draft-tags";

const soup = { id: "1", name: "Suppe", slug: "suppe" };
const vegan = { id: "2", name: "vegan", slug: "vegan" };

describe("draft tags", () => {
  it("starts with the recognized tags that exist, and without a recipe with none", () => {
    expect(recognizedTags({ tags: [soup, { id: null, name: "neu" }] })).toEqual([soup]);
    expect(recognizedTags(null)).toEqual([]);
  });

  it("adds a tag once", () => {
    expect(withTag([soup], vegan)).toEqual([soup, vegan]);
    expect(withTag([soup], soup)).toEqual([soup]);
  });

  it("sends only the ticked tags and skips recipes with none left", () => {
    const proposals = [
      { recipeId: "a", slug: "a", name: "A", tags: [soup, vegan] },
      { recipeId: "b", slug: "b", name: "B", tags: [soup] },
    ];
    expect(confirmedItems(proposals, new Set(["a:2", "b:1"]))).toEqual([{ recipeId: "a", tagIds: ["1"] }]);
    expect(confirmedItems(proposals, new Set())).toHaveLength(2);
  });
});
