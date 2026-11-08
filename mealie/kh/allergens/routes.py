"""KH: the allergen routes under /api/kh (D44): a recipe's allergens with corrections, the "Ich vertrage nicht"
profile and the warnings for the viewer's household."""

from fastapi import HTTPException, status

from mealie.kh.allergens.profile import (
    household_members,
    household_warnings,
    load_allergies,
    save_allergies,
    warnings_for,
)
from mealie.kh.allergens.rules import recipe_allergens
from mealie.kh.allergens.schemas import (
    AllergenCorrectionIn,
    AllergenProfile,
    AllergenReport,
    allergen_key,
)
from mealie.kh.allergens.service import corrections_of, group_recipes, set_correction
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.response import ErrorResponse
from mealie.services.recipe.recipe_service import RecipeService

router = UserAPIRouter()


@controller(router)
class KhAllergensController(BaseUserController):
    """Allergens of the recipes of the user's group and the user's own list."""

    def _recipe(self, slug: str) -> Recipe:
        """The group's recipe, from any household; 404 for others."""
        recipe = get_repositories(self.session, group_id=self.group_id, household_id=None).recipes.get_one(slug, "slug")
        if recipe is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Recipe not found"))
        return recipe

    @router.get("/recipes/{slug}/allergens", response_model=AllergenReport)
    def get_allergens(self, slug: str) -> AllergenReport:
        """The allergens of any recipe of the user's group (also another household's), with their source lines and
        the warnings for the user's own household."""
        recipe = self._recipe(slug)
        hits = recipe_allergens(recipe, corrections_of(self.session, recipe.id))
        return AllergenReport(
            hits=hits, warnings=household_warnings(self.session, self.household_id, hits), substitutions=[]
        )

    @router.put("/recipes/{slug}/allergens/{allergen}", response_model=AllergenCorrectionIn)
    def put_correction(self, slug: str, allergen: str, data: AllergenCorrectionIn) -> AllergenCorrectionIn:
        """Corrects one allergen of a recipe (present None clears it), for whoever may edit the recipe."""
        try:
            allergen_key(allergen)
        except ValueError as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, ErrorResponse.respond(str(e))) from e
        recipe = self._recipe(slug)
        if not RecipeService(self.repos, self.user, self.household, self.translator).can_update([slug]):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Dieses Rezept darfst du nicht ändern")
        set_correction(self.session, recipe.id, allergen, data.present)
        return data

    @router.get("/users/self/allergies", response_model=AllergenProfile)
    def get_allergies(self) -> AllergenProfile:
        """The allergens the user cannot have."""
        return AllergenProfile(allergens=load_allergies(self.session, self.user.id))

    @router.put("/users/self/allergies", response_model=AllergenProfile)
    def put_allergies(self, data: AllergenProfile) -> AllergenProfile:
        """Stores the user's list and returns it as stored (no duplicates, in the app's order)."""
        save_allergies(self.session, self.user.id, data.allergens)
        return data

    @router.get("/allergens/warnings", response_model=dict[str, list[str]])
    def get_warnings(self) -> dict[str, list[str]]:
        """For every recipe of the group with a warning for the user's household: its slug and the allergens
        concerned. ponytail: computed on request over all recipes; cache when a group passes about 2,000 recipes."""
        members = household_members(self.session, self.household_id)
        if not members:
            return {}
        found = {}
        for recipe in group_recipes(self.session, self.group_id):
            warnings = warnings_for(members, recipe_allergens(recipe, corrections_of(self.session, recipe.id)))
            if warnings:
                found[recipe.slug] = [w.allergen for w in warnings]
        return found
