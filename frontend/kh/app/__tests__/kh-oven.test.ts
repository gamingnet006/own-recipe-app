// KH: tests for the fan-oven bracket (D43, F6): which temperatures get one, in which direction, the device setting
// and the combination with amounts and times in stepDisplay.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { ovenBrackets } from "../lib/oven";
import { stepDisplay, type KhStepIngredient } from "../lib/step-text";

const KEY = "kh-oven";
const texts = (text: string, oven: "conventional" | "fan") => ovenBrackets(text, oven).map(b => b.text);

describe("fan oven", () => {
  test("a bare temperature gets the fan value right after it", () => {
    const text = "auf 180 °C vorheizen";
    expect(ovenBrackets(text, "fan")).toEqual([{ at: text.indexOf("°C") + 2, text: " (Umluft 160 °C)" }]);
  });
  test("°C without space, and Grad", () => {
    expect(texts("auf 180°C vorheizen", "fan")).toEqual([" (Umluft 160 °C)"]);
    expect(texts("200 Grad", "fan")).toEqual([" (Umluft 180 °C)"]);
  });
  test("a text stating the fan already gets none, before or after the number", () => {
    expect(texts("bei 160 °C Umluft backen", "fan")).toEqual([]);
    expect(texts("Umluft 160 °C", "fan")).toEqual([]);
  });
  test("a text stating the conventional heat still gets the fan value", () => {
    expect(texts("180 °C Ober-/Unterhitze", "fan")).toEqual([" (Umluft 160 °C)"]);
  });
  test("turning the tray by an angle is no oven temperature", () => {
    expect(texts("Blech nach 15 Min. um 180 Grad drehen", "fan")).toEqual([]);
    expect(texts("das Blech 180 Grad drehen", "fan")).toEqual([]);
    expect(texts("Form um 180 Grad gewendet", "fan")).toEqual([]);
  });
  test("preheating to the same number still gets its bracket", () => {
    expect(texts("auf 180 Grad vorheizen und dann drehen", "fan")).toEqual([" (Umluft 160 °C)"]);
  });
  test("a range converts both ends", () => {
    expect(texts("bei 180-200 °C backen", "fan")).toEqual([" (Umluft 160–180 °C)"]);
  });
});

describe("conventional oven", () => {
  test("a fan temperature gets the conventional value", () => {
    expect(texts("bei 160 °C Umluft backen", "conventional")).toEqual([" (Ober-/Unterhitze 180 °C)"]);
    expect(texts("Umluft bei 160 °C", "conventional")).toEqual([" (Ober-/Unterhitze 180 °C)"]);
  });
  test("a fan word more than three words away does not count", () => {
    expect(texts("160 °C und dann noch lange Umluft", "conventional")).toEqual([]);
  });
  test("a bare temperature or a stated conventional heat gets none", () => {
    expect(texts("auf 180 °C vorheizen", "conventional")).toEqual([]);
    expect(texts("180 °C Ober-/Unterhitze", "conventional")).toEqual([]);
    expect(texts("180 °C Ober- und Unterhitze", "conventional")).toEqual([]);
    expect(texts("180 °C O/U", "conventional")).toEqual([]);
  });
});

describe("temperatures that are not oven temperatures (Review Focus 5)", () => {
  test.each(["auf 60 °C abkühlen", "Kerntemperatur 75 °C", "bei −18 °C lagern", "bei -18 °C lagern", "auf 99 Grad"])("%s", (text) => {
    expect(texts(text, "fan")).toEqual([]);
    expect(texts(text, "conventional")).toEqual([]);
  });
  test("100 °C is the lowest", () => {
    expect(texts("bei 100 °C trocknen", "fan")).toEqual([" (Umluft 80 °C)"]);
  });
  test("decimals and longer numbers are no oven temperature", () => {
    expect(texts("auf 180,5 °C", "fan")).toEqual([]);
    expect(texts("Zahl 1180 °C", "fan")).toEqual([]);
  });
});

describe("several temperatures", () => {
  test("one bracket each, in order, each judged by its own words", () => {
    const text = "erst 200 °C, dann 180 °C Umluft";
    expect(ovenBrackets(text, "fan")).toEqual([{ at: text.indexOf("°C") + 2, text: " (Umluft 180 °C)" }]);
    expect(texts("erst 200 °C Ober-/Unterhitze, dann 180 °C Umluft", "conventional")).toEqual([" (Ober-/Unterhitze 200 °C)"]);
    expect(texts("200 °C, dann 180 °C", "fan")).toEqual([" (Umluft 180 °C)", " (Umluft 160 °C)"]);
  });
});

describe("useKhOven", () => {
  beforeEach(() => localStorage.clear());
  // The setting lives in module state, so each test loads the module anew, as a page reload would.
  async function fresh() {
    vi.resetModules();
    return (await import("../lib/oven")).useKhOven();
  }

  test("conventional at first", async () => {
    expect((await fresh()).value).toBe("conventional");
  });
  test("a stored choice comes back, and changes are stored", async () => {
    localStorage.setItem(KEY, "fan");
    const oven = await fresh();
    expect(oven.value).toBe("fan");
    oven.value = "conventional";
    expect(localStorage.getItem(KEY)).toBe("conventional");
  });
  test("a broken value gives the standard", async () => {
    localStorage.setItem(KEY, "{not valid");
    expect((await fresh()).value).toBe("conventional");
  });
});

describe("stepDisplay with an oven", () => {
  const butter: KhStepIngredient = { referenceId: "b", names: ["Butter"], amount: "200 g" };
  const steps = [{ ingredientReferences: [{ referenceId: "b" }] }];
  const show = (text: string, oven: "conventional" | "fan" | null) => stepDisplay(0, text, [butter], steps, new Set(), oven);

  test("the bracket is an amount span right after the temperature", () => {
    expect(show("auf 180 °C vorheizen", "fan").html).toBe("auf 180 °C <span class=\"kh-amount\">(Umluft 160 °C)</span> vorheizen");
  });
  test("null and no argument add nothing", () => {
    expect(show("auf 180 °C vorheizen", null).html).toBe("auf 180 °C vorheizen");
    expect(stepDisplay(0, "auf 180 °C vorheizen", [], [], new Set()).html).toBe("auf 180 °C vorheizen");
  });
  test("together with an amount and a time in one sentence", () => {
    expect(show("Butter schmelzen, bei 180 °C 10 Min. backen", "fan").html).toBe(
      "Butter <span class=\"kh-amount\">(200 g)</span> schmelzen, bei 180 °C <span class=\"kh-amount\">(Umluft 160 °C)</span>"
      + " <span class=\"kh-time\">10 Min.</span> backen",
    );
  });
});
