// KH: the drafts UI's shared logic (phase 2): the API client, the drafts counter of the menu, and pure
// functions for the import redirect, the review layout and the texts, so they can be tested without Vue.
import { useRequests } from "~/composables/api/api-client";
import { KhDraftsApi, type KhOrigin } from "../lib/api/drafts";
import en from "../../lang/en-US.json";

type Translate = (key: string) => string;

// Mealie's import pages that the intake replaces; typing a recipe yourself and the zip import stay
const REDIRECTED_IMPORT = /^\/g\/([^/]+)\/r\/create\/(?:url|ai|image|html|bulk)\/?$/;
// From this width (iPad upright) original and result stand side by side
const SIDE_BY_SIDE_FROM = 768;
const ERROR_CODES = new Set(Object.keys(en.kh.drafts.error));

// One counter for the menu and the drafts pages; the app runs without server rendering, so a module ref is shared state
const count = ref(0);

/** Mealie's API requests with the drafts routes. */
export function useKhDraftsApi(): KhDraftsApi {
  return new KhDraftsApi(useRequests());
}

/** The number of drafts not approved yet, for "Drafts (n)"; refresh() after every change to a draft. */
export function useKhDraftCount() {
  const api = useKhDraftsApi();

  async function refresh() {
    const { data } = await api.list();
    if (data) count.value = data.length; // if loading fails, the last number stays
  }

  return { count, refresh };
}

/** The intake for one of Mealie's import pages, else null. */
export function importRedirectTarget(path: string): string | null {
  const match = REDIRECTED_IMPORT.exec(path);
  return match ? `/g/${match[1]}/drafts/new` : null;
}

/** Original and result one below the other on a phone, side by side from tablet width. */
export function reviewLayout(width: number): "stacked" | "side" {
  return width >= SIDE_BY_SIDE_FROM ? "side" : "stacked";
}

/** The sentence for an error code from the API; codes this version does not know get the general one. */
export function errorText(code: string, t: Translate): string {
  return t(`kh.drafts.error.${ERROR_CODES.has(code) ? code : "unknown"}`);
}

/** "From a photo · 31.10.2026 · Alex"; the name is left out when the user no longer exists. */
export function originLabel(origin: KhOrigin, t: Translate, day: (value: Date) => string): string {
  return [t(`kh.drafts.origin.${origin.sourceType}`), day(new Date(origin.createdAt)), origin.userName]
    .filter(Boolean)
    .join(" · ");
}
