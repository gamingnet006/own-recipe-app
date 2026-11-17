// KH: the destinations of Kochheft's navigation (D38) in one list. The bar at the bottom on phones, Mealie's
// side menu from 840 px and the More page all read from here, so a destination is added or renamed in one place.
import type { KhAddonFlags } from "../lib/addons";
import { khAddons } from "./use-kh-addons";
import { useUserApi } from "~/composables/api";
import { useLoggedInState } from "~/composables/use-logged-in-state";

const SHOPPING_LISTS = "/shopping-lists";

export type KhNavKey = "recipes" | "intake" | "shopping" | "more" | "mealplan" | "cookbooks" | "finder" | "favorites"
  | "organizers" | "categories" | "tags" | "tools" | "timeline" | "duplicates" | "nutrition" | "tolerance" | "profile" | "data" | "admin" | "about" | "system" | "addons" | "switch" | "households";

export type KhTab = "recipes" | "intake" | "shopping" | "more";

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

/** Every destination, with the group's and the user's part of the path and the shopping list filled in. */
function allTargets(groupSlug: string, userId: string, shoppingTo = SHOPPING_LISTS): Targets {
  const group = `/g/${groupSlug}`;
  const target = (key: KhNavKey, to: string, icon: string, title: string): KhNavTarget => ({ key, to, icon, title });
  return {
    recipes: target("recipes", group, "silverwareForkKnife", "general.recipes"),
    intake: target("intake", `${group}/drafts`, "import", "kh.nav.intake"),
    shopping: target("shopping", shoppingTo, "formatListCheck", "kh.nav.shopping"),
    more: target("more", `${group}/more`, "dotsHorizontal", "kh.nav.more"),
    mealplan: target("mealplan", "/household/mealplan/planner/view", "calendarMultiselect", "meal-plan.meal-planner"),
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
    profile: target("profile", "/user/profile", "cog", "profile.user-settings"),
    data: target("data", "/group/data", "manageData", "data-pages.data-management"),
    admin: target("admin", "/admin/site-settings", "wrench", "settings.admin-settings"),
    about: target("about", `${group}/ueber`, "informationOutline", "kh.nav.about"),
    system: target("system", `${group}/systempruefung`, "clipboardCheck", "kh.nav.system"),
    addons: target("addons", `${group}/zusatzfunktionen`, "tools", "kh.nav.addons"),
    // not a page: the More page opens a dialog for it
    switch: target("switch", `${group}/more`, "swapHorizontal", "kh.accounts.switch"),
    households: target("households", `${group}/haushalte`, "household", "kh.nav.households"),
  };
}

/**
 * The tabs of the bar at the bottom (without the shopping list, while that is switched off, three); SHOPPING_TO from
 * useKhShoppingTarget. ON is the household's add-on switches (D46), by default the shared state; the next functions use it alike.
 */
export function barTargets(groupSlug: string, shoppingTo: string, on: KhAddonFlags = khAddons.enabled): KhNavTarget[] {
  const all = allTargets(groupSlug, "", shoppingTo);
  return [all.recipes, all.intake, ...(on.shopping ? [all.shopping] : []), all.more];
}

/** Mealie's side menu from 840 px: the bar's destinations and More's, with the organizers grouped as in Mealie; More
 * itself comes last, because only there are the add-on pages and the oven, nutrition and clock settings (D51). */
export function sidebarTargets(groupSlug: string, shoppingTo: string, on: KhAddonFlags = khAddons.enabled): KhNavTarget[] {
  const all = allTargets(groupSlug, "", shoppingTo);
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
  ];
}

/** What the More page lists besides the settings: planning, and the user's collection. */
export function moreSections(
  groupSlug: string,
  userId: string,
  on: KhAddonFlags = khAddons.enabled,
): { plan: KhNavTarget[]; collection: KhNavTarget[] } {
  const all = allTargets(groupSlug, userId);
  return {
    plan: [...(on.planner ? [all.mealplan] : []), all.cookbooks, all.finder],
    collection: [
      all.favorites, all.categories, all.tags, all.tools, all.timeline,
      ...(on.duplicates ? [all.duplicates] : []),
      ...(on.nutrition ? [all.nutrition] : []),
      ...(on.allergens ? [all.tolerance] : []),
    ],
  };
}

/** The settings pages this user may open, as in Mealie's side menu, plus our add-ons, the household switch (only with
 * linked accounts, D52), households and system check (admins) and About. */
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
    ...(user.admin ? [all.admin, all.households, all.system] : []),
    all.about,
  ];
}

/** The tab of the bar a page belongs to; whatever is not recipes, intake or shopping list sits under More. */
export function activeTab(path: string, groupSlug: string): KhTab {
  const group = `/g/${groupSlug}`;
  const within = (base: string) => path === base || path.startsWith(`${base}/`);
  if (path === group || path === `${group}/` || path.startsWith(`${group}/r/`)) return "recipes";
  if (within(`${group}/drafts`)) return "intake";
  if (within(SHOPPING_LISTS)) return "shopping";
  return "more";
}

/** The household's only shopping list, else Mealie's overview of all lists. */
export function shoppingTarget(listIds: string[]): string {
  return listIds.length === 1 ? `${SHOPPING_LISTS}/${listIds[0]}` : SHOPPING_LISTS;
}

/**
 * Where the shopping list tab leads, from every list of the household; Mealie's overview until they are loaded, when
 * they can't be and for visitors. Mealie's own redirect counts only the user's lists, so the others would land on
 * "no lists".
 */
export function useKhShoppingTarget(): Ref<string> {
  const target = ref(SHOPPING_LISTS);
  if (!useLoggedInState().loggedIn.value) return target;
  // ponytail: loaded once per mount of the bar or side menu; a list made or deleted later counts after a reload
  useUserApi().shopping.lists.getAll(1, -1).then(({ data }) => {
    if (data) target.value = shoppingTarget(data.items.map(list => list.id));
  });
  return target;
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
