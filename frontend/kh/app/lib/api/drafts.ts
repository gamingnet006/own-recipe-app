// KH: the drafts API (phase 2) as a Mealie API class. The answer types are written by hand, because
// Mealie's type generator only reads mealie/schema and ours live in mealie/kh/drafts/schemas.py.
import { BaseAPI } from "~/lib/api/base/base-clients";
import type { Recipe } from "~/lib/api/types/recipe";

const drafts = "/api/kh/drafts";

export type KhDraftStatus = "working" | "ready" | "failed" | "approved";
export type KhDraftSource = "link" | "text" | "image";

export interface KhDraftWarning {
  kind: "duplicate_link" | "similar_title" | "similar_ingredients";
  name: string;
  recipeSlug: string | null;
  draftId: string | null;
}

export interface KhDraft {
  id: string;
  groupId: string;
  householdId: string;
  userId: string | null;
  userName: string;
  status: KhDraftStatus;
  sourceType: KhDraftSource;
  sourceUrl: string | null;
  sourceUrlNormalized: string | null;
  sourceText: string | null;
  originalFiles: string[];
  recipe: Recipe | null;
  warnings: KhDraftWarning[];
  error: string | null;
  aiModel: string | null;
  recipeId: string | null;
  approvedBy: string | null;
  approvedAt: string | null;
  createdAt: string;
  updateAt: string;
}

export interface KhOrigin {
  draftId: string;
  sourceType: KhDraftSource;
  sourceUrl: string | null;
  userName: string;
  createdAt: string;
  aiModel: string | null;
  originalCount: number;
}

/** Servings and yield set in the review; they are saved with the recipe when it is approved. */
export interface KhRecipeChanges {
  recipeServings: number;
  recipeYieldQuantity: number;
  recipeYield: string;
}

/** The detail of a failed drafts request: a code, and for some codes what goes with it. */
export interface KhRequestError {
  code: string;
  warnings?: KhDraftWarning[]; // 409 duplicates: the hints that are new since the recognition
  slug?: string | null; // 409 already_approved: the saved recipe
}

export class KhDraftsApi extends BaseAPI {
  /** Hands in a link, a text or photos (form fields url, text, images); the recognition runs afterwards. */
  async create(form: FormData) {
    return await this.requests.post<KhDraft, FormData>(drafts, form);
  }

  /** The household's drafts that are not approved yet, newest first. */
  async list() {
    return await this.requests.get<KhDraft[]>(drafts);
  }

  async get(id: string) {
    return await this.requests.get<KhDraft>(`${drafts}/${id}`);
  }

  /** Starts the recognition of a failed draft again. */
  async retry(id: string) {
    return await this.requests.post<KhDraft, undefined>(`${drafts}/${id}/retry`, undefined);
  }

  /** Saves the draft as a recipe with the review's changes; FORCE saves it despite possible duplicates that
   * turned up meanwhile. */
  async approve(id: string, force = false, changes?: KhRecipeChanges) {
    return await this.requests.post<{ slug: string }, { force: boolean } & Partial<KhRecipeChanges>>(
      `${drafts}/${id}/approve`,
      { force, ...changes },
    );
  }

  async discard(id: string) {
    return await this.requests.delete(`${drafts}/${id}`);
  }

  /** Where a recipe came from; no data for recipes that were not added through a draft. */
  async origin(recipeId: string) {
    return await this.requests.get<KhOrigin>(`/api/kh/recipes/${recipeId}/origin`);
  }

  /** Address of the n-th original photo (from 1); images send the session cookie, so it works in <img>. */
  originalUrl(id: string, n: number): string {
    return `${drafts}/${id}/originals/${n}`;
  }
}
