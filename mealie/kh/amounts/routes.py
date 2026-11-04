"""KH: the amounts' route under /api/kh/amounts (D39): a saved recipe's range ends, fixed lines and step links, for
every member of its group."""

from fastapi import HTTPException, status
from pydantic import UUID4

from mealie.kh.amounts.schemas import AmountsOut
from mealie.kh.amounts.service import load_amounts
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.response import ErrorResponse

router = UserAPIRouter(prefix="/amounts")


@controller(router)
class KhAmountsController(BaseUserController):
    """The amounts of the group's recipes."""

    @router.get("/{recipe_id}", response_model=AmountsOut)
    def amounts(self, recipe_id: UUID4) -> AmountsOut:
        """The amounts of a recipe of the user's group, any household; 404 for another group's or an unknown one."""
        recipes = get_repositories(self.session, group_id=self.group_id, household_id=None).recipes
        if recipes.get_one(recipe_id, "id") is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Recipe not found"))
        return load_amounts(self.session, recipe_id)
