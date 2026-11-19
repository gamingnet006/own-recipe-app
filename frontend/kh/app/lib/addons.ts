// KH: the rules of the add-ons page (D46) without any screen: the switches, the presets of the two big areas, which
// rows are locked, and which pages go back to the recipes while their add-on is off.

export const ADDON_NAMES = [
  "shopping", "planner", "books", "duplicates", "oven", "nutrition", "allergens", "substitutions", "offline", "clock",
  "shareLinks", "telegram", "whisper", "voice", "season",
] as const;
export type KhAddonName = typeof ADDON_NAMES[number];
export type KhAddonFlags = Record<KhAddonName, boolean>;

/** The answer of GET /api/kh/addons: what the admin chose, what is in force, and what the host does not offer. */
export interface KhAddonsAnswer {
  flags: KhAddonFlags;
  enabled: KhAddonFlags;
  unavailable: KhAddonName[];
}

/** The fresh-install defaults (mealie/kh/addons/schemas.py); they also apply until the answer has arrived. */
export const DEFAULT_ADDONS: KhAddonFlags = {
  shopping: true, planner: true, books: true, duplicates: true, oven: true, nutrition: true, allergens: true,
  substitutions: true, offline: true, clock: true, shareLinks: false, telegram: false, whisper: false, voice: false, season: false,
};

/** The two big areas, which the presets and the first-start question set. */
export type KhPreset = "recipes" | "shopping" | "planner";
const PRESETS: Record<KhPreset, Pick<KhAddonFlags, "shopping" | "planner">> = {
  recipes: { shopping: false, planner: false },
  shopping: { shopping: true, planner: false },
  planner: { shopping: true, planner: true },
};

/** FLAGS with only the two big switches set as the preset says. */
export function applyPreset(flags: KhAddonFlags, preset: KhPreset): KhAddonFlags {
  return { ...flags, ...PRESETS[preset] };
}

/** The preset the two big switches show; null for the mix "planner without shopping list". */
export function currentPreset(flags: KhAddonFlags): KhPreset | null {
  return (Object.keys(PRESETS) as KhPreset[]).find(
    preset => PRESETS[preset].shopping === flags.shopping && PRESETS[preset].planner === flags.planner,
  ) ?? null;
}

export interface KhRowState {
  on: boolean;
  disabled: boolean;
  reason: "unavailable" | "needs-allergens" | null;
}

/** How a row of the page looks: add-ons the host does not offer are locked off, exchange needs allergens. */
export function rowState(name: KhAddonName, flags: KhAddonFlags, unavailable: string[]): KhRowState {
  if (unavailable.includes(name)) return { on: false, disabled: true, reason: "unavailable" };
  if (name === "substitutions" && !flags.allergens) return { on: false, disabled: true, reason: "needs-allergens" };
  return { on: flags[name], disabled: false, reason: null };
}

// The pages (by their start of the path) that belong to an add-on
const GROUP_PAGES: [RegExp, KhAddonName][] = [
  [/^\/g\/[^/]+\/kochbuch(\/|$)/, "books"],
  [/^\/g\/[^/]+\/doppelte(\/|$)/, "duplicates"],
  [/^\/g\/[^/]+\/naehrwerte(\/|$)/, "nutrition"],
  [/^\/g\/[^/]+\/vertraeglichkeit(\/|$)/, "allergens"],
  [/^\/(shopping-lists|einkauf)(\/|$)/, "shopping"], // KH: the tile page (D60) and Mealie's classic view
  [/^\/household\/mealplan(\/|$)/, "planner"],
];

/** Where a page of a switched-off add-on goes instead (the recipes of the group), with the add-on's name for the hint. */
export function addonRedirect(path: string, enabled: KhAddonFlags, groupSlug: string): { to: string; addon: KhAddonName } | null {
  const hit = GROUP_PAGES.find(([pattern, addon]) => pattern.test(path) && !enabled[addon]);
  return hit ? { to: `/g/${groupSlug}`, addon: hit[1] } : null;
}
