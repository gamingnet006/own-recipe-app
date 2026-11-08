"""KH: what the nutrition endpoints send and take (D44), in camelCase like every Mealie answer."""

from pydantic import Field

from mealie.schema._mealie import MealieModel


class FoodMappingIn(MealieModel):
    """What the mapping page saves for a food: its BLS entry (None: no fitting entry), whether a person confirmed it,
    and the food's own weight of one piece."""

    bls_code: str | None = None
    confirmed: bool
    piece_grams: float | None = Field(None, gt=0)


class FoodMappingOut(MealieModel):
    """A food's mapping as the page shows it; suggested is true while the shown entry is only our guess."""

    food_id: str
    food_name: str
    bls_code: str | None
    bls_name: str | None
    confirmed: bool
    suggested: bool
    piece_grams: float | None
    recipe_count: int


class BlsHitOut(MealieModel):
    """One BLS search hit."""

    code: str
    name: str
    kcal: float | None
