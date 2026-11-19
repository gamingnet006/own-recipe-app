// KH: tests for the pure parts of "Woche vorschlagen" (D70).
import { describe, expect, test } from "vitest";
import { buildRows, dayLabel, daysWithoutDinner, entriesToCreate } from "../lib/week-suggestion";

const recipe = (id: string) => ({ id, slug: id, name: id, image: null });
const today = new Date(2026, 10, 19);
const days = [18, 19, 20, 21].map(day => new Date(2026, 10, day));

describe("daysWithoutDinner", () => {
  test("skips past days and days with a dinner, ignores other meals and week entries", () => {
    const meals = [
      { date: "2026-11-20", entryType: "dinner" },
      { date: "2026-11-19", entryType: "lunch" },
      { date: "2026-11-16", endDate: "2026-11-22", entryType: "dinner" },
    ];
    expect(daysWithoutDinner(days, meals, today)).toEqual(["2026-11-19", "2026-11-21"]);
  });
});

describe("buildRows", () => {
  test("pairs days with suggestions, ticked, and stops at the shorter list", () => {
    const rows = buildRows(["2026-11-19", "2026-11-20", "2026-11-21"], [recipe("a"), recipe("b")]);
    expect(rows.map(row => [row.date, row.recipe.id, row.checked])).toEqual([
      ["2026-11-19", "a", true],
      ["2026-11-20", "b", true],
    ]);
  });
});

describe("entriesToCreate", () => {
  test("makes dinner entries for the ticked rows only", () => {
    const rows = buildRows(["2026-11-19", "2026-11-20"], [recipe("a"), recipe("b")]);
    rows[0]!.checked = false;
    expect(entriesToCreate(rows)).toEqual([{ date: "2026-11-20", entryType: "dinner", recipeId: "b" }]);
  });
});

describe("dayLabel", () => {
  test("is short: weekday, day and month", () => {
    expect(dayLabel("2026-11-20", "de-DE")).toBe("Fr 20.11.");
    expect(dayLabel("2026-11-20", "en-US")).toBe("Fri 11/20");
  });
});
