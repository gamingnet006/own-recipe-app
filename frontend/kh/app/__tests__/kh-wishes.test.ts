// KH: tests for the pure parts of the wish list (D72) and the shared week (D73).
import { describe, expect, test } from "vitest";
import { dayChips, dayLabel } from "../lib/week-days";
import { weekText } from "../lib/week-text";
import { isWishedBy, joinNames, wishers } from "../lib/wishes";

const wish = { people: [{ id: "a", name: "Anna" }, { id: "o", name: "Opa" }, { id: "m", name: "Mama" }] };

describe("wishers", () => {
  test("puts the signed-in person first as 'Du'", () => {
    expect(wishers(wish, "o", "Du")).toEqual(["Du", "Anna", "Mama"]);
    expect(wishers(wish, undefined, "Du")).toEqual(["Anna", "Opa", "Mama"]);
  });
});

describe("joinNames", () => {
  test("reads like speech", () => {
    expect(joinNames(["Anna"], "und")).toBe("Anna");
    expect(joinNames(["Anna", "Opa"], "und")).toBe("Anna und Opa");
    expect(joinNames(["Anna", "Opa", "Mama"], "und")).toBe("Anna, Opa und Mama");
  });
});

describe("isWishedBy", () => {
  test("knows own wishes", () => {
    expect(isWishedBy(wish, "a")).toBe(true);
    expect(isWishedBy(wish, "x")).toBe(false);
    expect(isWishedBy(undefined, "a")).toBe(false);
  });
});

describe("day labels", () => {
  const monday = new Date(2026, 10, 23);
  test("name the weekday and the date", () => {
    expect(dayLabel(monday, "de-DE")).toBe("Mo 23.");
    expect(dayLabel(monday, "de-DE", true)).toBe("Mo 23.11.");
  });

  test("chips skip days in the past", () => {
    const chips = dayChips([new Date(2026, 10, 22), monday, new Date(2026, 10, 24)], "de-DE", monday);
    expect(chips).toEqual([{ date: "2026-11-23", label: "Mo 23." }, { date: "2026-11-24", label: "Di 24." }]);
  });
});

describe("weekText", () => {
  test("lists days with entries, joined, with title and address", () => {
    const days = [
      { date: new Date(2026, 10, 23), meals: [{ recipe: { name: "Lasagne" } }, { title: "Salat" }] },
      { date: new Date(2026, 10, 24), meals: [] },
      { date: new Date(2026, 10, 25), meals: [{ title: "", recipe: null }, { recipe: { name: "Suppe" } }] },
    ];
    expect(weekText(days, "Essen diese Woche", "https://k.example", "de-DE")).toBe(
      "Essen diese Woche\n\nMo 23.11.: Lasagne · Salat\nMi 25.11.: Suppe\n\nhttps://k.example",
    );
  });

  test("is empty when nothing is planned", () => {
    expect(weekText([{ date: new Date(2026, 10, 23), meals: [] }], "T", "o", "de-DE")).toBe("");
  });
});
