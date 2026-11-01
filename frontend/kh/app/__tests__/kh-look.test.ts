// KH: tests for the look (D38): every release asks for the theme colors anew, because Mealie lets browsers keep the
// answer for a week and a new look would otherwise show only days after an update; and the hint stays readable.
import { expect, test } from "vitest";
import { KH_HINT_COLORS, themeRequestUrl } from "../lib/theme";

/** WCAG contrast ratio of two #RRGGBB colors. */
function contrast(first: string, second: string): number {
  const luminance = (hex: string) => {
    const [r, g, b] = [1, 3, 5].map((start) => {
      const channel = parseInt(hex.slice(start, start + 2), 16) / 255;
      return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
  };
  const [light, dark] = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (light! + 0.05) / (dark! + 0.05);
}

test("every build asks for the theme anew", () => {
  expect(themeRequestUrl("abc")).toBe("/api/app/about/theme?build=abc");
  expect(themeRequestUrl("abc")).not.toBe(themeRequestUrl("def"));
});

test("the hint's text reaches 4.5:1 on its surface in both themes", () => {
  expect(KH_HINT_COLORS.light).toEqual({ "kh-hint": "#E6F2EC", "on-kh-hint": "#256447" });
  for (const colors of [KH_HINT_COLORS.light, KH_HINT_COLORS.dark]) {
    expect(contrast(colors["kh-hint"], colors["on-kh-hint"])).toBeGreaterThanOrEqual(4.5);
  }
});
