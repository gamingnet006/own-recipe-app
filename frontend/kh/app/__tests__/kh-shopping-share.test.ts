// KH: tests for the text of the shared shopping list (D56): unchecked items only, one per line, order kept.
import { expect, test } from "vitest";
import { shareText } from "../lib/shopping-share";

test("leaves out checked items and empty displays, keeps the order", () => {
  const items = [
    { display: "2 eggs", checked: false },
    { display: "milk", checked: true },
    { display: "", checked: false },
    { display: null, checked: false },
    { display: "1 kg flour", checked: false },
  ];
  expect(shareText(items)).toBe("2 eggs\n1 kg flour");
});

test("an empty list gives an empty text", () => {
  expect(shareText([])).toBe("");
});
