// KH: the destinations of Kochheft's navigation (D38) in one list. The bar at the bottom on phones, Mealie's
// side menu from 840 px and the More page all read from here, so a destination is added or renamed in one place.
import type { KhAddonFlags } from "../lib/addons";
import { WIZARD_PATH } from "../lib/setup-wizard";
import { khAddons } from "./use-kh-addons";
import { khSidebar } from "./use-kh-sidebar";

// The tile shopping page (D60); Mealie's own list pages stay as the classic view
const SHOPPING_PAGE = "/einkauf";
const CLASSIC_SHOPPING = "/shopping-lists";

export type KhNavKey = "recipes" | "intake" | "shopping" | "more" | "mealplan" | "cookbooks" | "finder" | "favorites"
  | "organizers" | "categories" | "tags" | "tools" | "timeline" | "duplicates" | "nutrition" | "tolerance" | "profile" | "data" | "admin" | "about" | "settings" | "system" | "addons" | "wizard" | "switch" | "households";

/** The side-menu entries a person may hide (D58), in the menu's order; the server holds the same keys
 * (mealie/kh/navigation/schemas.py). Recipes and More always stay. */
export const HIDEABLE_ENTRIES = ["intake", "shopping", "mealplan", "cookbooks", "finder", "organizers", "timeline"] as const;

// What the simple view (D79) keeps in the bar and the side menu; the rest stays reachable under More
const SIMPLE_MENU: readonly KhNavKey[] = ["recipes", "shopping", "mealplan", "more"];

export type MoreSection = "plan" | "collection" | "settings" | "help" | "account";

export type KhTab = "recipes" | "intake" | "shopping" | "mealplan" | "more";

// The planner page (D70, D76: its own tab in the bar)
const PLANNER_PAGE = "/household/mealplan";

export interface KhNavTarget {
  key: KhNavKey;
  to: string;
  /** Name of one of Mealie's icons ($globals.icons) */
  icon: string;
  /** Key of the text, ours or Mealie's */
  title: string;
  children?: KhNavTarget[];
}

type Targets = Record<Exclude<KhNavKey, "organizers">, KhNavTarget>;

/** Every destination, with the group's and the user's part of the path filled in. */
function allTargets(groupSlug: string, userId: string): Targets {
  const group = `/g/${groupSlug}`;
  const target = (key: KhNavKey, to: string, icon: string, title: string): KhNavTarget => ({ key, to, icon, title });
  return {
    recipes: target("recipes", group, "silverwareForkKnife", "general.recipes"),
    intake: target("intake", `${group}/drafts`, "import", "kh.nav.intake"),
    shopping: target("shopping", SHOPPING_PAGE, "formatListCheck", "kh.nav.shopping"),
    more: target("more", `${group}/more`, "dotsHorizontal", "kh.nav.more"),
    mealplan: target("mealplan", `${PLANNER_PAGE}/planner/view`, "calendarMultiselect", "kh.nav.mealplan"),
    cookbooks: target("cookbooks", `${group}/cookbooks`, "book", "cookbook.cookbooks"),
    finder: target("finder", `${group}/recipes/finder`, "search", "kh.nav.finder"),
    favorites: target("favorites", `/user/${userId}/favorites`, "heart", "general.favorites"),
    categories: target("categories", `${group}/recipes/categories`, "categories", "sidebar.categories"),
    tags: target("tags", `${group}/recipes/tags`, "tags", "sidebar.tags"),
    tools: target("tools", `${group}/recipes/tools`, "potSteam", "tool.tools"),
    timeline: target("timeline", `${group}/recipes/timeline`, "timelineText", "recipe.timeline"),
    duplicates: target("duplicates", `${group}/doppelte`, "duplicate", "kh.nav.duplicates"),
    nutrition: target("nutrition", `${group}/naehrwerte`, "foods", "kh.nav.nutrition"),
    tolerance: target("tolerance", `${group}/vertraeglichkeit`, "alertOutline", "kh.nav.tolerance"),
    settings: target("settings", `${group}/einstellungen`, "cog", "kh.nav.settings"),
    profile: target("profile", "/user/profile", "cog", "profile.user-settings"),
    data: target("data", "/group/data", "manageData", "data-pages.data-management"),
    admin: target("admin", "/admin/site-settings", "wrench", "settings.admin-settings"),
    about: target("about", `${group}/ueber`, "informationOutline", "kh.nav.about"),
    system: target("system", `${group}/systempruefung`, "clipboardCheck", "kh.nav.system"),
    addons: target("addons", `${group}/zusatzfunktionen`, "tools", "kh.nav.addons"),
    wizard: target("wizard", WIZARD_PATH, "autoFix", "kh.nav.wizard"), // D83: Mealie's setup wizard, opened again
    // not a page: the settings page opens a dialog for it
    switch: target("switch", `${group}/more`, "swapHorizontal", "kh.accounts.switch"),
    households: target("households", `${group}/haushalte`, "household", "kh.nav.households"),
  };
}

/**
 * The tabs of the bar at the bottom: recipes, intake, shopping list, week (the planner, D76) and More; a tab of a
 * switched-off add-on is missing, so the bar has three to five places; in the simple view (D79) the intake is left out
 * (it is under More). ON is the household's add-on switches (D46), by default the shared state; the next functions use
 * it alike.
 */
