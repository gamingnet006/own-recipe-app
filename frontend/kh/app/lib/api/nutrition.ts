// KH: the API of nutrition values (D44) as a Mealie API class: a recipe's values per serving, the food-to-BLS mapping and
// the BLS search. The types are written by hand like the books' (mealie/kh/nutrition).
import { BaseAPI } from "~/lib/api/base/base-clients";

const base = "/api/kh";

export type KhNutrientKey = "kcal" | "fat" | "saturated" | "carbs" | "sugar" | "protein" | "fiber" | "salt";

/** Already rounded by the server; null where no counted ingredient had a value. */
export type KhNutritionValues = Record<KhNutrientKey, number | null>;

export interface KhRecipeNutrition {
  per: "serving" | "recipe";
  servings: number | null;
  /** Null when nothing could be counted. */
  values: KhNutritionValues | null;
  counted: number;
  total: number;
  /** The ingredient lines that were not counted. */
  missing: string[];
  /** A suggestion nobody confirmed went into the sum. */
  estimated: boolean;
  /** The values come from Mealie's own nutrition fields and were not calculated. */
  manual: boolean;
}

export interface KhFoodMapping {
  foodId: string;
  foodName: string;
  blsCode: string | null;
  blsName: string | null;
  confirmed: boolean;
  suggested: boolean;
  pieceGrams: number | null;
  recipeCount: number;
}

/** "No matching entry" is blsCode null with confirmed true. */
export interface KhFoodMappingUpdate {
  blsCode: string | null;
  confirmed: boolean;
  pieceGrams: number | null;
}

export interface KhBlsHit {
  code: string;
  name: string;
  kcal: number | null;
}

export class KhNutritionApi extends BaseAPI {
  async forRecipe(slug: string) {
    return await this.requests.get<KhRecipeNutrition>(`${base}/recipes/${encodeURIComponent(slug)}/nutrition`);
  }

  /** Every food used in recipes, the unconfirmed ones first. */
  async getFoods() {
    return await this.requests.get<KhFoodMapping[]>(`${base}/nutrition/foods`);
  }

  /** Stores the mapping of one food; 422 when the BLS code does not exist. */
  async putFood(foodId: string, update: KhFoodMappingUpdate) {
    return await this.requests.put<KhFoodMapping>(`${base}/nutrition/foods/${encodeURIComponent(foodId)}`, update);
  }

  /** At most 20 BLS entries whose name contains Q; none for an empty Q. */
  async searchBls(q: string) {
    return await this.requests.get<KhBlsHit[]>(`${base}/nutrition/bls?q=${encodeURIComponent(q)}`);
  }
}
