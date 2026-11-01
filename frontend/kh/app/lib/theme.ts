// KH: the look's own colors and where the app asks for its theme colors (D38). Mealie lets browsers keep the answer
// for a week; the build id in the address makes every release ask once anew, so a new look shows right after an update.

/** The hint's surface and text as theme colors ("kh-hint" with variant "flat"), at least 4.5:1 in both themes. */
export const KH_HINT_COLORS = {
  light: { "kh-hint": "#E6F2EC", "on-kh-hint": "#256447" },
  dark: { "kh-hint": "#26352D", "on-kh-hint": "#4FB07E" }, // the dark accent at 16 % on Mealie's dark ground
};

/** The theme request of this build of the app. */
export function themeRequestUrl(buildId: string): string {
  return `/api/app/about/theme?build=${encodeURIComponent(buildId)}`;
}
