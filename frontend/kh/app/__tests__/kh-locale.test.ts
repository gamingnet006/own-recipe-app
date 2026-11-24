// KH: tests for the language rules: account, then device, then installation, then English; only German and English.
import { describe, expect, test } from "vitest";
import { asKhLocale, chooseLocale, deviceLocale, KH_LOCALES } from "../lib/locale";

describe("deviceLocale", () => {
  test("takes the first German or English entry and ignores other languages before it", () => {
    expect(deviceLocale(["de-AT", "en"])).toBe("de-DE");
    expect(deviceLocale(["fr-FR", "en-GB"])).toBe("en-US");
    expect(deviceLocale(["EN-us"])).toBe("en-US");
  });

  test("is null for other languages or none", () => {
    expect(deviceLocale(["fr-FR", "es"])).toBeNull();
    expect(deviceLocale([])).toBeNull();
  });
});

describe("chooseLocale", () => {
  test("the account's choice beats everything", () => {
    expect(chooseLocale("en-US", "de-DE", "de-DE")).toBe("en-US");
  });

  test("without a choice the device follows, then the installation, then English", () => {
    expect(chooseLocale(null, "de-DE", "en-US")).toBe("de-DE");
    expect(chooseLocale(undefined, null, "de-DE")).toBe("de-DE");
    expect(chooseLocale(null, null, null)).toBe("en-US");
  });

  test("an unknown stored language is ignored", () => {
    expect(chooseLocale("fr-FR", "de-DE", null)).toBe("de-DE");
  });
});

test("the picker offers exactly Deutsch and English", () => {
  expect(KH_LOCALES.map(locale => locale.name)).toEqual(["Deutsch", "English"]);
  expect(asKhLocale("de-DE")).toBe("de-DE");
  expect(asKhLocale("zh-CN")).toBeNull();
});
