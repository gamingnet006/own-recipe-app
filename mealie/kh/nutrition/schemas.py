"""KH: what the nutrition endpoints send and take (D44), in camelCase like every Mealie answer."""

from typing import Literal

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


class NutritionValues(MealieModel):
    """The nine values of the BLS (g, kcal for energy), rounded for display; None where no counted line has one."""

    kcal: float | None = None
    fat: float | None = None
    saturated: float | None = None
    carbs: float | None = None
    sugar: float | None = None
    protein: float | None = None
    fiber: float | None = None
    salt: float | None = None


class NutritionOut(MealieModel):
    """A recipe's nutrition: per serving, or for the whole recipe without servings. counted of total lines went in,
    missing holds the text of the others, estimated says a suggested BLS entry counted, manual says the values were
    entered by hand in Mealie's fields and nothing was calculated."""

    per: Literal["serving", "recipe"]
    servings: float | None
    values: NutritionValues | None
    counted: int
    total: int
    missing: list[str]
    estimated: bool
    manual: bool
