"""KH: how many grams an ingredient line weighs (D44): its quantity, unit and food against data/weights.json.
A line that cannot be weighed gives None and is then not counted in the nutrition."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from mealie.db.models.recipe import IngredientUnitModel
from mealie.kh.amounts.parse import stem
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient

WEIGHTS_JSON = Path(__file__).parent / "data" / "weights.json"
DEFAULT_DENSITY = 1.0  # g per ml for a food the table does not know


@lru_cache
def _weights() -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    """The units (by normalized name) and the foods (by stem) of weights.json."""
    data = json.loads(WEIGHTS_JSON.read_text(encoding="utf-8"))
    units = {IngredientUnitModel.normalize(name): value for name, value in data["units"].items()}
    foods = {stem(name): value for name, value in data["foods"].items()}
    return units, foods


def name_stems(food_name: str) -> list[str]:
    """The stems to try for a food name: the whole name's first, then each word's from the right (the noun comes
    last in German), so "Rote Zwiebeln" finds Zwiebel and "Grüne Bohnen" Bohne, not Grünkohl."""
    return [stem(food_name), *[stem(word) for word in reversed(food_name.split())]]


def food_entry(food_name: str) -> dict[str, float]:
    """The table's entry (density, piece) for a food name, found by name_stems or as the last part of a
    compound; empty if the table does not know it."""
    foods = _weights()[1]
    stems = name_stems(food_name)
    exact = next((foods[key] for key in stems if key in foods), None)
    if exact is not None:
        return exact
    # a compound weighs like its last part: Weizenmehl like Mehl, Rapsöl like Öl; at least three letters must come
    # before that part, so Brei is no Ei
    for word in stems[1:]:
        tail = max((key for key in foods if word.endswith(key) and len(word) - len(key) >= 3), key=len, default=None)
        if tail:
            return foods[tail]
    return {}


def _unit_entry(ingredient: RecipeIngredient) -> dict[str, Any] | None:
    """The table's entry ({"g": n} or {"ml": n}) for the line's unit, found by name, plural, abbreviation or alias."""
    unit = ingredient.unit
    if unit is None:
        return None
    names = [unit.name, unit.plural_name, unit.abbreviation, unit.plural_abbreviation]
    names += [alias.name for alias in unit.aliases]
    units = _weights()[0]
    return next((units[n] for n in (IngredientUnitModel.normalize(n) for n in names if n) if n in units), None)


def grams_of(ingredient: RecipeIngredient, piece_grams: float | None = None) -> float | None:
    """The line's weight in grams, or None if it has no quantity, no known unit or no piece weight. PIECE_GRAMS is the
    food's own piece weight; it goes before the table's."""
    if not ingredient.quantity or ingredient.quantity <= 0:
        return None
    entry = food_entry(ingredient.food.name) if ingredient.food else {}
    unit = _unit_entry(ingredient) if ingredient.unit else None
    if ingredient.unit and unit is None:
        return None
    if unit is None or "piece" in unit:  # no unit, or a unit that counts pieces (Stück, Zehe)
        # piece_default: a clove of garlic weighs 4 g, though "Knoblauch" has no piece weight
        piece = piece_grams or entry.get("piece") or (unit or {}).get("piece_default")
        return ingredient.quantity * piece if piece else None
    if "g" in unit:
        return ingredient.quantity * unit["g"]
    return ingredient.quantity * unit["ml"] * entry.get("density", DEFAULT_DENSITY)
