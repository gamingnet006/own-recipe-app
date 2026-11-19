"""KH: the season row's route under /api/kh/recipes/season (D80); closed with 403 while the add-on is off."""

from typing import Annotated

from fastapi import Query
from pydantic import StringConstraints

from mealie.kh.season.schemas import SeasonOut
from mealie.kh.season.service import season_recipes
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter

router = UserAPIRouter(prefix="/recipes")

FoodName = Annotated[str, StringConstraints(max_length=40)]


@controller(router)
class KhSeasonController(BaseUserController):
    """The recipes that use what is in season."""

    @router.get("/season", response_model=SeasonOut)
    def season(self, food: Annotated[list[FoodName], Query(max_length=120)] = []) -> SeasonOut:  # noqa: B006
        """Up to eight recipes of the group using one of the FOOD names (the frontend sends this month's foods)."""
        return season_recipes(self.session, self.group_id, food)
