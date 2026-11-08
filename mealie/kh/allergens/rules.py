"""KH: the keyword rules that find the 14 EU allergens in ingredient texts (D44), and the per-recipe corrections.
The rules are data in data/rules.json; this module only applies them."""

import json
import re
import unicodedata
from functools import cache
from pathlib import Path

from mealie.kh.allergens.schemas import ALLERGENS, AllergenHit
from mealie.schema.recipe.recipe import Recipe

RULES_JSON = Path(__file__).parent / "data" / "rules.json"


@cache
def _rules() -> dict[str, dict[str, list[str]]]:
    """rules.json: per allergen the words that point to it ("match") and the words that cancel it ("except"). A
    match starting with "=" must be a whole word (the short "ei"); every other is a lowercase substring, which is
    how German compounds (Dinkelvollkornmehl) are found."""
    return json.loads(RULES_JSON.read_text(encoding="utf-8"))


def _normalized(text: str) -> str:
    """Lowercase with composed umlauts, so "Gemu" + combining diaeresis equals "Gemü"."""
    return unicodedata.normalize("NFC", text).lower()


def allergens_of_line(text: str) -> set[str]:
    """The allergens an ingredient text probably contains: a keyword matches, and no exception word of the same
    allergen is in the text (Buchweizenmehl is no gluten, Kokosmilch no milk)."""
    lowered = _normalized(text)
    words = set(re.findall(r"[^\W\d_]+", lowered))

    def hit(key: str) -> bool:
        return key[1:] in words if key.startswith("=") else key in lowered

    return {
        allergen
        for allergen, rule in _rules().items()
        if any(hit(key) for key in rule["match"]) and not any(hit(key) for key in rule["except"])
    }


def recipe_allergens(recipe: Recipe, corrections: dict[str, bool]) -> list[AllergenHit]:
    """The recipe's allergens in spec order with the ingredient lines they come from. A correction False keeps the
    allergen in the list with corrected=False (so it can be undone); True adds one the rules did not find."""
    lines: dict[str, list[str]] = {}
    for line in recipe.recipe_ingredient:
        shown = line.display or line.original_text or ""
        text = line.food.name if line.food else shown
        for allergen in allergens_of_line(text):
            lines.setdefault(allergen, []).append(shown or text)
    return [
        AllergenHit(allergen=allergen, lines=lines.get(allergen, []), corrected=corrections.get(allergen))
        for allergen in ALLERGENS
        if allergen in lines or allergen in corrections
    ]
