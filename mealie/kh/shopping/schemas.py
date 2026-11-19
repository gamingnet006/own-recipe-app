"""KH: what the shopping page sends to make sure a food or a unit exists (D60)."""

from typing import Annotated, Literal

from pydantic import UUID4, StringConstraints

from mealie.schema._mealie import MealieModel


class EnsureFoodIn(MealieModel):
    """A food's name, 1 to 60 characters after trimming, and optionally the label (department) a new food gets."""

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    label_id: UUID4 | None = None


class EnsureUnitIn(MealieModel):
    """The abbreviation of one of the units the amount chips use."""

    abbreviation: Literal["g", "kg", "ml", "l"]
