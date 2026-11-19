// KH: the start page's season row (D80) as a Mealie API class; the types are written by hand
// (mealie/kh/season/schemas.py).
import { BaseAPI } from "~/lib/api/base/base-clients";

/** One card of the row and the in-season food that made the recipe match. */
export interface KhSeasonRecipe {
  id: string;
  slug: string;
  name: string;
  image: string | null;
  food: string;
}

export class KhSeasonApi extends BaseAPI {
  /** Up to eight recipes of the group that use one of the food names. */
  async get(terms: string[]) {
    const query = terms.map(term => `food=${encodeURIComponent(term)}`).join("&");
    return await this.requests.get<{ recipes: KhSeasonRecipe[] }>(`/api/kh/recipes/season?${query}`);
  }
}
