// KH: tests for the shared list of destinations (D38): the bar at the bottom, Mealie's side menu and the More
// page read from one list, every destination has a real icon and text, and every path belongs to one tab.
import { describe, expect, test } from "vitest";
import {
  activeTab,
  barTargets,
  type KhNavTarget,
  moreSections,
  settingsTargets,
  sidebarTargets,
} from "../composables/use-kh-navigation";
import { icons } from "~/lib/icons";
import mealieTexts from "~/lang/messages/en-US.json";
import khTexts from "../../lang/en-US.json";
import khTextsDe from "../../lang/de-DE.json";

/** A text by its dotted key, from our texts or Mealie's. */
function text(key: string): unknown {
  const find = (messages: object) =>
    key.split(".").reduce<unknown>((node, part) => (node as Record<string, unknown> | undefined)?.[part], messages);
  return find(khTexts) ?? find(mealieTexts);
}

function everyTarget(): KhNavTarget[] {
  const { plan, collection } = moreSections("familie", "u1");
  const all = [...barTargets("familie"), ...sidebarTargets("familie"), ...plan, ...collection];
  all.push(...settingsTargets({ canOrganize: true, admin: true }));
  return all.flatMap(target => [target, ...(target.children ?? [])]);
}

describe("destinations", () => {
  test("the bar has recipes, intake, shopping list and more", () => {
    expect(barTargets("familie").map(target => [target.key, target.to])).toEqual([
      ["recipes", "/g/familie"],
      ["intake", "/g/familie/drafts"],
      ["shopping", "/shopping-lists"],
      ["more", "/g/familie/more"],
    ]);
  });

  test("the side menu shows the same destinations, without More", () => {
    const targets = sidebarTargets("familie");
    expect(targets.map(target => target.key)).toEqual(
      ["recipes", "intake", "shopping", "mealplan", "cookbooks", "finder", "organizers", "timeline"],
    );
    expect(targets.find(target => target.key === "organizers")?.children?.map(child => child.key))
      .toEqual(["categories", "tags", "tools"]);
  });

  test("More holds what the bar does not have", () => {
    const { plan, collection } = moreSections("familie", "u1");
    expect(plan.map(target => target.key)).toEqual(["mealplan", "cookbooks", "finder"]);
    expect(collection.map(target => target.key)).toEqual(["favorites", "categories", "tags", "tools", "timeline"]);
    expect(collection[0]!.to).toBe("/user/u1/favorites");
  });

  test("the settings follow the user's rights", () => {
    expect(settingsTargets({}).map(target => target.key)).toEqual(["profile"]);
    expect(settingsTargets({ canOrganize: true, admin: true }).map(target => target.key))
      .toEqual(["profile", "data", "admin"]);
  });

  test("every destination has one of Mealie's icons and a text", () => {
    for (const target of everyTarget()) {
      expect(icons, target.key).toHaveProperty(target.icon);
      expect(typeof text(target.title), target.title).toBe("string");
    }
  });
});

test("the hint on waiting drafts has a singular and a plural form in both languages", () => {
  for (const texts of [khTexts, khTextsDe]) {
    expect((texts.kh.nav as Record<string, string>)["drafts-waiting"]?.split(" | ")).toHaveLength(2);
  }
});

test("every path belongs to one tab of the bar", () => {
  expect(activeTab("/g/familie", "familie")).toBe("recipes");
  expect(activeTab("/g/familie/r/apfelkuchen", "familie")).toBe("recipes");
  expect(activeTab("/g/familie/drafts", "familie")).toBe("intake");
  expect(activeTab("/g/familie/drafts/123", "familie")).toBe("intake");
  expect(activeTab("/shopping-lists/abc", "familie")).toBe("shopping");
  expect(activeTab("/g/familie/more", "familie")).toBe("more");
  expect(activeTab("/g/familie/cookbooks/kuchen", "familie")).toBe("more");
  expect(activeTab("/household/mealplan/planner/view", "familie")).toBe("more");
  expect(activeTab("/user/profile", "familie")).toBe("more");
});
