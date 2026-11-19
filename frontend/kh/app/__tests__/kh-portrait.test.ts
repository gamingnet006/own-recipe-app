// KH: tests for the phone-landscape decision (D71).
import { describe, expect, test } from "vitest";
import { isPhone, isPhoneLandscape } from "../lib/portrait";

describe("isPhoneLandscape", () => {
  test("covers a phone held sideways, whichever way the screen is reported", () => {
    expect(isPhoneLandscape({ width: 390, height: 844 }, true, true)).toBe(true);
    expect(isPhoneLandscape({ width: 844, height: 390 }, true, true)).toBe(true);
  });

  test("leaves an upright phone alone", () => {
    expect(isPhoneLandscape({ width: 390, height: 844 }, true, false)).toBe(false);
  });

  test("never covers an iPad, also not in a narrow split view", () => {
    expect(isPhoneLandscape({ width: 1194, height: 834 }, true, true)).toBe(false);
    expect(isPhoneLandscape({ width: 744, height: 1133 }, true, true)).toBe(false);
  });

  test("never covers a computer with a mouse", () => {
    expect(isPhoneLandscape({ width: 400, height: 300 }, false, true)).toBe(false);
  });
});

describe("isPhone", () => {
  test("is true for a small touch screen only", () => {
    expect(isPhone({ width: 390, height: 844 }, true)).toBe(true);
    expect(isPhone({ width: 820, height: 1180 }, true)).toBe(false);
  });
});
