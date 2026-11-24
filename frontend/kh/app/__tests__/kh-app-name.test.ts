// KH: tests for the app's name by language (key kh.app.name) and the rule that an own branding name is kept, and a
// guard that English texts never repeat the literal name (they link kh.app.name, so "Cookbook" shows in English).
import { describe, expect, test } from "vitest";
import de from "../../lang/de-DE.json";
import en from "../../lang/en-US.json";
import { appName } from "../lib/locale";

describe("appName", () => {
  test("the default name shows translated, an own branding name as it is", () => {
    expect(appName("Kochheft", "Cookbook")).toBe("Cookbook");
    expect(appName("Our Kitchen", "Cookbook")).toBe("Our Kitchen");
  });
});

test("the two languages name the app Kochheft and Cookbook", () => {
  expect(de.kh.app.name).toBe("Kochheft");
  expect(en.kh.app.name).toBe("Cookbook");
});

test("English texts use the name key, not the German name", () => {
  const allowed = ["Kochheft files"]; // the name of a file; the shortcuts are called "Import to Cookbook" etc. in English
  const literal = JSON.stringify(en)
    .split(/"[^"]*":/)
    .join("\n")
    .match(/[^\n]*Kochheft[^\n]*/g)
    ?.filter(text => !allowed.some(name => text.includes(name)) && text !== "\"Kochheft\"");
  expect(en.kh.app.name).not.toBe("Kochheft");
  expect(literal ?? []).toEqual([]);
});
