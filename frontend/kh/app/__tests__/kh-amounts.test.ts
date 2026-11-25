// KH: tests for the amounts' display (D39, phase 3): fractions, the rounding of grams and millilitres with kg and l,
// halves of pieces with the egg tip, 3 TL as 1 EL, ranges and fixed amounts, each at the factors the spec names.
import { expect, test, vi } from "vitest";
import { nextTick, reactive } from "vue";
import {
  formatAmount,
  haveOnlyFactor,
  panFactor,
  parsePan,
  scaleStepText,
  scaleTitle,
  servingsFactor,
  stepSegments,
  timeHint,
  type KhAmount,
} from "../lib/amounts";
import { khAmounts } from "../lib/amounts-store";
import { useKhAmounts } from "../composables/use-kh-amounts";

const getMock = vi.hoisted(() => vi.fn());

vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock }) }));

const g = { name: "Gramm", abbreviation: "g" };
const ml = { name: "Milliliter", abbreviation: "ml" };
const el = { name: "Esslöffel", abbreviation: "EL" };
const tl = { name: "Teelöffel", abbreviation: "TL", useAbbreviation: true };
const prise = { name: "Prise" };
const fmt = (a: KhAmount, scale = 1, locale = "de-DE") => formatAmount(a, scale, locale);
const text = (a: KhAmount, scale = 1, locale = "de-DE") => fmt(a, scale, locale).quantity;

test("fractions near ¼ ⅓ ½ ⅔ ¾, else one decimal", () => {
  expect(text({ quantity: 0.5, unit: el })).toBe("½");
  expect(text({ quantity: 1 / 3, unit: el })).toBe("⅓");
  expect(text({ quantity: 0.66, unit: el })).toBe("⅔");
  expect(text({ quantity: 0.75, unit: el })).toBe("¾");
  expect(text({ quantity: 1.5, unit: el })).toBe("1½");
  expect(text({ quantity: 0.4, unit: el })).toBe("0,4");
  expect(text({ quantity: 0.4, unit: el }, 1, "en-US")).toBe("0.4");
  expect(text({ quantity: 2, unit: el })).toBe("2");
});

test("grams and millilitres round by size", () => {
  expect(text({ quantity: 14.5, unit: g }, 0.5)).toBe("7,3");
  expect(text({ quantity: 91.2, unit: g }, 0.5)).toBe("46");
  expect(text({ quantity: 246, unit: g }, 0.5)).toBe("125");
  expect(text({ quantity: 1006, unit: g }, 0.5)).toBe("500");
  expect(fmt({ quantity: 1250, unit: g })).toMatchObject({ quantity: "1,25", unit: "kg" });
  expect(fmt({ quantity: 1000, unit: g })).toMatchObject({ quantity: "1", unit: "kg" });
  expect(fmt({ quantity: 1500, unit: ml })).toMatchObject({ quantity: "1,5", unit: "l" });
});

test("factors 0.5, 2 and 3", () => {
  expect(text({ quantity: 250, unit: g }, 0.5)).toBe("125");
  expect(text({ quantity: 250, unit: g }, 2)).toBe("500");
  expect(text({ quantity: 250, unit: g }, 3)).toBe("750");
});

test("pieces in halves, with the egg tip", () => {
  expect(fmt({ quantity: 3, food: "Eier" }, 0.5)).toMatchObject({ quantity: "1½", eggTip: true });
  expect(fmt({ quantity: 2 }, 1.3)).toMatchObject({ quantity: "2½", eggTip: false });
});

test("factor 1 shows the recipe's own amounts", () => {
  expect(text({ quantity: 0.25 })).toBe("¼"); // ¼ Zwiebel, not ½
  expect(text({ quantity: 1.25 })).toBe("1¼");
  expect(text({ quantity: 12.5, unit: g })).toBe("12,5");
  expect(text({ quantity: 333, unit: g })).toBe("333");
  expect(text({ quantity: 0.25, fixed: true }, 2)).toBe("¼");
});

test("3 TL are 1 EL when it divides", () => {
  expect(fmt({ quantity: 3, unit: tl })).toMatchObject({ quantity: "1", unit: "EL" });
  expect(fmt({ quantity: 6, unit: tl })).toMatchObject({ quantity: "2", unit: "EL" });
  expect(fmt({ quantity: 4, unit: tl })).toMatchObject({ quantity: "4", unit: null });
});

