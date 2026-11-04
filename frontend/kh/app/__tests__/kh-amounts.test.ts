// KH: tests for the amounts' display (D39, phase 3): fractions, the rounding of grams and millilitres with kg and l,
// halves of pieces with the egg tip, 3 TL as 1 EL, ranges and fixed amounts, each at the factors the spec names.
import { expect, test } from "vitest";
import { formatAmount, type KhAmount } from "../lib/amounts";

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
