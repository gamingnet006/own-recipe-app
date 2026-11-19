"""KH: the cooked rows' route under /api/kh/recipes/cooked (D67), for the user's group and household."""

from mealie.kh.cooked.schemas import CookedOut
from mealie.kh.cooked.service import cooked_rows
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter

router = UserAPIRouter(prefix="/recipes")


@controller(router)
class KhCookedController(BaseUserController):
    """What the family cooks often and what it has not cooked for long."""

    @router.get("/cooked", response_model=CookedOut)
    def cooked(self) -> CookedOut:
        """Up to eight recipes made most often in the last year (at least twice) and up to eight made at least once
        but not for over 30 days (by this household, the longest ago first)."""
        return cooked_rows(self.session, self.group_id, self.household_id)
