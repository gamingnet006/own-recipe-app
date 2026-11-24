// KH: the drafts UI's shared logic (phase 2): the API client, the drafts counter of the menu, reloading while
// a draft is recognized, and pure functions for redirects, layout, titles and texts, testable without Vue.
import { useRequests } from "~/composables/api/api-client";
import {
  KhDraftsApi,
  type KhDraft,
  type KhDraftWarning,
  type KhFileImport,
  type KhOrigin,
  type KhRecipeChanges,
  type KhRequestError,
} from "../lib/api/drafts";
import type { RecipeOut } from "~/lib/api/types/recipe";
import type { KhDraftAmounts } from "../lib/api/amounts";
import { recognizedTags } from "../lib/draft-tags";
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
// Links to these sites (and their subdomains) are never fetched (D5); the backend keeps the same list in
// mealie/kh/drafts/video.py
const VIDEO_HOSTS = ["instagram.com", "tiktok.com", "youtube.com", "youtu.be", "facebook.com", "fb.watch"];
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
    if (data) count.value = waitingCount(data); // if loading fails, the last number stays
  }

  return { count, refresh };
}

/** The drafts the badge counts: the ones that wait for a review. A failed draft needs no review (D76), so it stays out. */
export function waitingCount(list: KhDraft[]): number {
  return list.filter(draft => draft.status !== "failed").length;
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

/** Whether a link points at a video site, so the intake asks for the description or a screenshot instead. */
export function isVideoLink(url: string): boolean {
  try {
    const host = new URL(url.includes("//") ? url : `//${url}`, "https://x.invalid").hostname.toLowerCase();
    return VIDEO_HOSTS.some(video => host === video || host.endsWith(`.${video}`));
  }
  catch {
    return false;
  }
}

/** The error code of a draft that failed because no AI provider is set up (D76): trying again cannot help, typing can. */
export const NO_AI_ERROR = "ai_not_configured";

/** The sentence for an error code from the API; codes this version does not know get the general one. Whoever cannot
 * manage the AI providers (CAN_MANAGE false) is told to ask the admin instead of where to set one up (D76). */
export function errorText(code: string, t: Translate, canManage = true): string {
  if (code === NO_AI_ERROR && !canManage) return t("kh.drafts.error.ai_not_configured_member");
  return t(`kh.drafts.error.${ERROR_CODES.has(code) ? code : "unknown"}`);
}

/** The one number of "Ergibt 12 Muffins" (D76): the yield amount, else the servings. */
export function yieldNumber(changes: Pick<KhRecipeChanges, "recipeServings" | "recipeYieldQuantity">): number {
  return changes.recipeYieldQuantity || changes.recipeServings;
}

/** Sets servings and yield amount to the same number, as the single field of the review writes both. */
export function setYieldNumber(changes: Pick<KhRecipeChanges, "recipeServings" | "recipeYieldQuantity">, value: number): void {
  changes.recipeServings = value;
  changes.recipeYieldQuantity = value;
}

/** The sentence after a file import (D62): "3 Entwürfe angelegt, 1 übersprungen: Suppe.txt (zu groß)". T writes the
 * keys of kh.drafts; a number as its second argument picks the plural form. */
export function fileSummary(result: KhFileImport, t: (key: string, arg?: number | Record<string, unknown>) => string): string {
  const made = t("kh.drafts.file-created", result.created.length);
  if (!result.skipped.length) return made;
  const left = result.skipped.map(file => `${file.name} (${t(`kh.drafts.skip.${file.reason}`)})`).join(", ");
  return `${made}, ${t("kh.drafts.file-skipped", { n: result.skipped.length, list: left })}`;
}

/** The name of a draft in lists and headings: its recipe, else its link, else the start of its text. */
export function draftTitle(draft: KhDraft): string {
  if (draft.recipe?.name) return draft.recipe.name;
  if (draft.sourceUrl) return draft.sourceUrl.replace(/^https?:\/\/(?:www\.)?/, "");
  if (draft.sourceNote) return draft.sourceNote;
  const firstLine = (draft.sourceText ?? "").trim().split("\n")[0] ?? "";
  return firstLine.length > TITLE_LENGTH ? `${firstLine.slice(0, TITLE_LENGTH)}…` : firstLine;
}

/** Whether a draft is still being recognized, so the page has to look again soon. */
export function pollingNeeded(list: KhDraft[]): boolean {
  return list.some(draft => draft.status === "working");
}

/** What a draft carries for its amounts under khAmounts in its recipe JSON (D39); empty for older drafts. */
export function draftAmounts(recipe: RecipeOut | null | undefined): KhDraftAmounts {
  const amounts = (recipe as { khAmounts?: Partial<KhDraftAmounts> } | null | undefined)?.khAmounts;
  return { extras: amounts?.extras ?? [], stepAmounts: amounts?.stepAmounts ?? [] };
}

/** The review's fields start from what the recognition found: servings, yield amount and yield text, the step
 * links it made and the tags it chose. */
export function recipeChanges(recipe: RecipeOut | null): KhRecipeChanges {
  return {
    recipeServings: recipe?.recipeServings ?? 0,
    recipeYieldQuantity: recipe?.recipeYieldQuantity ?? 0,
    recipeYield: recipe?.recipeYield ?? "",
    linkedSteps: draftAmounts(recipe).stepAmounts.flatMap((link, index) => (link.linked ? [index] : [])),
    tags: recognizedTags(recipe),
  };
}

/** Where approving leads: the saved recipe, in Mealie's edit mode for "Save and edit". */
export function approveTarget(slug: string, groupSlug: string, edit: boolean): string {
  return `/g/${groupSlug}/r/${slug}${edit ? "?edit=true" : ""}`;
}

/** Where a hint on a possible duplicate leads: the saved recipe, else the other draft; nowhere for a hint on what
 * looks wrong in the draft itself. */
export function warningTarget(warning: KhDraftWarning, groupSlug: string): string {
  if (warning.recipeSlug) return `/g/${groupSlug}/r/${warning.recipeSlug}`;
  return warning.draftId ? `/g/${groupSlug}/drafts/${warning.draftId}` : ""; // a hint on the draft itself links nowhere
}

/** The detail of a failed drafts request, e.g. 409 with code "duplicates"; "offline" when the request never
 * reached the server, "media_too_large" for a 413 (a proxy such as Cloudflare cuts big uploads before the app
 * answers), "unknown" when the answer has no code. */
export function requestError(error: unknown): KhRequestError {
  const failed = error as { isAxiosError?: boolean; response?: { status?: number; data?: { detail?: unknown } } } | null;
  if (failed?.isAxiosError && !failed.response) return { code: "offline" };
  if (failed?.response?.status === 413) return { code: "media_too_large" };
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
