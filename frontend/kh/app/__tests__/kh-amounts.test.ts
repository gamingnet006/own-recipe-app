// KH: tests for the amounts' display (D39, phase 3): fractions, the rounding of grams and millilitres with kg and l,
// halves of pieces with the egg tip, 3 TL as 1 EL, ranges and fixed amounts, each at the factors the spec names.
import { expect, test } from "vitest";
import {
  formatAmount,
  haveOnlyFactor,
  panFactor,
  parsePan,
  servingsFactor,
  timeHint,
  type KhAmount,
} from "../lib/amounts";

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
  expect(text({ quantity: 7.25, unit: g })).toBe("7,3");
  expect(text({ quantity: 45.6, unit: g })).toBe("46");
  expect(text({ quantity: 123, unit: g })).toBe("125");
  expect(text({ quantity: 503, unit: g })).toBe("500");
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
