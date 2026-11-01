// KH: where the app asks for its theme colors (D38). Mealie lets browsers keep the answer for a week; the build id in
// the address makes every release ask once anew, so a new look shows right after an update.

/** The theme request of this build of the app. */
export function themeRequestUrl(buildId: string): string {
  return `/api/app/about/theme?build=${encodeURIComponent(buildId)}`;
}
