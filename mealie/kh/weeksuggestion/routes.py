"""KH: the week suggestion's route under /api/kh/recipes/week-suggestion (D70), for the user's group and household."""

from fastapi import Query
from pydantic import UUID4

from mealie.kh.weeksuggestion.schemas import SuggestedRecipe
from mealie.kh.weeksuggestion.service import suggest_week
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter

router = UserAPIRouter(prefix="/recipes")


@controller(router)
class KhWeekSuggestionController(BaseUserController):
    """Recipe ideas for the days of a week that have no dinner yet."""

    @router.get("/week-suggestion", response_model=list[SuggestedRecipe])
    def week_suggestion(
        self,
        days: int = Query(7, ge=1, le=31),
        exclude: list[UUID4] = Query(default_factory=list),
        seed: int | None = None,
    ) -> list[SuggestedRecipe]:
        """DAYS distinct recipes: often and long-ago cooked ones, never-made favorites, then random ones. Not made in
        the last 7 days, not planned in the next 14, not in EXCLUDE. SEED makes the answer repeatable (tests)."""
        return suggest_week(self.session, self.group_id, self.household_id, self.user.id, days, exclude, seed)