export function barTargets(
  groupSlug: string,
  on: KhAddonFlags = khAddons.enabled,
  simple: boolean = khSidebar.simple,
): KhNavTarget[] {
  const all = allTargets(groupSlug, "");
  const week = { ...all.mealplan, icon: "calendar", title: "kh.nav.week" };
  return [
    all.recipes,
    ...(simple ? [] : [all.intake]),
    ...(on.shopping ? [all.shopping] : []),
    ...(on.planner ? [week] : []),
    all.more,
  ];
}

/** Mealie's side menu from 840 px: the bar's destinations and More's, with the organizers grouped as in Mealie; More
 * itself comes last, because only there are the add-on pages and the oven, nutrition and clock settings (D51).
 * HIDDEN are the entries the person hid (D58); the simple view (D79) shows only the short list of the bar. */
export function sidebarTargets(
  groupSlug: string,
  on: KhAddonFlags = khAddons.enabled,
  hidden: readonly string[] = khSidebar.hidden,
  simple: boolean = khSidebar.simple,
): KhNavTarget[] {
  const all = allTargets(groupSlug, "");
  const organizers: KhNavTarget = {
    key: "organizers",
    to: all.categories.to,
    icon: "organizers",
    title: "general.organizers",
    children: [all.categories, all.tags, all.tools],
  };
  return [
    all.recipes,
    all.intake,
    ...(on.shopping ? [all.shopping] : []),
    ...(on.planner ? [all.mealplan] : []),
    all.cookbooks,
    all.finder,
    organizers,
    all.timeline,
    all.more,
  ].filter(target => (simple ? SIMPLE_MENU.includes(target.key) : !hidden.includes(target.key)));
}

/** The entries of the side menu a person can hide or show again, which the add-on switches leave in the menu. */
export function sidebarChoices(groupSlug: string, on: KhAddonFlags = khAddons.enabled): KhNavTarget[] {
  return sidebarTargets(groupSlug, on, [], false).filter(target => HIDEABLE_ENTRIES.some(key => key === target.key));
}

/** What the More page lists (D76): planning, the user's collection, the one row to the settings page and the help
 * pages (the tour, set-up and news rows are dialogs and pages of their own, only About is a destination). An intake or
 * shopping list missing from the side menu (hidden, D58, or left out by the simple view, D79) is listed under planning,
 * so it stays reachable on a wide screen. */
export function moreSections(
  groupSlug: string,
  userId: string,
  on: KhAddonFlags = khAddons.enabled,
  hidden: readonly string[] = khSidebar.hidden,
  simple: boolean = khSidebar.simple,
): { plan: KhNavTarget[]; collection: KhNavTarget[]; settings: KhNavTarget[]; help: KhNavTarget[] } {
  const all = allTargets(groupSlug, userId);
  const inMenu = (key: KhNavKey) => (simple ? SIMPLE_MENU.includes(key) : !hidden.includes(key));
  return {
    plan: [
      ...(inMenu("intake") ? [] : [all.intake]),
      ...(on.shopping && !inMenu("shopping") ? [all.shopping] : []),
      ...(on.planner ? [all.mealplan] : []),
      all.cookbooks,
      all.finder,
    ],
    collection: [
      all.favorites, all.categories, all.tags, all.tools, all.timeline,
      ...(on.duplicates ? [all.duplicates] : []),
      ...(on.nutrition ? [all.nutrition] : []),
      ...(on.allergens ? [all.tolerance] : []),
    ],
    settings: [all.settings],
    help: [all.about],
  };
}

/** The order of the More page's sections (D79): the simple view shows planning, help and the account first and folds
 * the collection and the settings row away behind "Show more"; otherwise all five show in the usual order. */
export function moreLayout(simple: boolean): { first: MoreSection[]; folded: MoreSection[] } {
  return simple
    ? { first: ["plan", "help", "account"], folded: ["collection", "settings"] }
    : { first: ["plan", "collection", "settings", "help", "account"], folded: [] };
}

/** The pages of the settings page (D76) this user may open, as in Mealie's side menu, plus our add-ons, the household
 * switch (only with linked accounts, D52), households and system check (admins). */
export function settingsTargets(
  user: { canOrganize?: boolean; admin?: boolean; linked?: boolean },
  groupSlug: string,
): KhNavTarget[] {
  const all = allTargets(groupSlug, "");
  return [
    all.profile,
    ...(user.canOrganize ? [all.data] : []),
    all.addons,
    ...(user.linked ? [all.switch] : []),
    ...(user.admin ? [all.admin, all.households, all.system, all.wizard] : []),
  ];
}

/** The tab of the bar a page belongs to; whatever is not recipes, intake, shopping list or week sits under More. */
export function activeTab(
  path: string,
  groupSlug: string,
  on: KhAddonFlags = khAddons.enabled,
  simple: boolean = khSidebar.simple,
): KhTab {
  const group = `/g/${groupSlug}`;
  const within = (base: string) => path === base || path.startsWith(`${base}/`);
  if (path === group || path === `${group}/` || path.startsWith(`${group}/r/`)) return "recipes";
  if (!simple && within(`${group}/drafts`)) return "intake"; // the simple view has no intake tab (D79)
  if (within(SHOPPING_PAGE) || within(CLASSIC_SHOPPING)) return "shopping";
  if (on.planner && within(PLANNER_PAGE)) return "mealplan";
  return "more";
}

/** Mealie's side menu: open while the screen is wide, also after an iPad is turned to landscape. */
export function useKhSidebar(wide: Ref<boolean>): Ref<boolean> {
  const open = ref(false);
  onMounted(() => {
    open.value = wide.value;
  });
  watch(wide, (value) => {
    open.value = value;
  });
  return open;
}
