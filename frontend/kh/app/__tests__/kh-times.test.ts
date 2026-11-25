// KH: tests for the time recognition in step texts (D42, cook mode): numbers, combinations, ranges, number words,
// English units, and phrases without a fixed duration.
import { describe, expect, test } from "vitest";
import { parseTimes } from "../lib/times";

const one = (s: string) => {
  const t = parseTimes(s);
  expect(t).toHaveLength(1);
  return t[0]!;
};

describe("parseTimes", () => {
  test("numbers with units", () => {
    expect(one("10 Min. ruhen").seconds).toBe(600);
    expect(one("10 Minuten").seconds).toBe(600);
    expect(one("1 Std.").seconds).toBe(3600);
    expect(one("1,5 Stunden").seconds).toBe(5400);
    expect(one("1½ Stunden").seconds).toBe(5400);
    expect(one("45 Sek.").seconds).toBe(45);
  });
  test("combined is one timer", () => {
    expect(one("1 Std. 20 Min. backen").seconds).toBe(4800);
    expect(one("1 Stunde und 20 Minuten").seconds).toBe(4800);
  });
  test("ranges", () => {
    expect(one("20–30 Min.")).toMatchObject({ seconds: 1200, upperSeconds: 1800 });
    expect(one("20-30 Minuten")).toMatchObject({ seconds: 1200, upperSeconds: 1800 });
    expect(one("20 bis 30 Minuten")).toMatchObject({ seconds: 1200, upperSeconds: 1800 });
    expect(one("1–2 Std.")).toMatchObject({ seconds: 3600, upperSeconds: 7200 });
  });
  test("words", () => {
    expect(one("eine Minute").seconds).toBe(60);
    expect(one("eine halbe Stunde").seconds).toBe(1800);
    expect(one("eine Viertelstunde").seconds).toBe(900);
    expect(one("eine Dreiviertelstunde").seconds).toBe(2700);
    expect(one("anderthalb Stunden").seconds).toBe(5400);
    expect(one("zwölf Minuten").seconds).toBe(720);
  });
  test("english", () => {
    expect(one("10 minutes").seconds).toBe(600);
    expect(one("10 mins").seconds).toBe(600);
    expect(one("1 hr").seconds).toBe(3600);
    expect(one("1-2 hours")).toMatchObject({ seconds: 3600, upperSeconds: 7200 });
  });
  test("no fixed duration", () => {
    for (const s of ["über Nacht", "einige Stunden", "mehrere Minuten", "ein paar Minuten", "bei 180 °C", "200 g Mehl", "Minuten später"]) {
      expect(parseTimes(s)).toEqual([]);
    }
  });
  test("offsets cut the match from the text", () => {
    const s = "Dann 10 Min. ruhen und 1 Std. backen.";
    expect(parseTimes(s).map(t => s.slice(t.start, t.end))).toEqual(["10 Min.", "1 Std."]);
  });
});

test("a reversed range keeps only the lower end", () => {
  expect(parseTimes("30–20 Min.")[0]).toMatchObject({ seconds: 1800, upperSeconds: null });
});

test("written fractions and mixed numbers (v1.1)", () => {
  const minutes = (s: string) => parseTimes(s).map(t => t.seconds / 60);
  expect(minutes("1/2 Stunde backen")).toEqual([30]);
  expect(minutes("3/4 Std. ziehen lassen")).toEqual([45]);
  expect(minutes("1 1/2 Stunden schmoren")).toEqual([90]);
  expect(minutes("1 ½ Std. schmoren")).toEqual([90]);
  expect(minutes("1½ Stunden")).toEqual([90]);
  expect(parseTimes("1 1/2 Stunden schmoren")[0]!.text).toBe("1 1/2 Stunden");
  expect(minutes("20 Minuten")).toEqual([20]);
});

describe("English durations", () => {
  const seconds = (text: string) => parseTimes(text).map(time => [time.text, time.seconds, time.upperSeconds]);

  test("phrases without a number", () => {
    expect(seconds("Bake for half an hour.")).toEqual([["half an hour", 1800, null]]);
    expect(seconds("Rest an hour and a half.")).toEqual([["an hour and a half", 5400, null]]);
    expect(seconds("Chill a quarter of an hour.")).toEqual([["a quarter of an hour", 900, null]]);
    expect(seconds("three quarters of an hour")).toEqual([["three quarters of an hour", 2700, null]]);
  });

  test("number words and a range with to", () => {
    expect(seconds("Simmer for two hours")).toEqual([["two hours", 7200, null]]);
    expect(seconds("Fry one minute per side")).toEqual([["one minute", 60, null]]);
    expect(seconds("Boil 10 to 15 minutes")).toEqual([["10 to 15 minutes", 600, 900]]);
    expect(seconds("Cook for an hour")).toEqual([["an hour", 3600, null]]);
  });

  test("hours and minutes with and are one timer", () => {
    expect(seconds("1 hour and 20 minutes")).toEqual([["1 hour and 20 minutes", 4800, null]]);
  });

  test("a stray article is no duration", () => {
    expect(seconds("Add a pinch of salt")).toEqual([]);
  });
});
