"""KH: the nutrition routes under /api/kh (D44): the food to BLS mapping and the BLS search."""

from fastapi import HTTPException, Query, status
from pydantic import UUID4

from mealie.kh.nutrition.bls import BLS_SEARCH_LIMIT, load_bls, search_bls
from mealie.kh.nutrition.calculate import calculate
from mealie.kh.nutrition.mapping import food_mapping, list_mappings, load_aliases, mappings_for, save_mapping
from mealie.kh.nutrition.schemas import BlsHitOut, FoodMappingIn, FoodMappingOut, NutritionOut
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.response import ErrorResponse

router = UserAPIRouter()


@controller(router)
class KhNutritionController(BaseUserController):
    """The mapping of the user's group's foods to BLS entries."""

    @router.get("/nutrition/foods", response_model=list[FoodMappingOut])
    def get_foods(self) -> list[FoodMappingOut]:
        """The group's foods that recipes use, unconfirmed first, then by name."""
        return list_mappings(self.session, self.group_id)

    @router.put("/nutrition/foods/{food_id}", response_model=FoodMappingOut)
    def put_food(self, food_id: UUID4, data: FoodMappingIn) -> FoodMappingOut:
        """Saves a food's mapping and returns it as stored; 422 for a BLS code the table does not have, 404 for a
        food of another group."""
        food = get_repositories(self.session, group_id=self.group_id, household_id=None).ingredient_foods.get_one(
            food_id
        )
        if food is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Food not found"))
        if data.bls_code is not None and data.bls_code not in load_bls():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, ErrorResponse.respond("Unknown BLS code"))
        save_mapping(self.session, food.id, data)
        return food_mapping(self.session, food)

    @router.get("/nutrition/bls", response_model=list[BlsHitOut])
    def get_bls(self, q: str = Query("", description="Words the BLS name must contain")) -> list[BlsHitOut]:
        """At most BLS_SEARCH_LIMIT BLS foods whose names contain every word of the query."""
        return [BlsHitOut(code=f.code, name=f.name, kcal=f.kcal) for f in search_bls(q, load_bls(), BLS_SEARCH_LIMIT)]

    @router.get("/recipes/{slug}/nutrition", response_model=NutritionOut)
    def get_nutrition(self, slug: str) -> NutritionOut:
        """The nutrition of any recipe of the user's group (also another household's); 404 for other groups."""
        recipe = get_repositories(self.session, group_id=self.group_id, household_id=None).recipes.get_one(slug, "slug")
        if recipe is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Recipe not found"))
        return calculate(recipe, mappings_for(self.session, recipe), load_bls(), load_aliases())
