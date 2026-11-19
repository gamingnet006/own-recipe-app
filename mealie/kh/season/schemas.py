"""KH: what the start page's season row gets (D80)."""

from pydantic import UUID4

from mealie.schema._mealie import MealieOutModel


class SeasonRecipe(MealieOutModel):
    """One card of the row: enough for the recipe card, and the in-season food that made it match."""

    id: UUID4
    slug: str
    name: str
    image: str | None = None
    food: str


class SeasonOut(MealieOutModel):
    """Up to eight recipes of the group that use an in-season food."""

    recipes: list[SeasonRecipe]