test("ranges scale at both ends", () => {
  expect(text({ quantity: 2, upper: 3, unit: el }, 2)).toBe("4–6");
});

test("fixed amounts stay", () => {
  expect(text({ quantity: 1, unit: prise, fixed: true }, 3)).toBe("1");
  expect(fmt({ quantity: 1, unit: prise }, 3).plural).toBe(false); // the unit reads as shown: "1 Prise"
  expect(fmt({ quantity: 1, unit: el }, 3).plural).toBe(true);
  expect(text({ quantity: 2, unit: el, fixed: true }, 2)).toBe("2");
});

test("without extras the unit keeps a pinch fixed", () => {
  // Review focus 2: a line Mealie's parser read has no kh extras
  expect(text({ quantity: 1, unit: prise }, 2)).toBe("1");
});

test("tiny amounts never show as 0", () => {
  expect(text({ quantity: 0.02, unit: g })).toBe("< 0,1");
});

test("servings", () => {
  expect(servingsFactor(8, 4)).toBe(2);
  expect(servingsFactor(2, 4)).toBe(0.5);
  expect(servingsFactor(12, 4)).toBe(3);
  // Review focus 4: nothing usable typed in, or no base to start from
  for (const [servings, base] of [[0, 4], [-1, 4], [Number.NaN, 4], [8, 0]]) {
    expect(servingsFactor(servings!, base!)).toBeNull();
  }
});

test("I only have", () => {
  expect(haveOnlyFactor(300, 250)).toBeCloseTo(1.2);
  expect(haveOnlyFactor(0, 250)).toBeNull();
  expect(haveOnlyFactor(300, 0)).toBeNull();
});

test("pans", () => {
  expect(panFactor({ shape: "round", diameter: 26 }, { shape: "round", diameter: 20 })).toBeCloseTo(0.59, 2);
  expect(panFactor({ shape: "round", diameter: 26 }, { shape: "rect", length: 20, width: 30 })).toBeCloseTo(1.13, 2);
  expect(panFactor({ shape: "round", diameter: 0 }, { shape: "round", diameter: 20 })).toBeNull();
  expect(panFactor({ shape: "round", diameter: 26 }, { shape: "rect", length: -20, width: 30 })).toBeNull();
});

test("the old pan from the yield", () => {
  expect(parsePan("Springform Ø 26 cm")).toEqual({ shape: "round", diameter: 26 });
  expect(parsePan("26er Springform")).toEqual({ shape: "round", diameter: 26 });
  expect(parsePan("24 x 30 cm")).toEqual({ shape: "rect", length: 24, width: 30 });
  expect(parsePan("24×30")).toEqual({ shape: "rect", length: 24, width: 30 });
  // Mealie's import takes the number out of a yield: "26" and "Springform Ø cm"; the sheet joins them again
  expect(parsePan("26 Springform Ø cm")).toEqual({ shape: "round", diameter: 26 });
  expect(parsePan("26 er Springform")).toEqual({ shape: "round", diameter: 26 });
  expect(parsePan("1 Springform Ø 26 cm")).toEqual({ shape: "round", diameter: 26 });
  expect(parsePan("1 Kuchen")).toBeNull();
  expect(parsePan(null)).toBeNull();
});

test("times hint", () => {
  expect(timeHint(2.5)).toBe(true);
  expect(timeHint(0.4)).toBe(true);
  for (const scale of [2, 0.5, 1]) expect(timeHint(scale)).toBe(false);
});

test("extreme factors stay finite", () => {
  // Review focus 4: 0.1 and 10 never show NaN or Infinity
  const amounts: KhAmount[] = [
    { quantity: 250, unit: g },
    { quantity: 3, food: "Eier" },
    { quantity: 2, upper: 3, unit: el },
    { quantity: 3, unit: tl },
    { quantity: 1, unit: prise },
  ];
  for (const amount of amounts) {
    for (const scale of [0.1, 10]) expect(fmt(amount, scale).quantity).not.toMatch(/NaN|Infinity/);
  }
});

test("step segments", () => {
  const link = { start: 0, end: 5, text: "250 g" };
  expect(stepSegments("250 g Mehl unterrühren", [link])).toEqual([
    { text: "250 g", link: 0 },
    { text: " Mehl unterrühren", link: null },
  ]);
  // Review focus 3: a link whose text no longer stands there, and one overlapping another, are left out
  const stale = { start: 6, end: 10, text: "Zuck" };
  const overlapping = { start: 3, end: 7, text: "g Me" };
  expect(stepSegments("250 g Mehl", [link, stale, overlapping])).toEqual([
    { text: "250 g", link: 0 },
    { text: " Mehl", link: null },
  ]);
});

