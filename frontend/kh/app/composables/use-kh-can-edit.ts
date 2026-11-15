// KH: whether the signed-in user may edit RECIPE, shared by the recipe header and the allergen block (D38, D44).
import { ref } from "vue";
import { useUserApi } from "~/composables/api";
import { usePageUser } from "~/composables/recipe-page/shared-state";
import { useRecipePermissions } from "~/composables/recipes";
import type { HouseholdSummary } from "~/lib/api/types/household";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import type { RecipeOut } from "~/lib/api/types/recipe";

/** Who may edit, as in Mealie's RecipePageHeader: the recipe's household decides for other households' recipes. */
export function useKhCanEdit(recipe: NoUndefinedField<RecipeOut>) {
  const { user } = usePageUser();
  const recipeHousehold = ref<HouseholdSummary>();
  if (user) {
    useUserApi().households.getOne(recipe.householdId).then(({ data }) => {
      recipeHousehold.value = data || undefined;
    });
  }
  return useRecipePermissions(recipe, recipeHousehold, user).canEditRecipe;
}
