// KH: tests for the season calendar (D80): months inside a range and over New Year, the food names sent to the
// server, and a calendar that is complete (every month has something, every item has valid months).
import { describe, expect, test } from "vitest";
import { inSeason, monthOf, SEASON, seasonTerms } from "../lib/season";

const names = (month: number) => inSeason(month).map(item => item.names[0]);

describe("inSeason", () => {
  test("a range inside the year", () => {
    expect(names(5)).toContain("Spargel");
    expect(names(7)).not.toContain("Spargel");
    expect(names(10)).toContain("Kürbis");
  });

  test("a range over New Year counts both ends", () => {
    for (const month of [11, 12, 1, 2]) expect(names(month)).toContain("Grünkohl");
    expect(names(6)).not.toContain("Grünkohl");
    expect(names(1)).toContain("Äpfel"); // storage apples
  });

  test("the calendar is valid and every month has something", () => {
    for (const item of SEASON) {
      expect(item.names.length).toBeGreaterThan(0);
      expect(item.from).toBeGreaterThanOrEqual(1);
      expect(item.to).toBeLessThanOrEqual(12);
    }
    for (let month = 1; month <= 12; month++) expect(inSeason(month).length).toBeGreaterThan(3);
  });
});

describe("seasonTerms", () => {
  test("lists plurals and spellings too", () => {
    const terms = seasonTerms(11);
    expect(terms).toEqual(expect.arrayContaining(["Kürbis", "Kürbisse", "Äpfel", "Apfel", "Rote Bete"]));
    expect(terms).not.toContain("Spargel");
  });
});

test("monthOf counts from 1", () => {
  expect(monthOf(new Date(2026, 0, 15))).toBe(1);
  expect(monthOf(new Date(2026, 11, 15))).toBe(12);
});
