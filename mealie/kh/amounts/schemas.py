"""KH: what the amounts send and keep (D39), in camelCase like every Mealie answer; the draft keeps the same shapes
under "khAmounts" in its recipe JSON until the approval saves them."""

from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel


class IngredientExtraOut(MealieModel):
    """An ingredient line's range end or its mark that it never scales."""

    model_config = ConfigDict(from_attributes=True)

    reference_id: UUID4
    upper: float | None = None
    fixed: bool = False


class StepAmountOut(MealieModel):
    """An amount in a step's text linked to an ingredient, as a fraction of its amount."""

    model_config = ConfigDict(from_attributes=True)

    step: int  # the step's place in the recipe, from 0
    start: int
    end: int
    text: str
    reference_id: UUID4
    fraction: float = 1


class DraftStepAmount(StepAmountOut):
    """A link found in a draft; the review may unlink it before the approval."""

    linked: bool = True


class DraftAmounts(MealieModel):
    """What a draft carries for its amounts."""

    extras: list[IngredientExtraOut] = []
    step_amounts: list[DraftStepAmount] = []


class AmountsOut(MealieModel):
    """A saved recipe's amounts for the views: range ends, fixed lines and the links in the steps."""

    extras: list[IngredientExtraOut] = []
    step_amounts: list[StepAmountOut] = []
