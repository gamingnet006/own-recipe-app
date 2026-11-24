// KH: moving photos one place earlier or later, before sending or in the review.
import { describe, expect, test } from "vitest";
import { applyOrder, movedOrder } from "../lib/photo-order";

describe("movedOrder", () => {
  test("moves a photo one place earlier or later", () => {
    expect(movedOrder(3, 1, -1)).toEqual([1, 0, 2]);
    expect(movedOrder(3, 1, 1)).toEqual([0, 2, 1]);
  });

  test("the first cannot go earlier and the last not later", () => {
    expect(movedOrder(3, 0, -1)).toBeNull();
    expect(movedOrder(3, 2, 1)).toBeNull();
  });

  test("a place that does not exist moves nothing", () => {
    expect(movedOrder(3, 5, -1)).toBeNull();
    expect(movedOrder(1, 0, 1)).toBeNull();
  });
});

describe("applyOrder", () => {
  test("puts the items in the new order", () => {
    expect(applyOrder(["a", "b", "c"], movedOrder(3, 2, -1)!)).toEqual(["a", "c", "b"]);
  });
});
