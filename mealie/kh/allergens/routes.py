"""KH: the allergen routes under /api/kh (D44): a recipe's allergens with corrections."""

from fastapi import HTTPException, status

from mealie.kh.allergens.rules import ALLERGENS, recipe_allergens
from mealie.kh.allergens.schemas import AllergenCorrectionIn, AllergenHit
from mealie.kh.allergens.service import corrections_of, set_correction
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.response import ErrorResponse
from mealie.services.recipe.recipe_service import RecipeService

router = UserAPIRouter()


@controller(router)
class KhAllergensController(BaseUserController):
    """Allergens of the recipes of the user's group."""

    def _recipe(self, slug: str) -> Recipe:
        """The group's recipe, from any household; 404 for others."""
        recipe = get_repositories(self.session, group_id=self.group_id, household_id=None).recipes.get_one(slug, "slug")
        if recipe is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Recipe not found"))
        return recipe

    @router.get("/recipes/{slug}/allergens", response_model=list[AllergenHit])
    def get_allergens(self, slug: str) -> list[AllergenHit]:
        """The allergens of any recipe of the user's group (also another household's), with their source lines."""
        recipe = self._recipe(slug)
        return recipe_allergens(recipe, corrections_of(self.session, recipe.id))

    @router.put("/recipes/{slug}/allergens/{allergen}", response_model=AllergenCorrectionIn)
    def put_correction(self, slug: str, allergen: str, data: AllergenCorrectionIn) -> AllergenCorrectionIn:
        """Corrects one allergen of a recipe (present None clears it), for whoever may edit the recipe."""
        if allergen not in ALLERGENS:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, ErrorResponse.respond("Unknown allergen"))
        recipe = self._recipe(slug)
        if not RecipeService(self.repos, self.user, self.household, self.translator).can_update([slug]):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Dieses Rezept darfst du nicht ändern")
        set_correction(self.session, recipe.id, allergen, data.present)
        return data
