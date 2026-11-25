// KH: the recipes the AI was already asked about for tag suggestions, kept per group in this browser so a new visit
// does not ask them (and spend AI requests) again.
const key = (groupSlug: string) => `kh-tags-asked-${groupSlug}`;

/** The stored recipe ids of the group; empty when nothing is stored or the browser refuses storage. */
export function loadAsked(groupSlug: string): string[] {
  try {
    const stored = JSON.parse(localStorage.getItem(key(groupSlug)) ?? "[]");
    return Array.isArray(stored) ? stored.filter(id => typeof id === "string") : [];
  }
  catch {
    return [];
  }
}

/** Stores the ids; a browser without storage just forgets them. */
export function saveAsked(groupSlug: string, ids: string[]): void {
  try {
    localStorage.setItem(key(groupSlug), JSON.stringify(ids));
  }
  catch {
    // private window or blocked storage: the list then lasts only for this visit
  }
}

/** Forgets the list, so every recipe may be asked about again. */
export function clearAsked(groupSlug: string): void {
  try {
    localStorage.removeItem(key(groupSlug));
  }
  catch {
    // nothing stored, nothing to forget
  }
}
