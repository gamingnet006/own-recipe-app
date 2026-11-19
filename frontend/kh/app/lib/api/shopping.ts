// KH: the shopping page's API (D60): a food or unit made on the way, also for members who may not organize, which
// Mealie's own POST /api/foods and /api/units demand.
import { BaseAPI } from "~/lib/api/base/base-clients";
import type { IngredientFoodOut, IngredientUnitOut } from "~/lib/api/types/recipe";

export class KhShoppingApi extends BaseAPI {
  /** The group's food of that name (ignoring case and number), made with LABELID when there is none. */
  async ensureFood(name: string, labelId: string | null) {
    return await this.requests.post<IngredientFoodOut, { name: string; labelId: string | null }>("/api/kh/shopping/ensure-food", { name, labelId });
  }

  /** The group's unit g, kg, ml or l, made when missing. */
  async ensureUnit(abbreviation: string) {
    return await this.requests.post<IngredientUnitOut, { abbreviation: string }>("/api/kh/shopping/ensure-unit", { abbreviation });
  }
}
