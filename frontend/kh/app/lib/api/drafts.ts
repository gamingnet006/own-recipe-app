// KH: the drafts API (phase 2) as a Mealie API class. The answer types are written by hand, because
// Mealie's type generator only reads mealie/schema and ours live in mealie/kh/drafts/schemas.py.
import { BaseAPI } from "~/lib/api/base/base-clients";
import { OWN_ERRORS } from "./own-errors";
import type { RecipeOut } from "~/lib/api/types/recipe";
import type { KhDraftEdit } from "../draft-edit";

const drafts = "/api/kh/drafts";

export type KhDraftStatus = "working" | "ready" | "failed" | "approved";
export type KhDraftSource = "link" | "text" | "image";

export interface KhDraftWarning {
  kind:
    | "duplicate_link"
    | "similar_title"
    | "similar_ingredients"
    // what looks wrong in the draft (D39); name is the line, time, temperature, ingredient or units
    | "amount_unparsed"
    | "amount_unusual"
    | "time_unusual"
    | "temperature_unusual"
    | "ingredient_unused"
    | "units_converted";
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
  sourceNote: string | null; // the file name of a recording (P7.3)
  sourceUrl: string | null;
  sourceUrlNormalized: string | null;
  sourceText: string | null;
  originalFiles: string[];
  recipe: RecipeOut | null;
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

/** A category chosen in the review, as the recipe holds it. */
export interface KhCategoryRef {
  id: string;
  name: string;
  slug: string;
}

/** Servings and yield set in the review, the indices of the step links it kept and the categories it chose (D55);
 * saved with the recipe when it is approved. */
export interface KhRecipeChanges {
  recipeServings: number;
  recipeYieldQuantity: number;
  recipeYield: string;
  linkedSteps: number[];
  recipeCategory?: KhCategoryRef[];
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
    return await this.requests.post<KhDraft, FormData>(drafts, form, OWN_ERRORS);
  }

  /** The household's drafts that are not approved yet, newest first. */
  async list() {
    return await this.requests.get<KhDraft[]>(drafts);
  }

  async get(id: string) {
    return await this.requests.get<KhDraft>(`${drafts}/${id}`);
  }

  /** Changes the name, one ingredient line or one step of a ready draft's recipe; answers the draft as it is now. */
  async edit(id: string, body: KhDraftEdit) {
    return await this.requests.patch<KhDraft, KhDraftEdit>(`${drafts}/${id}/recipe`, body, OWN_ERRORS);
  }

  /** Starts the recognition of a failed draft again. */
  async retry(id: string) {
    return await this.requests.post<KhDraft, undefined>(`${drafts}/${id}/retry`, undefined, OWN_ERRORS);
  }

  /** Saves the draft as a recipe with the review's changes; FORCE saves it despite possible duplicates that
   * turned up meanwhile. */
  async approve(id: string, force = false, changes?: KhRecipeChanges) {
    return await this.requests.post<{ slug: string }, { force: boolean } & Partial<KhRecipeChanges>>(
      `${drafts}/${id}/approve`,
      { force, ...changes },
      OWN_ERRORS,
    );
  }

  async discard(id: string) {
    return await this.requests.delete(`${drafts}/${id}`, OWN_ERRORS);
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
