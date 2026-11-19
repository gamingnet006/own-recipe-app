// KH: the start page's cooked rows (D67) as a Mealie API class; the types are written by hand like the drafts'
// (mealie/kh/cooked/schemas.py).
import { BaseAPI } from "~/lib/api/base/base-clients";

/** One card of a row: how often the recipe was made and when last (by the household). */
export interface KhCookedRecipe {
  id: string;
  slug: string;
  name: string;
  image: string | null;
  count: number;
  lastMade: string | null;
}

export interface KhCooked {
  often: KhCookedRecipe[];
  longAgo: KhCookedRecipe[];
}

export class KhCookedApi extends BaseAPI {
  /** The recipes made most often in the last year and those not made for long. */
  async get() {
    return await this.requests.get<KhCooked>("/api/kh/recipes/cooked");
  }
}
