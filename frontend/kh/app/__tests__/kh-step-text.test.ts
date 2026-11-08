// KH: tests for the step display text (D41, D42): amount parentheses behind ingredient names under the four
// conditions of the spec, and the highlighted times, also inside Markdown.
import { describe, expect, test } from "vitest";
import { onlyStepOf, stepDisplay, type KhStepIngredient } from "../lib/step-text";

const butter: KhStepIngredient = { referenceId: "b", names: ["Butter"], amount: "200 g" };
const ref = (...ids: string[]) => ({ ingredientReferences: ids.map(referenceId => ({ referenceId })) });
const alone = [ref("b"), ref()];
const html = (text: string, ingredients: KhStepIngredient[], steps = alone, linked = new Set<string>()) =>
  stepDisplay(0, text, ingredients, steps, linked).html;

describe("amount parentheses", () => {
  test("after the name of an ingredient used by this step only", () => {
    expect(html("die Butter schmelzen", [butter])).toBe("die Butter <span class=\"kh-amount\">(200 g)</span> schmelzen");
  });
  test("unchanged when two steps use the ingredient", () => {
    expect(html("die Butter schmelzen", [butter], [ref("b"), ref("b")])).toBe("die Butter schmelzen");
  });
  test("unchanged when the step already has an amount for it", () => {
    expect(html("die Butter schmelzen", [butter], alone, new Set(["b"]))).toBe("die Butter schmelzen");
  });
  test("plural name, whole words only", () => {
    const egg: KhStepIngredient = { referenceId: "b", names: ["Ei", "Eier"], amount: "3" };
    expect(html("die Eier verquirlen", [egg])).toBe("die Eier <span class=\"kh-amount\">(3)</span> verquirlen");
    expect(html("das Eigelb", [egg])).toBe("das Eigelb");
    expect(html("Salzwasser", [{ referenceId: "b", names: ["Salz"], amount: "1 TL" }])).toBe("Salzwasser");
  });
  test("only after the first occurrence, ignoring case", () => {
    expect(html("Butter in die Pfanne, dann die butter bräunen", [butter])).toBe(
      "Butter <span class=\"kh-amount\">(200 g)</span> in die Pfanne, dann die butter bräunen",
    );
  });
  test("unchanged without an amount", () => {
    expect(html("die Butter schmelzen", [{ ...butter, amount: null }])).toBe("die Butter schmelzen");
  });
});

describe("times", () => {
  test("highlighted inside Markdown", () => {
    const result = stepDisplay(0, "**10 Min.** ruhen", [], [], new Set());
    expect(result.html).toBe("**<span class=\"kh-time\">10 Min.</span>** ruhen");
    expect(result.times[0]!.seconds).toBe(600);
  });
  test("two times in order", () => {
    const result = stepDisplay(0, "10 Min. ruhen, 1 Std. backen", [], [], new Set());
    expect(result.html).toBe("<span class=\"kh-time\">10 Min.</span> ruhen, <span class=\"kh-time\">1 Std.</span> backen");
    expect(result.times.map(t => t.seconds)).toEqual([600, 3600]);
  });
  test("together with an amount", () => {
    expect(html("die Butter 10 Min. schmelzen", [butter])).toBe(
      "die Butter <span class=\"kh-amount\">(200 g)</span> <span class=\"kh-time\">10 Min.</span> schmelzen",
    );
  });
});

describe("onlyStepOf", () => {
  test("the single step that references it", () => {
    expect(onlyStepOf("b", [ref("b"), ref()])).toBe(0);
    expect(onlyStepOf("b", [ref(), ref("b")])).toBe(1);
  });
  test("null for none or several", () => {
    expect(onlyStepOf("b", [ref("b"), ref("b")])).toBeNull();
    expect(onlyStepOf("b", [ref(), {}])).toBeNull();
  });
});
