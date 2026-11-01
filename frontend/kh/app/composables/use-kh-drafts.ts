// KH: the drafts UI's shared logic (phase 2): the API client, the drafts counter of the menu, reloading while
// a draft is recognized, and pure functions for redirects, layout, titles and texts, testable without Vue.
import { useRequests } from "~/composables/api/api-client";
import {
  KhDraftsApi,
  type KhDraft,
  type KhDraftWarning,
  type KhOrigin,
  type KhRecipeChanges,
  type KhRequestError,
} from "../lib/api/drafts";
import type { Recipe } from "~/lib/api/types/recipe";
import en from "../../lang/en-US.json";

type Translate = (key: string) => string;

// Mealie's import pages that the intake replaces, and the intake's old address from before it moved onto the drafts
// page (D38); typing a recipe yourself and the zip import stay
const REDIRECTED_TO_INTAKE = /^\/g\/([^/]+)\/(?:r\/create\/(?:url|ai|image|html|bulk)|drafts\/new)\/?$/;
// From this width (iPad upright) original and result stand side by side
const SIDE_BY_SIDE_FROM = 768;
// The list and the review look again this often while a draft is being recognized
const POLL_INTERVAL_MS = 3000;
// A draft without recipe and link is named by the start of its text, cut to this many characters
const TITLE_LENGTH = 60;
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

/** Runs LOAD now and again every few seconds while it answers true; stops for good when the page is left. */
export function useKhPolling(load: () => Promise<boolean>) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  let left = false;

  async function reload() {
    clearTimeout(timer);
    const again = await load();
    if (again && !left) timer = setTimeout(reload, POLL_INTERVAL_MS); // a load still running when the page is left must not start a new round
  }

  onMounted(reload);
  onBeforeUnmount(() => {
    left = true;
    clearTimeout(timer);
  });
  return { reload };
}

/** The intake for one of Mealie's import pages or the intake's old address, else null. */
export function importRedirectTarget(path: string): string | null {
  const match = REDIRECTED_TO_INTAKE.exec(path);
  return match ? `/g/${match[1]}/drafts` : null;
}

/** Original and result one below the other on a phone, side by side from tablet width. */
export function reviewLayout(width: number): "stacked" | "side" {
  return width >= SIDE_BY_SIDE_FROM ? "side" : "stacked";
}

/** The sentence for an error code from the API; codes this version does not know get the general one. */
export function errorText(code: string, t: Translate): string {
  return t(`kh.drafts.error.${ERROR_CODES.has(code) ? code : "unknown"}`);
}

/** The name of a draft in lists and headings: its recipe, else its link, else the start of its text. */
export function draftTitle(draft: KhDraft): string {
  if (draft.recipe?.name) return draft.recipe.name;
  if (draft.sourceUrl) return draft.sourceUrl.replace(/^https?:\/\/(?:www\.)?/, "");
  const firstLine = (draft.sourceText ?? "").trim().split("\n")[0] ?? "";
  return firstLine.length > TITLE_LENGTH ? `${firstLine.slice(0, TITLE_LENGTH)}…` : firstLine;
}

/** Whether a draft is still being recognized, so the page has to look again soon. */
export function pollingNeeded(list: KhDraft[]): boolean {
  return list.some(draft => draft.status === "working");
}

/** The review's fields start from what the recognition found: servings, yield amount and yield text. */
export function recipeChanges(recipe: Recipe | null): KhRecipeChanges {
  return {
    recipeServings: recipe?.recipeServings ?? 0,
    recipeYieldQuantity: recipe?.recipeYieldQuantity ?? 0,
    recipeYield: recipe?.recipeYield ?? "",
  };
}

/** Where approving leads: the saved recipe, in Mealie's edit mode for "Save and edit". */
export function approveTarget(slug: string, groupSlug: string, edit: boolean): string {
  return `/g/${groupSlug}/r/${slug}${edit ? "?edit=true" : ""}`;
}

/** Where a hint on a possible duplicate leads: the saved recipe, else the other draft. */
export function warningTarget(warning: KhDraftWarning, groupSlug: string): string {
  return warning.recipeSlug ? `/g/${groupSlug}/r/${warning.recipeSlug}` : `/g/${groupSlug}/drafts/${warning.draftId}`;
}

/** The detail of a failed drafts request, e.g. 409 with code "duplicates"; "offline" when the request never
 * reached the server, "unknown" when the answer has no code. */
export function requestError(error: unknown): KhRequestError {
  const failed = error as { isAxiosError?: boolean; response?: { data?: { detail?: unknown } } } | null;
  if (failed?.isAxiosError && !failed.response) return { code: "offline" };
  const detail = failed?.response?.data?.detail;
  const known = typeof detail === "object" && detail !== null && typeof (detail as KhRequestError).code === "string";
  return known ? detail as KhRequestError : { code: "unknown" };
}

/** "From a photo · 31.10.2026 · Alex"; the name is left out when the user no longer exists. */
export function originLabel(origin: KhOrigin, t: Translate, day: (value: Date) => string): string {
  return [t(`kh.drafts.origin.${origin.sourceType}`), day(new Date(origin.createdAt)), origin.userName]
    .filter(Boolean)
    .join(" · ");
}