const link = (start: number, text: string, referenceId = "mehl", fraction = 1) =>
  ({ step: 0, start, end: start + text.length, text, referenceId, fraction });
const lines = new Map<string, KhAmount>([
  ["mehl", { quantity: 250, unit: g }],
  ["zucker", { quantity: 2, unit: el }],
  ["butter", { quantity: 600, unit: g }],
]);
const step = (text: string, links: ReturnType<typeof link>[], scale: number) => scaleStepText(text, links, lines, scale, "de-DE");

test("linked amounts follow the factor", () => {
  expect(step("250 g Mehl unterrühren", [link(0, "250 g")], 2)).toBe("500 g Mehl unterrühren");
});

test("parts follow too", () => {
  expect(step("125 g Mehl", [link(0, "125 g", "mehl", 0.5)], 2)).toBe("250 g Mehl");
});

test("kilograms in the text", () => {
  expect(step("600 g Butter", [link(0, "600 g", "butter")], 2)).toBe("1,2 kg Butter");
});

test("scale 1 keeps the text", () => {
  expect(step("250 g Mehl unterrühren", [link(0, "250 g")], 1)).toBe("250 g Mehl unterrühren");
});

test("a stale link changes nothing", () => {
  // Review focus 3: the text at the link's place is no longer the link's text
  expect(step("300 g Mehl unterrühren", [link(0, "250 g")], 2)).toBe("300 g Mehl unterrühren");
});

test("several links in one step", () => {
  const text = "250 g Mehl und 2 EL Zucker";
  expect(step(text, [link(0, "250 g"), link(15, "2 EL", "zucker")], 2)).toBe("500 g Mehl und 4 EL Zucker");
});

test("the amounts load when the recipe opens and again after a save, the newest answer wins", async () => {
  const answers: ((value: unknown) => void)[] = [];
  getMock.mockImplementation(() => new Promise(resolve => answers.push(resolve)));
  const recipe = reactive({ id: "r1", dateUpdated: "1" });
  useKhAmounts(() => recipe);
  recipe.dateUpdated = "2"; // saved: the backend moved or dropped links
  await nextTick();
  expect(getMock).toHaveBeenCalledTimes(2);
  const newer = { extras: [], stepAmounts: [] };
  answers[1]!({ data: newer });
  answers[0]!({ data: { extras: [{ referenceId: "x", upper: 3, fixed: false }], stepAmounts: [] } }); // late, older
  await new Promise(resolve => setTimeout(resolve));
  expect(khAmounts.value).toEqual(newer);
});

test("scaleTitle follows the servings a section title names (v1.3)", () => {
  expect(scaleTitle("Zutaten für 6 Portionen:", 8 / 6, "de-DE")).toBe("Zutaten für 8 Portionen:");
  expect(scaleTitle("Für 4 Personen", 1.5, "de-DE")).toBe("Für 6 Personen");
  expect(scaleTitle("Ingredients for 4 servings", 0.5, "en-US")).toBe("Ingredients for 2 servings");
  expect(scaleTitle("Teig für 4 Portionen", 1 / 3, "de-DE")).toBe("Teig für 1,3 Portionen");
  expect(scaleTitle("Für den Teig", 2, "de-DE")).toBe("Für den Teig");
  expect(scaleTitle("Zutaten für 6 Portionen:", 1, "de-DE")).toBe("Zutaten für 6 Portionen:");
});

test("English pans, inches read as centimetres", () => {
  expect(parsePan("26 cm springform pan")).toEqual({ shape: "round", diameter: 26 });
  expect(parsePan("round cake tin 22 cm")).toEqual({ shape: "round", diameter: 22 });
  expect(parsePan("9-inch springform pan")).toEqual({ shape: "round", diameter: 9 * 2.54 });
  expect(parsePan("a 10 inch round")).toEqual({ shape: "round", diameter: 10 * 2.54 });
  expect(parsePan("9 x 13 inch baking dish")).toEqual({ shape: "rect", length: 9 * 2.54, width: 13 * 2.54 });
  expect(parsePan("loaf pan 25 x 11 cm")).toEqual({ shape: "rect", length: 25, width: 11 });
  expect(parsePan("a baking dish")).toBeNull();
  expect(parsePan("Serves 4")).toBeNull();
});
