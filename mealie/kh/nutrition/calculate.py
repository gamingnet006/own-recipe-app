"""KH: the nutrition of a recipe (D44): grams of each ingredient line times its BLS values per 100 g, summed and
divided by the servings. Pure; the lines it cannot weigh or match are named, never counted as zero."""

import math
import re
from uuid import UUID

from mealie.kh.nutrition.bls import SALT_PER_SODIUM, BlsFood
from mealie.kh.nutrition.grams import grams_of
from mealie.kh.nutrition.mapping import resolve_code
from mealie.kh.nutrition.models import KhFoodNutrition
from mealie.kh.nutrition.schemas import NutritionOut, NutritionValues
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.schema.recipe.recipe_nutrition import Nutrition

NUTRIENTS = ("kcal", "fat", "saturated", "carbs", "sugar", "protein", "fiber", "salt")
# Mealie's nutrition field for each of our values; sodium is converted to salt separately
MEALIE_FIELDS = {
    "kcal": "calories",
    "fat": "fat_content",
    "saturated": "saturated_fat_content",
    "carbs": "carbohydrate_content",
    "sugar": "sugar_content",
    "protein": "protein_content",
    "fiber": "fiber_content",
}
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
KCAL_STEP = 10


def _half_up(value: float, digits: int = 0) -> float:
    """VALUE rounded to DIGITS decimals, halves upward (Python's round() goes to the even neighbour)."""
    factor = 10**digits
    return math.floor(value * factor + 0.5) / factor


def _rounded(nutrient: str, value: float | None) -> float | None:
    """VALUE for display: kcal to 10, grams from 10 g whole and below with one decimal, salt with one decimal."""
    if value is None:
        return None
    if nutrient == "kcal":
        return _half_up(value / KCAL_STEP) * KCAL_STEP
    return _half_up(value, 0 if nutrient != "salt" and value >= 10 else 1)


def _is_title(ingredient: RecipeIngredient) -> bool:
    """Whether the line is only a section title ("Für den Teig")."""
    return bool(ingredient.title) and not (ingredient.note or ingredient.food or ingredient.unit or ingredient.quantity)


def _number(text: str | None) -> float | None:
    """The first number in TEXT ("12,5 g" gives 12.5), or None."""
    match = NUMBER.search(text or "")
    return float(match.group().replace(",", ".")) if match else None


def _manual(nutrition: Nutrition | None) -> dict[str, float | None] | None:
    """The values a person entered in Mealie's nutrition fields, or None if the fields are all empty. Text without a
    number gives None for that value; sodium (mg) becomes salt."""
    if nutrition is None or not any(value and value.strip() for value in nutrition.model_dump().values()):
        return None
    values = {name: _number(getattr(nutrition, field)) for name, field in MEALIE_FIELDS.items()}
    sodium = _number(nutrition.sodium_content)
    values["salt"] = None if sodium is None else sodium * SALT_PER_SODIUM / 1000
    return values


def calculate(
    recipe: RecipeDraft | RecipeOut,
    mappings: dict[UUID, KhFoodNutrition],
    bls: dict[str, BlsFood],
    aliases: dict[str, str],
) -> NutritionOut:
    """The recipe's nutrition. MAPPINGS holds the stored food mappings by food ID, BLS the table and ALIASES the
    common foods' codes. A line counts when it has grams and a BLS entry; a suggested entry makes the result
    "estimated"."""
    servings = recipe.recipe_servings if recipe.recipe_servings and recipe.recipe_servings > 0 else None
    per = "serving" if servings else "recipe"
    manual = _manual(recipe.nutrition)
    if manual is not None:
        return NutritionOut(
            per="serving",
            servings=servings,
            values=NutritionValues(**manual),
            counted=0,
            total=0,
            missing=[],
            estimated=False,
            manual=True,
        )

    lines = [line for line in recipe.recipe_ingredient if not _is_title(line)]
    sums: dict[str, float | None] = dict.fromkeys(NUTRIENTS)
    missing: list[str] = []
    estimated = False
    for line in lines:
        row = mappings.get(line.food.id) if line.food and line.food.id else None
        code, suggested = resolve_code(line.food.name, row, bls, aliases) if line.food else (None, False)
        grams = grams_of(line, row.piece_grams if row else None)
        if grams is None or code not in bls:
            missing.append(line.display or line.original_text or "")
            continue
        estimated = estimated or suggested
        for nutrient in NUTRIENTS:
            per_100g = getattr(bls[code], nutrient)
            if per_100g is not None:
                sums[nutrient] = (sums[nutrient] or 0) + per_100g * grams / 100
    counted = len(lines) - len(missing)
    values = None
    if counted:
        values = NutritionValues(
            **{n: _rounded(n, None if v is None else v / (servings or 1)) for n, v in sums.items()}
        )
    return NutritionOut(
        per=per,
        servings=servings,
        values=values,
        counted=counted,
        total=len(lines),
        missing=missing,
        estimated=estimated,
        manual=False,
    )
