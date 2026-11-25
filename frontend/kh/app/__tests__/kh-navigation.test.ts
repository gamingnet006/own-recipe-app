// KH: tests for the shared list of destinations (D38): the bar at the bottom, Mealie's side menu and the More
// page read from one list, every destination has a real icon and text, and every path belongs to one tab.
import { flagsOfKind, type KhAccountKind } from "../lib/account-kind";
import { mount } from "@vue/test-utils";
import { describe, expect, test } from "vitest";
import { defineComponent, h, nextTick, ref, type Ref } from "vue";
import {
  activeTab,
  barTargets,
  type KhNavTarget,
  moreLayout,
  moreSections,
  settingsSections,
  sidebarChoices,
  sidebarTargets,
  useKhSidebar,
} from "../composables/use-kh-navigation";
import { DEFAULT_ADDONS } from "../lib/addons";
import { isCookScreen } from "../composables/use-kh-cook-screen";
import { firstDayOfWeek } from "../lib/week-start";
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
  const { plan, collection, settings, help } = moreSections("familie", "u1");
  const all = [...barTargets("familie"), ...sidebarTargets("familie"), ...plan,
    ...collection, ...settings, ...help];
  all.push(...Object.values(settingsSections({ canOrganize: true, admin: true, linked: true }, "familie")).flat());
  return all.flatMap(target => [target, ...(target.children ?? [])]);
}

