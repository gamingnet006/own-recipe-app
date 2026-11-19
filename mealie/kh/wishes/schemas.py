"""KH: what the wish list's routes take and return (D72)."""

from datetime import date, datetime

from pydantic import UUID4

from mealie.schema._mealie import MealieModel, MealieOutModel
from mealie.schema.meal_plan.new_meal import PlanEntryType


class WishRecipe(MealieOutModel):
    """The wished recipe: enough for a card."""

    id: UUID4
    slug: str
    name: str
    image: str | None = None


class WishPerson(MealieOutModel):
    """A person of the household who wishes the recipe."""

    id: UUID4
    name: str


class WishOut(MealieOutModel):
    """One open wish: the recipe, everybody who wishes it, and since when (the oldest of them)."""

    recipe: WishRecipe
    people: list[WishPerson]
    since: datetime


class WishPlan(MealieModel):
    """Plans a wished recipe on a day; the entry type is a dinner unless said otherwise."""

    date: date
    entry_type: PlanEntryType = PlanEntryType.dinner
