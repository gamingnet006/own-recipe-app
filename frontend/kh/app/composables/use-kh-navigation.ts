// KH: the destinations of Küchenhelfer's navigation (D38) in one list. The bar at the bottom on phones, Mealie's
// side menu from 960 px and the More page all read from here, so a destination is added or renamed in one place.

export type KhNavKey = "recipes" | "intake" | "shopping" | "more" | "mealplan" | "cookbooks" | "finder" | "favorites"
  | "organizers" | "categories" | "tags" | "tools" | "timeline" | "profile" | "data" | "admin";

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

/** Every destination, with the group's and the user's part of the path filled in. */
function allTargets(groupSlug: string, userId: string): Targets {
  const group = `/g/${groupSlug}`;
  const target = (key: KhNavKey, to: string, icon: string, title: string): KhNavTarget => ({ key, to, icon, title });
  return {
    recipes: target("recipes", group, "silverwareForkKnife", "general.recipes"),
    intake: target("intake", `${group}/drafts`, "import", "kh.nav.intake"),
    shopping: target("shopping", "/shopping-lists", "formatListCheck", "kh.nav.shopping"),
    more: target("more", `${group}/more`, "dotsHorizontal", "kh.nav.more"),
    mealplan: target("mealplan", "/household/mealplan/planner/view", "calendarMultiselect", "meal-plan.meal-planner"),
    cookbooks: target("cookbooks", `${group}/cookbooks`, "book", "cookbook.cookbooks"),
    finder: target("finder", `${group}/recipes/finder`, "search", "kh.nav.finder"),
    favorites: target("favorites", `/user/${userId}/favorites`, "heart", "general.favorites"),
    categories: target("categories", `${group}/recipes/categories`, "categories", "sidebar.categories"),
    tags: target("tags", `${group}/recipes/tags`, "tags", "sidebar.tags"),
    tools: target("tools", `${group}/recipes/tools`, "potSteam", "tool.tools"),
    timeline: target("timeline", `${group}/recipes/timeline`, "timelineText", "recipe.timeline"),
    profile: target("profile", "/user/profile", "cog", "profile.user-settings"),
    data: target("data", "/group/data", "manageData", "data-pages.data-management"),
    admin: target("admin", "/admin/site-settings", "wrench", "settings.admin-settings"),
  };
}

/** The four tabs of the bar at the bottom. */
export function barTargets(groupSlug: string): KhNavTarget[] {
  const all = allTargets(groupSlug, "");
  return [all.recipes, all.intake, all.shopping, all.more];
}

/** Mealie's side menu from 960 px: the bar's destinations and More's, with the organizers grouped as in Mealie. */
export function sidebarTargets(groupSlug: string): KhNavTarget[] {
  const all = allTargets(groupSlug, "");
  const organizers: KhNavTarget = {
    key: "organizers",
    to: all.categories.to,
    icon: "organizers",
    title: "general.organizers",
    children: [all.categories, all.tags, all.tools],
  };
  return [all.recipes, all.intake, all.shopping, all.mealplan, all.cookbooks, all.finder, organizers, all.timeline];
}

/** What the More page lists besides the settings: planning, and the user's collection. */
export function moreSections(groupSlug: string, userId: string): { plan: KhNavTarget[]; collection: KhNavTarget[] } {
  const all = allTargets(groupSlug, userId);
  return {
    plan: [all.mealplan, all.cookbooks, all.finder],
    collection: [all.favorites, all.categories, all.tags, all.tools, all.timeline],
  };
}

/** The settings pages this user may open, as in Mealie's side menu. */
export function settingsTargets(user: { canOrganize?: boolean; admin?: boolean }): KhNavTarget[] {
  const all = allTargets("", "");
  return [all.profile, ...(user.canOrganize ? [all.data] : []), ...(user.admin ? [all.admin] : [])];
}

/** The tab of the bar a page belongs to; whatever is not recipes, intake or shopping list sits under More. */
export function activeTab(path: string, groupSlug: string): KhTab {
  const group = `/g/${groupSlug}`;
  const within = (base: string) => path === base || path.startsWith(`${base}/`);
  if (path === group || path === `${group}/` || path.startsWith(`${group}/r/`)) return "recipes";
  if (within(`${group}/drafts`)) return "intake";
  if (within("/shopping-lists")) return "shopping";
  return "more";
}
