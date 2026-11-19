// KH: tests for the recipe as text (D61) with a recipe written for the test: scale 1 is the format
// tests/kh/drafts/test_kh_drafts_text_format.py reads back (keep both in sync), scale 2 scales ingredients, section
// titles and linked step amounts, and the optional parts stay out when the recipe lacks them.
import { describe, expect, test } from "vitest";
import { formatAmount, scaleStepText, type KhAmount, type KhStepLink } from "../lib/amounts";
import { photoExtension, recipeText, type TextReaders } from "../lib/recipe-text";
import type { RecipeOut } from "~/lib/api/types/recipe";

const amounts: Record<string, KhAmount & { food: string }> = {
  m: { quantity: 200, unit: { name: "g" }, food: "Mehl" },
  z: { quantity: 100, unit: { name: "g" }, food: "Zucker" },
  e: { quantity: 3, food: "Eier" },
};
const links: KhStepLink[] = [{ step: 1, start: 0, end: 10, text: "30 Minuten", referenceId: "m", fraction: 0.15 }];

// Mealie's display needs a component; this stand-in writes "<amount> <unit> <food>" with the same amount function
const read: TextReaders = {
  ingredient: (line, scale) => {
    const amount = amounts[line.referenceId ?? ""]!;
    const shown = formatAmount(amount, scale, "de-DE");
    return [shown.quantity, shown.unit ?? amount.unit?.name, amount.food].filter(Boolean).join(" ");
  },
  step: (place, step, scale) => scaleStepText(step.text ?? "", links.filter(link => link.step === place), new Map(Object.entries(amounts)), scale, "de-DE"),
};

const recipe = {
  name: "Testkuchen",
  recipeServings: 4,
  prepTime: "15 Min.",
  performTime: "30 Min.",
  totalTime: "45 Min.",
  orgURL: "https://example.org/testkuchen",
  recipeIngredient: [
    { referenceId: "m", title: "Für den Teig" },
    { referenceId: "z" },
    { referenceId: "e", title: "Für den Guss für 4 Portionen" },
  ],
  recipeInstructions: [
    { text: "Ofen auf 180 Grad vorheizen." },
    { title: "Backen", text: "30 Minuten backen.\nAbkühlen lassen." },
  ],
  notes: [{ title: "", text: "Schmeckt auch kalt." }],
} as unknown as RecipeOut;

describe("recipeText", () => {
  test("scale 1 is the export format", () => {
    expect(recipeText(recipe, 1, "de-DE", read)).toBe(`Testkuchen
Portionen: 4 · Vorbereitung: 15 Min. · Zubereitung: 30 Min. · Gesamt: 45 Min.

Zutaten:
Für den Teig
- 200 g Mehl
- 100 g Zucker
Für den Guss für 4 Portionen
- 3 Eier

Zubereitung:
1. Ofen auf 180 Grad vorheizen.
Backen
2. 30 Minuten backen. Abkühlen lassen.

Notizen:
Schmeckt auch kalt.

Quelle: https://example.org/testkuchen

Exportiert aus Kochheft
`);
  });

  test("scale 2 doubles servings, amounts, section titles and linked step amounts", () => {
    const text = recipeText(recipe, 2, "de-DE", read);
    expect(text).toContain("Portionen: 8 ·");
    expect(text).toContain("- 400 g Mehl\n- 200 g Zucker");
    expect(text).toContain("Für den Guss für 8 Portionen\n- 6 Eier");
    expect(text).toContain("2. 60 Minuten backen.");
  });

  test("without servings, times, notes and source only the sections and the signature remain", () => {
    const bare = { name: "Brot", recipeIngredient: [{ referenceId: "m" }], recipeInstructions: [{ text: "Backen." }] } as unknown as RecipeOut;
    expect(recipeText(bare, 1, "de-DE", read)).toBe("Brot\n\nZutaten:\n- 200 g Mehl\n\nZubereitung:\n1. Backen.\n\nExportiert aus Kochheft\n");
  });

  test("steps and ingredients without text are left out and numbering stays continuous", () => {
    const odd = { name: "Brot", recipeIngredient: [], recipeInstructions: [{ text: " " }, { text: "Backen." }] } as unknown as RecipeOut;
    expect(recipeText(odd, 1, "de-DE", read)).toContain("Zubereitung:\n1. Backen.");
  });
});

describe("photoExtension", () => {
  test("from the media type", () => {
    expect(photoExtension("image/webp")).toBe("webp");
    expect(photoExtension("image/jpeg; charset=x")).toBe("jpg");
    expect(photoExtension("image/png")).toBe("png");
    expect(photoExtension(null)).toBe("webp");
  });
});

test("the yield is written as the page shows it and scales", () => {
  const muffins = { name: "Muffins", recipeServings: 12, recipeYieldQuantity: 12, recipeYield: "Muffins", recipeIngredient: [], recipeInstructions: [] } as unknown as RecipeOut;
  // the parser reads "Portionen: 13 Muffins" back as servings 13 and yield "Muffins" (test_servings_with_a_yield_word)
  expect(recipeText(muffins, 13 / 12, "de-DE", read)).toContain("\nPortionen: 13 Muffins\n");
  expect(recipeText(muffins, 1, "de-DE", read)).toContain("Portionen: 12 Muffins");
});
