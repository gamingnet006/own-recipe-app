// KH: the family note of a recipe (D82) as a Mealie API class; the types are written by hand
// (mealie/kh/notes/schemas.py).
import { BaseAPI } from "~/lib/api/base/base-clients";

/** A household's note on a recipe, who last changed it and when. */
export interface KhNote {
  text: string;
  /** null once that person's account is gone and nobody inherited the note */
  updatedBy: string | null;
  updatedByName: string;
  updatedAt: string | null;
}

export class KhNotesApi extends BaseAPI {
  /** The household's note on the recipe; null when there is none. */
  async get(recipeId: string) {
    return await this.requests.get<KhNote | null>(`/api/kh/recipes/${recipeId}/note`);
  }

  /** Stores the note (an empty text deletes it and answers null). */
  async put(recipeId: string, text: string) {
    return await this.requests.put<KhNote | null, { text: string }>(`/api/kh/recipes/${recipeId}/note`, { text });
  }
}