describe("destinations", () => {
  test("the bar has recipes, intake, shopping list, week and more (D76)", () => {
    expect(barTargets("familie").map(target => [target.key, target.to, target.title])).toEqual([
      ["recipes", "/g/familie", "general.recipes"],
      ["intake", "/g/familie/drafts", "kh.nav.intake"],
      ["shopping", "/einkauf", "kh.nav.shopping"],
      ["mealplan", "/household/mealplan/planner/view", "kh.nav.week"],
      ["more", "/g/familie/more", "kh.nav.more"],
    ]);
  });

  test("the side menu shows the same destinations, and More last for the rest (D51)", () => {
    const targets = sidebarTargets("familie");
    expect(targets.find(target => target.key === "shopping")?.to).toBe("/einkauf");
    expect(targets.map(target => target.key)).toEqual(
      ["recipes", "intake", "shopping", "mealplan", "cookbooks", "finder", "organizers", "timeline", "more"],
    );
    expect(targets.find(target => target.key === "organizers")?.children?.map(child => child.key))
      .toEqual(["categories", "tags", "tools"]);
  });

  test("More has one row to the settings and About under help (D76)", () => {
    const { settings, help } = moreSections("familie", "u1");
    expect(settings.map(target => [target.key, target.to])).toEqual([["settings", "/g/familie/einstellungen"]]);
    expect(help.map(target => [target.key, target.to])).toEqual([["about", "/g/familie/ueber"]]);
  });

  test("More holds what the bar does not have", () => {
    const { plan, collection } = moreSections("familie", "u1");
    expect(plan.map(target => target.key)).toEqual(["mealplan", "cookbooks", "finder"]);
    expect(collection.map(target => target.key)).toEqual(["favorites", "categories", "tags", "tools", "timeline", "duplicates", "nutrition", "tolerance"]);
    expect(collection[0]!.to).toBe("/user/u1/favorites");
  });

  test("the settings page lists what each person may open (wave 2)", () => {
    const keys = (user: Parameters<typeof settingsSections>[0], on = DEFAULT_ADDONS) =>
      Object.fromEntries(Object.entries(settingsSections(user, "familie", on)).map(([part, list]) => [part, list.map(target => target.key)]));
    expect(keys({})).toEqual({ me: ["profileEdit", "tolerance", "notifications"], device: ["setup"], family: [], advanced: [] });
    expect(keys({ canOrganize: true })).toMatchObject({ family: [], advanced: ["data"] });
    expect(keys({ canInvite: true }).family).toEqual(["invite"]);
    expect(keys({ canOrganize: true, admin: true, linked: true })).toEqual({
      me: ["profileEdit", "tolerance", "notifications", "switch"],
      device: ["setup"],
      family: ["people", "household", "invite", "addons", "households", "system", "wizard"],
      advanced: ["data", "profile", "admin"],
    });
    expect(keys({}, { ...DEFAULT_ADDONS, allergens: false }).me).not.toContain("tolerance");
  });

  test("each account kind finds Mealie's household and hub pages it needs", () => {
    const flags = (kind: KhAccountKind) => ({ ...flagsOfKind(kind), linked: false });
    const rows = (kind: KhAccountKind) => {
      const { family, advanced } = settingsSections(flags(kind), "familie");
      return [family.map(target => target.key), advanced.map(target => target.key)];
    };
    expect(rows("family")).toEqual([[], ["data"]]);
    expect(rows("manager")).toEqual([["household", "invite"], ["data"]]);
    expect(rows("admin")).toEqual([["people", "household", "invite", "addons", "households", "system", "wizard"], ["data", "profile", "admin"]]);
    // an account with its own selection: group management or "advanced" (API tokens) needs the hub
    expect(settingsSections({ canManage: true }, "familie").advanced.map(target => target.key)).toEqual(["profile"]);
    expect(settingsSections({ advanced: true }, "familie").advanced.map(target => target.key)).toEqual(["profile"]);
  });

  test("Mealie's profile hub and administration are linked for admins only", () => {
    const advanced = (admin: boolean) => settingsSections({ admin }, "familie").advanced.map(target => target.to);
    expect(advanced(true)).toEqual(["/user/profile", "/admin/site-settings"]);
    expect(advanced(false)).toEqual([]);
    expect(settingsSections({ admin: true }, "familie").family.map(target => target.to).slice(-3))
      .toEqual(["/g/familie/haushalte", "/g/familie/systempruefung", "/admin/setup"]);
  });

  test("switched-off add-ons leave the bar, the side menu and More (D46)", () => {
    const off = { ...DEFAULT_ADDONS, shopping: false, planner: false, duplicates: false, nutrition: false, allergens: false };
    expect(barTargets("familie", off).map(target => target.key)).toEqual(["recipes", "intake", "more"]);
    expect(barTargets("familie", { ...DEFAULT_ADDONS, planner: false }).map(target => target.key))
      .toEqual(["recipes", "intake", "shopping", "more"]); // the planner off leaves the bar at four
    expect(sidebarTargets("familie", off).map(target => target.key))
      .toEqual(["recipes", "intake", "cookbooks", "finder", "organizers", "timeline", "more"]);
    const { plan, collection } = moreSections("familie", "u1", off);
    expect(plan.map(target => target.key)).toEqual(["cookbooks", "finder"]);
    expect(collection.map(target => target.key)).toEqual(["favorites", "categories", "tags", "tools", "timeline"]);
  });

  test("the planner stays without the shopping list", () => {
    const off = { ...DEFAULT_ADDONS, shopping: false };
    expect(sidebarTargets("familie", off).map(target => target.key)).toContain("mealplan");
    expect(moreSections("familie", "u1", off).plan.map(target => target.key)).toContain("mealplan");
  });

  test("hidden entries leave the side menu, recipes and More stay (D58)", () => {
    const keys = (hidden: string[]) => sidebarTargets("familie", DEFAULT_ADDONS, hidden).map(target => target.key);
    expect(keys([])).toHaveLength(9);
    expect(keys(["finder", "organizers", "timeline"])).toEqual(["recipes", "intake", "shopping", "mealplan", "cookbooks", "more"]);
    expect(keys(["recipes", "more"])).toHaveLength(7); // hidden keys are filtered as given; the server never stores these two
  });

  test("the choices are the entries the side menu can show, also the ones hidden now", () => {
    expect(sidebarChoices("familie", DEFAULT_ADDONS).map(target => target.key))
      .toEqual(["intake", "shopping", "mealplan", "cookbooks", "finder", "organizers", "timeline"]);
    const off = { ...DEFAULT_ADDONS, shopping: false, planner: false };
    expect(sidebarChoices("familie", off).map(target => target.key))
      .toEqual(["intake", "cookbooks", "finder", "organizers", "timeline"]);
  });

  test("an intake or shopping list hidden from the side menu is listed under More", () => {
    const { plan } = moreSections("familie", "u1", DEFAULT_ADDONS, ["intake", "shopping", "finder"]);
    expect(plan.map(target => [target.key, target.to])).toEqual([
      ["intake", "/g/familie/drafts"],
      ["shopping", "/einkauf"],
      ["mealplan", "/household/mealplan/planner/view"],
      ["cookbooks", "/g/familie/cookbooks"],
      ["finder", "/g/familie/recipes/finder"],
    ]);
    expect(moreSections("familie", "u1", { ...DEFAULT_ADDONS, shopping: false }, ["shopping"]).plan.map(target => target.key))
      .not.toContain("shopping");
  });

  test("the simple view keeps recipes, shopping list, week and More, and nothing becomes unreachable (D79)", () => {
    const keys = (targets: KhNavTarget[]) => targets.map(target => target.key);
    expect(keys(barTargets("familie", DEFAULT_ADDONS, true))).toEqual(["recipes", "shopping", "mealplan", "more"]);
    expect(keys(sidebarTargets("familie", DEFAULT_ADDONS, ["shopping"], true))).toEqual(["recipes", "shopping", "mealplan", "more"]);
    const off = { ...DEFAULT_ADDONS, shopping: false, planner: false };
    expect(keys(barTargets("familie", off, true))).toEqual(["recipes", "more"]);
    const more = moreSections("familie", "u1", DEFAULT_ADDONS, ["shopping"], true);
    expect(keys(more.plan)).toEqual(["intake", "mealplan", "cookbooks", "finder"]); // the intake moves here
    expect(keys(more.collection)).toContain("timeline");
  });

  test("the simple view's More shows planning, settings, help and account first and folds the collection (D79)", () => {
    expect(moreLayout(true)).toEqual({ first: ["plan", "settings", "help", "account"], folded: ["collection"] });
    expect(moreLayout(false).folded).toEqual([]);
    expect(moreLayout(false).first).toHaveLength(5);
  });

  test("no intake tab in the simple view: its pages count as More (D79)", () => {
    expect(activeTab("/g/familie/drafts", "familie", DEFAULT_ADDONS, false)).toBe("intake");
    expect(activeTab("/g/familie/drafts", "familie", DEFAULT_ADDONS, true)).toBe("more");
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

test("the More page names no Mealie version, which reads \"develop\" in Kochheft's builds", () => {
  for (const texts of [khTexts, khTextsDe]) {
    expect(texts.kh.nav["based-on-mealie"]).not.toContain("{");
  }
});

describe("side menu", () => {
  function mountLayout(wide: Ref<boolean>): Ref<boolean> {
    let open: Ref<boolean> | undefined;
    mount(defineComponent({
      setup() {
        open = useKhSidebar(wide);
        return () => h("div");
      },
    }));
    return open!;
  }

  test("starts open on a wide screen and closed on a narrow one", () => {
    expect(mountLayout(ref(true)).value).toBe(true);
    expect(mountLayout(ref(false)).value).toBe(false);
  });

  test("opens when the screen turns wide, e.g. an iPad turned to landscape", async () => {
    const wide = ref(false);
    const open = mountLayout(wide);
    wide.value = true;
    await nextTick();
    expect(open.value).toBe(true);
  });
});

test("every path belongs to one tab of the bar", () => {
  expect(activeTab("/g/familie", "familie")).toBe("recipes");
  expect(activeTab("/g/familie/r/apfelkuchen", "familie")).toBe("recipes");
  expect(activeTab("/g/familie/drafts", "familie")).toBe("intake");
  expect(activeTab("/g/familie/drafts/123", "familie")).toBe("intake");
  expect(activeTab("/einkauf", "familie")).toBe("shopping");
  expect(activeTab("/shopping-lists/abc", "familie")).toBe("shopping"); // the classic view
  expect(activeTab("/g/familie/more", "familie")).toBe("more");
  expect(activeTab("/g/familie/cookbooks/kuchen", "familie")).toBe("more");
  expect(activeTab("/household/mealplan/planner/view", "familie")).toBe("mealplan");
  expect(activeTab("/household/mealplan/planner/view", "familie", { ...DEFAULT_ADDONS, planner: false })).toBe("more");
  expect(activeTab("/user/profile", "familie")).toBe("more");
});
test("cook mode takes the whole screen only with cook=true in the address (D76)", () => {
  expect(isCookScreen({ cook: "true" })).toBe(true);
  expect(isCookScreen({ cook: "false" })).toBe(false);
  expect(isCookScreen({})).toBe(false);
});
test("the week starts on Monday in German homes that never chose a day, else as chosen (D76)", () => {
  expect(firstDayOfWeek(0, "de-DE")).toBe(1);
  expect(firstDayOfWeek(undefined, "de-DE")).toBe(1);
  expect(firstDayOfWeek(3, "de-DE")).toBe(3);
  expect(firstDayOfWeek(0, "en-US")).toBe(0);
});
test("the destinations' new names read the same in both languages (D76)", () => {
  expect(khTextsDe.kh.nav.mealplan).toBe("Essensplan");
  for (const texts of [khTexts, khTextsDe]) {
    for (const key of ["mealplan", "week", "settings", "help", "account"]) {
      expect((texts.kh.nav as Record<string, string>)[key], key).toBeTruthy();
    }
  }
});
