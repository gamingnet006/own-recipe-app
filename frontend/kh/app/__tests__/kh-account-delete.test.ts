// KH: tests for the checks of deleting an account (D78).
import { describe, expect, test } from "vitest";
import { confirmMatches, heirOptions } from "../lib/account-delete";

describe("confirmMatches", () => {
  test("accepts the username in any case, with spaces around", () => {
    expect(confirmMatches("  Anna ", "anna")).toBe(true);
  });

  test("refuses other text and an empty name", () => {
    expect(confirmMatches("ann", "anna")).toBe(false);
    expect(confirmMatches("", "")).toBe(false);
  });
});

describe("heirOptions", () => {
  const users = [
    { id: "a", householdId: "h1" },
    { id: "b", householdId: "h1" },
    { id: "c", householdId: "h2" },
  ];

  test("lists the others of the same household only", () => {
    expect(heirOptions(users, "a").map(user => user.id)).toEqual(["b"]);
  });

  test("is empty for someone alone or unknown", () => {
    expect(heirOptions(users, "c")).toEqual([]);
    expect(heirOptions(users, "x")).toEqual([]);
  });
});
