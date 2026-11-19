"""KH: the shopping page's routes under /api/kh/shopping (D60). Mealie's own POST /api/foods and /api/units need the
permission to organize, which a normal family member lacks; these two let every signed-in member of the group
write down an item, and only ever make a food or one of four standard units."""

from fastapi import HTTPException, status

from mealie.kh.shopping.schemas import EnsureFoodIn, EnsureUnitIn
from mealie.kh.shopping.service import ensure_food, ensure_unit
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.recipe.recipe_ingredient import IngredientFoodOut, IngredientUnitOut
from mealie.schema.response import ErrorResponse

router = UserAPIRouter(prefix="/shopping")


@controller(router)
class KhShoppingController(BaseUserController):
    """Foods and units for members who may not organize."""

    @router.post("/ensure-food", response_model=IngredientFoodOut)
    def food(self, data: EnsureFoodIn) -> IngredientFoodOut:
        """The group's food of this name (ignoring case and singular or plural), made when there is none, for any
        member, also without the permission to organize. A label must belong to the user's group (422 otherwise)."""
        repos = get_repositories(self.session, group_id=self.group_id, household_id=None)
        if data.label_id and repos.group_multi_purpose_labels.get_one(data.label_id) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, ErrorResponse.respond("Unknown label"))
        return ensure_food(repos, data.name, data.label_id)

    @router.post("/ensure-unit", response_model=IngredientUnitOut)
    def unit(self, data: EnsureUnitIn) -> IngredientUnitOut:
        """The group's unit g, kg, ml or l (found by abbreviation or name, ignoring case), made when missing, for
        any member, also without the permission to organize; any other abbreviation is refused with 422."""
        repos = get_repositories(self.session, group_id=self.group_id, household_id=None)
        return ensure_unit(repos, data.abbreviation)
