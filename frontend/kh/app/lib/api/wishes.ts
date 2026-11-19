// KH: the household wish list's API (D72); the types are written by hand (mealie/kh/wishes/schemas.py).
import { BaseAPI } from "~/lib/api/base/base-clients";
import type { PlanEntryOut, PlanEntryType } from "~/lib/api/types/meal-plan";

export interface KhWishPerson {
  id: string;
  name: string;
}

/** One open wish: the recipe, everybody who wishes it and since when (the oldest wish). */
export interface KhWish {
  recipe: { id: string; slug: string; name: string; image: string | null };
  people: KhWishPerson[];
  since: string;
}

export class KhWishesApi extends BaseAPI {
  /** The household's open wishes, the longest wished first. */
  async list() {
    return await this.requests.get<KhWish[]>("/api/kh/wishes");
  }

  /** The signed-in person wishes the recipe. */
  async wish(recipeId: string) {
    return await this.requests.put<unknown, null>(`/api/kh/wishes/${recipeId}`, null);
  }

  /** The signed-in person takes their own wish back. */
  async unwish(recipeId: string) {
    return await this.requests.delete<unknown>(`/api/kh/wishes/${recipeId}`);
  }

  /** Plans the wished recipe (a dinner unless said otherwise) on DATE (yyyy-MM-dd); that ends the wish. */
  async plan(recipeId: string, date: string, entryType: PlanEntryType = "dinner") {
    return await this.requests.post<PlanEntryOut, { date: string; entryType: PlanEntryType }>(`/api/kh/wishes/${recipeId}/plan`, { date, entryType });
  }
}
