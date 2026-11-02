// KH: tests for the recipe view's arithmetic (D38): which times show as tiles, what the amount stepper starts from,
// when it is offered at all, how a step of one more or less turns into Mealie's scale, the amount's words, and which
// sources open as the original.
import { describe, expect, test } from "vitest";
import { recipeTimes, scaleBase, scaleLabel, scalesAmounts, sourceLink, stepScale } from "../composables/use-kh-recipe";
import de from "../../lang/de-DE.json";
import en from "../../lang/en-US.json";

/** Stands in for i18n's plural choice: the key and the number it was asked for. */
const t = (key: string, count: number) => `${key}:${count}`;

describe("times", () => {
  test("only the times the recipe has, in a fixed order", () => {
    expect(recipeTimes({ prepTime: "25 Minuten", performTime: "", totalTime: "1 Stunde" }, "de-DE"))
      .toEqual([{ key: "prep", value: "25 Minuten" }, { key: "total", value: "1 Stunde" }]);
    expect(recipeTimes({}, "de-DE")).toEqual([]);
  });

  test("structured times read as Mealie shows them", () => {
    expect(recipeTimes({ performTimeSeconds: 2700 }, "de-DE")).toEqual([{ key: "perform", value: "45 Minuten" }]);
  });
});

describe("amount stepper", () => {
  test("starts from the yield, else the servings, else there is none", () => {
    expect(scaleBase({ recipeYieldQuantity: 12, recipeServings: 4 })).toBe(12);
    expect(scaleBase({ recipeYieldQuantity: 0, recipeServings: 4 })).toBe(4);
    expect(scaleBase({})).toBe(0);
  });

  test("is offered only when an ingredient has an amount to change", () => {
    expect(scalesAmounts({ recipeIngredient: [{ quantity: 0, note: "250 g Linsen" }, { quantity: 2 }] })).toBe(true);
    expect(scalesAmounts({ recipeIngredient: [{ quantity: 0, note: "250 g Linsen" }] })).toBe(false);
    expect(scalesAmounts({})).toBe(false);
  });

  test("one more or one less is a whole piece or serving, never below one", () => {
    expect(stepScale(12, 1, 1)).toBeCloseTo(13 / 12);
    expect(stepScale(4, 0.25, -1)).toBeCloseTo(0.25);
    expect(stepScale(4, 1.5, -1)).toBeCloseTo(5 / 4);
  });

  test("from an amount between two whole ones, goes to the next whole one", () => {
    expect(stepScale(4, 0.6, 1)).toBeCloseTo(3 / 4);
    expect(stepScale(4, 0.6, -1)).toBeCloseTo(2 / 4);
    expect(stepScale(3, 7 / 3, -1)).toBeCloseTo(6 / 3);
  });
});

test("the original opens only from a web address", () => {
  expect(sourceLink("https://example.org/kuchen")).toBe("https://example.org/kuchen");
  expect(sourceLink(" http://example.org/suppe ")).toBe("http://example.org/suppe");
  expect(sourceLink("javascript:alert(1)")).toBe("");
  expect(sourceLink("Omas Kochbuch, Seite 12")).toBe("");
  expect(sourceLink(null)).toBe("");
});

describe("amount words", () => {
  test("a yield keeps its own words", () => {
    expect(scaleLabel({ recipeYieldQuantity: 12, recipeYield: "Stücke", recipeServings: 4 }, 13, t)).toBe("Stücke");
  });

  test("servings say serving or servings, with a yield text without number after them", () => {
    expect(scaleLabel({ recipeServings: 4 }, 1, t)).toBe("kh.recipe.servings:1");
    expect(scaleLabel({ recipeServings: 1, recipeYield: "Springform Ø 26 cm" }, 2, t))
      .toBe("kh.recipe.servings:2 · Springform Ø 26 cm");
  });

  test("a yield text alone stands as it is", () => {
    expect(scaleLabel({ recipeYield: "Springform Ø 26 cm" }, 0, t)).toBe("Springform Ø 26 cm");
  });

  test("the servings word has a singular and a plural form in both languages", () => {
    for (const texts of [de, en]) {
      expect(texts.kh.recipe.servings.split(" | ")).toHaveLength(2);
    }
  });
});
