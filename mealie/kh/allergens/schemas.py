"""KH: what the allergen endpoints send and take (D44), in camelCase like every Mealie answer."""

from mealie.schema._mealie import MealieModel


class AllergenHit(MealieModel):
    """One allergen of a recipe with the ingredient lines it was found in; corrected says a person's correction
    applies (False: taken out, True: added by hand, None: none)."""

    allergen: str
    lines: list[str]
    corrected: bool | None


class AllergenCorrectionIn(MealieModel):
    """A person's correction of one allergen of one recipe; None removes the correction."""

    present: bool | None
