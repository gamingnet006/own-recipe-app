// KH: the amounts' API (D39) as a Mealie API class: a saved recipe's range ends, fixed lines and links in the steps.
// The types are written by hand like the drafts' (mealie/kh/amounts/schemas.py).
import { BaseAPI } from "~/lib/api/base/base-clients";

/** An ingredient line's range end or its mark that it never scales, by the line's referenceId. */
export interface KhIngredientExtra {
  referenceId: string;
  upper: number | null;
  fixed: boolean;
}

/** An amount in a step's text linked to an ingredient, as a fraction of its amount; STEP is the step's place, from 0. */
export interface KhStepAmount {
  step: number;
  start: number;
  end: number;
  text: string;
  referenceId: string;
  fraction: number;
}

export interface KhAmounts {
  extras: KhIngredientExtra[];
  stepAmounts: KhStepAmount[];
}

/** What a draft carries under khAmounts in its recipe JSON; the review may unlink a step link before approving. */
export interface KhDraftAmounts {
  extras: KhIngredientExtra[];
  stepAmounts: (KhStepAmount & { linked: boolean })[];
}

export class KhAmountsApi extends BaseAPI {
  /** The amounts of a recipe of the user's group. */
  async get(recipeId: string) {
    return await this.requests.get<KhAmounts>(`/api/kh/amounts/${recipeId}`);
  }
}
