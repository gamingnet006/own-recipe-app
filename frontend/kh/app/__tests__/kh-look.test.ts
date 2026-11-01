// KH: tests for the look (D38): every release asks for the theme colors anew, because Mealie lets browsers keep the
// answer for a week and a new look would otherwise show only days after an update.
import { expect, test } from "vitest";
import { themeRequestUrl } from "../lib/theme";

test("every build asks for the theme anew", () => {
  expect(themeRequestUrl("abc")).toBe("/api/app/about/theme?build=abc");
  expect(themeRequestUrl("abc")).not.toBe(themeRequestUrl("def"));
});
