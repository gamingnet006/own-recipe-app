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


class AddByVoiceIn(MealieModel):
    """What was said or typed ("Milch und 2 Butter") and, optionally, the name of the list to put it on."""

    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    list: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)] | None = None


class AddByVoiceOut(MealieModel):
    """The sentence to read out, saying what stands on which list now."""

    message: str


class OnHandIn(MealieModel):
    """A food of the group and whether the household always has it in the house."""

    food_id: UUID4
    on_hand: bool
