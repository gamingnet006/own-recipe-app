// KH: tests for the step display text (D41, D42): amount parentheses behind ingredient names under the four
// conditions of the spec, and the highlighted times, also inside Markdown.
import { describe, expect, test } from "vitest";
import { onlyStepOf, stepDisplay, stepIngredientIds, stepNeeds, timeIndex, timerLabel, type KhNeed, type KhStepIngredient } from "../lib/step-text";

const butter: KhStepIngredient = { referenceId: "b", names: ["Butter"], amount: "200 g" };
const ref = (...ids: string[]) => ({ ingredientReferences: ids.map(referenceId => ({ referenceId })) });
const refText = (text: string, ...ids: string[]) => ({ text, ...ref(...ids) });
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

describe("shares named in the step text", () => {
  // An ingredient of FULL units at factor FACTOR; the share formatter mimics the amount formatting.
  const shared = (name: string, full: number, unit: string, factor = 1, id = "m"): KhStepIngredient => ({
    referenceId: id,
    names: [name],
    amount: `${full * factor} ${unit}`,
    shareAmount: fraction => `${Number((full * factor * fraction).toPrecision(10))} ${unit}`,
  });
  const flour = shared("Mehl", 250, "g");
  const display = (place: number, texts: string[], ingredient = flour) =>
    stepDisplay(place, texts[place]!, [ingredient], texts.map(t => refText(t, ingredient.referenceId)), new Set()).html;
  const amount = (value: string) => `<span class="kh-amount">(${value})</span>`;

  test("a fraction before the name, then the rest", () => {
    const texts = ["die Hälfte vom Mehl dazugeben", "Restliches Mehl unterheben"];
    expect(display(0, texts)).toBe(`die Hälfte vom Mehl ${amount("125 g")} dazugeben`);
    expect(display(1, texts)).toBe(`Restliches Mehl ${amount("125 g")} unterheben`);
  });
  test("follows the factor", () => {
    const texts = ["die Hälfte vom Mehl dazugeben", "Restliches Mehl unterheben"];
    expect(display(0, texts, shared("Mehl", 250, "g", 2))).toContain("(250 g)");
    expect(display(1, texts, shared("Mehl", 250, "g", 2))).toContain("(250 g)");
  });
  test("thirds, quarters and written fractions", () => {
    const milk = shared("Milch", 300, "ml");
    expect(display(0, ["ein Drittel der Milch", "x"], milk)).toContain("(100 ml)");
    expect(display(0, ["drei Viertel der Milch", "x"], milk)).toContain("(225 ml)");
    expect(display(0, ["zwei Drittel der Milch", "x"], milk)).toContain("(200 ml)");
    expect(display(0, ["½ des Mehls", "x"])).toContain("(125 g)");
    expect(display(0, ["1/2 vom Mehl", "x"])).toContain("(125 g)");
  });
  test("genitive and plural count as the name, the amount goes behind the form found", () => {
    expect(display(0, ["die Hälfte des Mehls dazu", "x"])).toBe(`die Hälfte des Mehls ${amount("125 g")} dazu`);
    expect(display(0, ["die Hälfte der Semmelbrösel", "x"], shared("Semmelbrösel", 100, "g"))).toContain("(50 g)");
  });
  test("remainder words", () => {
    for (const phrase of ["den Rest vom Mehl", "das übrige Mehl", "die übrigen Mehl", "restlichen Mehl"]) {
      expect(display(1, ["die Hälfte Mehl", phrase])).toContain("(125 g)");
    }
  });
  test("no amount for the rest when an earlier step names no fraction", () => {
    const texts = ["Mehl dazugeben", "Restliches Mehl unterheben"];
    expect(display(0, texts)).toBe("Mehl dazugeben");
    expect(display(1, texts)).toBe("Restliches Mehl unterheben");
  });
  test("no amount when the fraction is more than three words before the name", () => {
    expect(display(0, ["die Hälfte der Butter und dem Zucker mit Mehl", "x"])).not.toContain("kh-amount");
  });
  test("a fraction ends at punctuation", () => {
    expect(display(0, ["die Hälfte, dann Mehl", "x"])).not.toContain("kh-amount");
  });
  test("no amount without a fraction phrase, or for an ingredient of one step only", () => {
    expect(display(0, ["Mehl sieben", "x"])).toBe("Mehl sieben");
    const only = stepDisplay(0, "die Hälfte vom Mehl", [flour], [refText("die Hälfte vom Mehl", "m"), ref()], new Set());
    expect(only.html).toContain("(250 g)");
  });
  test("a step that does not reference the ingredient gets nothing", () => {
    const steps = [refText("die Hälfte vom Mehl", "m"), refText("die Hälfte vom Mehl", "m")];
    expect(stepDisplay(0, "die Hälfte vom Mehl", [flour], [ref(), steps[1]!], new Set()).html).toBe("die Hälfte vom Mehl");
  });
  test("English", () => {
    const flourEn = shared("flour", 300, "g");
    expect(display(0, ["add half of the flour", "x"], flourEn)).toContain("(150 g)");
    expect(display(1, ["half of the flour", "stir in the remaining flour"], flourEn)).toContain("(150 g)");
    expect(display(1, ["a third of the flour", "stir in the rest of the flour"], flourEn)).toContain("(200 g)");
  });
  test("a remainder that is used up gets nothing", () => {
    expect(display(2, ["die Hälfte Mehl", "die Hälfte Mehl", "den Rest vom Mehl"])).not.toContain("kh-amount");
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

/** A DOM element with a class and children, built without parsing HTML (Mealie's security lint). */
function el(tag: string, className: string, ...children: (Node | string)[]): HTMLElement {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.append(...children);
  return node;
}

describe("timeIndex", () => {
  const container = el("div", "", el("p", "", "erst ", el("span", "kh-time", "10 Min."), " dann ",
    el("b", "", el("span", "kh-time", "1 ", el("i", "", "Std.")))));
  const spans = container.querySelectorAll(".kh-time");

  test("the place of the clicked time among the times", () => {
    expect(timeIndex(spans[0]!, container)).toBe(0);
    expect(timeIndex(spans[1]!, container)).toBe(1);
    expect(timeIndex(container.querySelector("i"), container)).toBe(1);
  });
  test("-1 outside a time", () => {
    expect(timeIndex(container.querySelector("p"), container)).toBe(-1);
    expect(timeIndex(null, container)).toBe(-1);
  });
});

describe("timerLabel", () => {
  test("number and first four words, without Markdown marks", () => {
    expect(timerLabel(1, "**Den Teig** 10 Min. ruhen lassen, dann [formen](https://x.de)")).toBe("2. Den Teig 10 Min.");
  });
});

describe("stepNeeds", () => {
  const needs: KhNeed[] = [
    { referenceId: "b", name: "Butter", names: ["Butter"], amount: "200 g" },
    { referenceId: "m", name: "Mehl", names: ["Mehl"], amount: "300 g", shareAmount: fraction => `${300 * fraction} g` },
    { referenceId: "s", name: "Salz", names: ["Salz"], amount: null },
  ];
  test("name and amount for an ingredient only this step uses", () => {
    expect(stepNeeds(0, ref("b"), needs, [ref("b"), ref("m")])).toEqual(["Butter 200 g"]);
  });
  test("name alone when several steps share it or it has no amount", () => {
    expect(stepNeeds(0, ref("m", "s"), needs, [ref("m", "s"), ref("m")])).toEqual(["Mehl", "Salz"]);
  });
  test("the share the step text names", () => {
    const steps = [refText("die Hälfte vom Mehl", "m"), refText("Rest Mehl", "m")];
    expect(stepNeeds(0, steps[0]!, needs, steps)).toEqual(["Mehl 150 g"]);
    expect(stepNeeds(1, steps[1]!, needs, steps)).toEqual(["Mehl 150 g"]);
    expect(stepNeeds(1, refText("Mehl", "m"), needs, [steps[0]!, refText("Mehl", "m")])).toEqual(["Mehl"]);
  });
  test("nothing without references", () => {
    expect(stepNeeds(0, ref(), needs, [ref()])).toEqual([]);
    expect(stepNeeds(0, {}, needs, [{}])).toEqual([]);
  });
});

describe("stepIngredientIds", () => {
  test("lists the ingredients a step references and ignores empty ids", () => {
    const step = { ingredientReferences: [{ referenceId: "a" }, { referenceId: null }, { referenceId: "b" }] };
    expect([...stepIngredientIds(step)]).toEqual(["a", "b"]);
  });

  test("a step without references or no step uses none", () => {
    expect(stepIngredientIds({}).size).toBe(0);
    expect(stepIngredientIds(undefined).size).toBe(0);
  });
});
