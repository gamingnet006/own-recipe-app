"""KH: what the "What do I cook this week?" suggestion returns (D70)."""

from pydantic import UUID4

from mealie.schema._mealie import MealieOutModel


class SuggestedRecipe(MealieOutModel):
    """One suggested recipe: enough for a recipe card."""

    id: UUID4
    slug: str
    name: str
    image: str | None = None
