// KH: the "Woche vorschlagen" API (D70); the type is written by hand (mealie/kh/weeksuggestion/schemas.py).
import { BaseAPI } from "~/lib/api/base/base-clients";

/** One suggested recipe: enough for a recipe card. */
export interface KhSuggestedRecipe {
  id: string;
  slug: string;
  name: string;
  image: string | null;
}

export class KhWeekSuggestionApi extends BaseAPI {
  /** DAYS recipes, none of those in EXCLUDE (ids). */
  async get(days: number, exclude: string[]) {
    const query = [`days=${days}`, ...exclude.map(id => `exclude=${encodeURIComponent(id)}`)].join("&");
    return await this.requests.get<KhSuggestedRecipe[]>(`/api/kh/recipes/week-suggestion?${query}`);
  }
}
