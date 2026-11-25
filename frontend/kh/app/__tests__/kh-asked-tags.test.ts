// KH: tests for the list of recipes already asked about for tag suggestions.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { clearAsked, loadAsked, saveAsked } from "../lib/asked-tags";

describe("asked tags", () => {
  beforeEach(() => localStorage.clear());

  it("keeps the ids per group", () => {
    saveAsked("home", ["a", "b"]);
    expect(loadAsked("home")).toEqual(["a", "b"]);
    expect(loadAsked("other")).toEqual([]);
  });

  it("forgets them on request", () => {
    saveAsked("home", ["a"]);
    clearAsked("home");
    expect(loadAsked("home")).toEqual([]);
  });

  it("ignores stored rubbish", () => {
    localStorage.setItem("kh-tags-asked-home", "{not json");
    expect(loadAsked("home")).toEqual([]);
    localStorage.setItem("kh-tags-asked-home", JSON.stringify({ a: 1 }));
    expect(loadAsked("home")).toEqual([]);
  });

  it("works without storage", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(loadAsked("home")).toEqual([]);
    expect(() => saveAsked("home", ["a"])).not.toThrow();
    vi.restoreAllMocks();
  });
});
