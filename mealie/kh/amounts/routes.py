"""KH: the amounts' route under /api/kh/amounts (D39): a saved recipe's range ends, fixed lines and step links, for
every member of its group."""

from fastapi import HTTPException, Request, status
from pydantic import UUID4

from mealie.kh.amounts.line import parse_shopping_line
from mealie.kh.amounts.parse import ensure_extra_units
from mealie.kh.amounts.schemas import AmountsOut, ShoppingLineIn, ShoppingLineOut
from mealie.kh.amounts.service import load_amounts
from mealie.kh.i18n.messages import request_locale
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.response import ErrorResponse
from mealie.services.parser_services._base import DataMatcher

router = UserAPIRouter(prefix="/amounts")


@controller(router)
class KhAmountsController(BaseUserController):
    """The amounts of the group's recipes."""

    @router.post("/parse-line", response_model=ShoppingLineOut)
    def parse_line(self, data: ShoppingLineIn, request: Request) -> ShoppingLineOut:
        """A line typed on the shopping page read with the group's units and foods (D60)."""
        repos = get_repositories(self.session, group_id=self.group_id, household_id=None)
        ensure_extra_units(repos)
        matcher = DataMatcher(repos)
        try:
            line = parse_shopping_line(
                data.text,
                matcher.units_by_alias,
                matcher.foods_by_alias,
                request_locale(self.session, self.user.id, request),
            )
        except ValueError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, ErrorResponse.respond("No article in the line")
            ) from None
        return ShoppingLineOut(
            quantity=line.quantity,
            unit_id=line.unit.id if line.unit else None,
            unit_abbreviation=line.unit_abbreviation,
            food_id=line.food.id if line.food else None,
            name=line.name,
            note=line.note,
        )

    @router.get("/{recipe_id}", response_model=AmountsOut)
    def amounts(self, recipe_id: UUID4) -> AmountsOut:
        """The amounts of a recipe of the user's group, any household; 404 for another group's or an unknown one."""
        recipes = get_repositories(self.session, group_id=self.group_id, household_id=None).recipes
        if recipes.get_one(recipe_id, "id") is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Recipe not found"))
        return load_amounts(self.session, recipe_id)
