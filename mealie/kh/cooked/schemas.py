"""KH: what the start page's cooked rows get (D67)."""

from datetime import datetime

from pydantic import UUID4

from mealie.schema._mealie import MealieOutModel


class CookedRecipe(MealieOutModel):
    """One card of a row: enough for the recipe card, how often it was made and when last (by the household)."""

    id: UUID4
    slug: str
    name: str
    image: str | None = None
    count: int
    last_made: datetime | None = None


class CookedOut(MealieOutModel):
    """The two rows: made most often in the last year, and not made for the longest time."""

    often: list[CookedRecipe]
    long_ago: list[CookedRecipe]
