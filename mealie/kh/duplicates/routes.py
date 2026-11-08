"""KH: the duplicate report's routes under /api/kh/duplicates (D43), for the user's household."""

from fastapi import HTTPException, status
from pydantic import UUID4

from mealie.kh.duplicates.schemas import DuplicatePair, IgnorePair
from mealie.kh.duplicates.service import duplicate_report, ignore_pair
from mealie.kh.features.settings import get_kh_settings
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.response import ErrorResponse

router = UserAPIRouter(prefix="/duplicates")


@controller(router)
class KhDuplicatesController(BaseUserController):
    """Recipes of the user's household that may be doubles."""

    @router.get("", response_model=list[DuplicatePair])
    def report(self, tag: UUID4 | None = None) -> list[DuplicatePair]:
        """Pairs of the household's recipes that may be the same dish, the most alike first; with `tag` (an ID) only
        pairs where one has it. Pairs the family chose to keep are left out."""
        return duplicate_report(self.session, self.repos.recipes.get_all(), tag, get_kh_settings())

    @router.post("/ignore", status_code=status.HTTP_204_NO_CONTENT)
    def ignore(self, data: IgnorePair) -> None:
        """Keeps both recipes: the pair no longer shows up in the report."""
        found = [self.repos.recipes.get_one(slug, "slug") for slug in (data.a, data.b)]
        if None in found or data.a == data.b:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Recipe not found"))
        ignore_pair(self.session, self.group_id, found[0].id, found[1].id)  # type: ignore[union-attr]
