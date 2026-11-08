"""KH: the family cookbook's routes under /api/kh (D43): print settings per cookbook, and the own-photo flag per
recipe."""

from fastapi import HTTPException, Query, status
from pydantic import UUID4

from mealie.kh.books.schemas import BookSettings, RecipeFlags
from mealie.kh.books.service import load_settings, own_photo_slugs, save_settings, set_own_photo
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.cookbook import ReadCookBook
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.response import ErrorResponse
from mealie.services.recipe.recipe_service import RecipeService

router = UserAPIRouter()


@controller(router)
class KhBooksController(BaseUserController):
    """Book settings and flags of the user's group."""

    def _cookbook(self, cookbook_id: UUID4) -> ReadCookBook:
        """The group's cookbook, from any household (Mealie lets everyone read them); 404 for others."""
        cookbook = get_repositories(self.session, group_id=self.group_id, household_id=None).cookbooks.get_one(
            cookbook_id
        )
        if cookbook is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Cookbook not found"))
        return cookbook

    def _recipe(self, slug: str) -> Recipe:
        """The group's recipe, from any household; 404 for others."""
        recipe = get_repositories(self.session, group_id=self.group_id, household_id=None).recipes.get_one(slug, "slug")
        if recipe is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Recipe not found"))
        return recipe

    @router.get("/cookbooks/{cookbook_id}/print", response_model=BookSettings)
    def get_print(self, cookbook_id: UUID4) -> BookSettings:
        """The cookbook's stored print settings, or the defaults."""
        self._cookbook(cookbook_id)
        return load_settings(self.session, self.group_id, cookbook_id)

    @router.put("/cookbooks/{cookbook_id}/print", response_model=BookSettings)
    def put_print(self, cookbook_id: UUID4, data: BookSettings) -> BookSettings:
        """Stores the settings, only for the cookbook's own household, and returns them as stored."""
        if self._cookbook(cookbook_id).household_id != self.household_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur der eigene Haushalt kann dieses Kochbuch ändern")
        return save_settings(self.session, self.group_id, cookbook_id, data)

    @router.get("/recipes/flags", response_model=dict[str, RecipeFlags])
    def get_flags(self, slugs: str = Query("", description="Comma-separated recipe slugs")) -> dict[str, RecipeFlags]:
        """The flags of the named recipes of the user's group, by slug; unknown slugs are left out."""
        found = own_photo_slugs(self.session, self.group_id, [s for s in slugs.split(",") if s])
        return {slug: RecipeFlags(own_photo=own) for slug, own in found.items()}

    @router.put("/recipes/{slug}/flags", response_model=RecipeFlags)
    def put_flags(self, slug: str, data: RecipeFlags) -> RecipeFlags:
        """Sets a recipe's flags, for whoever may edit the recipe."""
        recipe = self._recipe(slug)
        if not RecipeService(self.repos, self.user, self.household, self.translator).can_update([slug]):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Dieses Rezept darfst du nicht ändern")
        set_own_photo(self.session, recipe.id, data.own_photo)
        return data
