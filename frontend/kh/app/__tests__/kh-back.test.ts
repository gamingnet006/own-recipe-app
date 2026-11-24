// KH: tests for the back arrow of sub-pages (the installed app has no browser back): top-level pages and cook mode get
// none, every other page gets one that falls back to the tab it belongs to when there is no history.
import { describe, expect, test } from "vitest";
import { backTarget } from "../composables/use-kh-navigation";
import { DEFAULT_ADDONS } from "../lib/addons";

const back = (path: string, simple = false, cook = false) => backTarget(path, "familie", cook, DEFAULT_ADDONS, simple);

describe("backTarget", () => {
  test("the tabs of the bar and More itself get no arrow", () => {
    for (const path of ["/g/familie", "/g/familie/", "/g/familie/drafts", "/einkauf", "/household/mealplan/planner/view", "/g/familie/more"]) {
      expect(back(path), path).toBeNull();
    }
  });

  test("cook mode, the recipe page with its own arrow and shared recipes get none", () => {
    expect(back("/g/familie/r/apfelkuchen", false, true)).toBeNull();
    expect(back("/g/familie/r/apfelkuchen")).toBeNull();
    expect(back("/g/familie/shared/r/abc")).toBeNull();
  });

  test("pages reached from More fall back to More", () => {
    for (const path of ["/g/familie/einstellungen", "/g/familie/zusatzfunktionen", "/g/familie/haushalte", "/g/familie/systempruefung",
      "/g/familie/doppelte", "/g/familie/naehrwerte", "/g/familie/vertraeglichkeit", "/g/familie/ueber", "/mitteilungen", "/aufs-handy",
      "/user/profile", "/user/profile/edit", "/group/data/foods", "/admin/site-settings", "/g/familie/cookbooks", "/g/familie/recipes/tags"]) {
      expect(back(path), path).toBe("/g/familie/more");
    }
  });

  test("sub-pages of a tab fall back to that tab", () => {
    expect(back("/g/familie/drafts/abc")).toBe("/g/familie/drafts");
    expect(back("/shopping-lists/abc")).toBe("/einkauf");
    expect(back("/household/mealplan/planner/edit")).toBe("/household/mealplan/planner/view");
    expect(back("/g/familie/r/create/new")).toBe("/g/familie");
  });

  test("the simple view has no intake tab, so the intake page is a sub-page of More", () => {
    expect(back("/g/familie/drafts", true)).toBe("/g/familie/more");
  });
});
