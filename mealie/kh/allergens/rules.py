"""KH: the keyword rules that find the 14 EU allergens in ingredient texts (D44), and the per-recipe corrections.
The rules are data in data/rules.json; this module only applies them."""

import json
import re
import unicodedata
from collections.abc import Iterable
from functools import cache, lru_cache
from pathlib import Path

from mealie.kh.allergens.schemas import ALLERGENS, AllergenHit
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient

RULES_JSON = Path(__file__).parent / "data" / "rules.json"


@cache
def _rules() -> dict[str, dict[str, list[str]]]:
    """rules.json: per allergen the words that point to it ("match"), the compounds cut out of the text before
    matching ("except": Buchweizenmehl is no gluten, but Kartoffelbrot still is) and the words that cancel the
    allergen for the whole text ("cancel": glutenfrei, vegan). A match starting with "=" must be a whole word (the
    short "ei"); every other is a lowercase substring, which is how German compounds (Dinkelvollkornmehl) are found."""
    rules = json.loads(RULES_JSON.read_text(encoding="utf-8"))
    for rule in rules.values():
        for kind in ("match", "except", "cancel"):
            rule[kind] = [_normalized(word) for word in rule[kind]]  # "eiweiß" meets "Eiweiss"
        rule["except"].sort(key=len, reverse=True)  # Buchweizenmehl is cut before Buchweizen
    return rules


def _normalized(text: str) -> str:
    """Lowercase with composed umlauts and "ss" for "ß", so "Gemu" + combining diaeresis equals "Gemü" and "Eiweiss"
    equals "Eiweiß"."""
    return unicodedata.normalize("NFC", text).lower().replace("ß", "ss")


def text_has(text: str, key: str) -> bool:
    """Whether TEXT contains the rule word KEY (a lowercase substring, or a whole word when it starts with "=")."""
    lowered = _normalized(text)
    if key.startswith("="):
        return key[1:] in re.findall(r"[^\W\d_]+", lowered)
    return key in lowered


@lru_cache(maxsize=4096)  # the rules are static data and "Butter", "Salz", "Mehl" repeat across hundreds of recipes
def allergens_of_line(text: str) -> frozenset[str]:
    """The allergens an ingredient text probably contains: a keyword matches in the text with the allergen's
    exception compounds cut out (Kokosmilch is no milk, Kakaomilch is), unless a cancel word is in the text.
    A frozenset, because the result is cached."""
    found = set()
    for allergen, rule in _rules().items():
        cut = _normalized(text)
        for compound in rule["except"]:
            cut = cut.replace(compound, " ")
        if any(text_has(cut, key) for key in rule["match"]) and not any(text_has(text, key) for key in rule["cancel"]):
            found.add(allergen)
    return frozenset(found)


def line_text(line: RecipeIngredient) -> tuple[str, str]:
    """An ingredient line as (shown, checked): the text the family sees, and the text the rules read, which is the
    food's name when the line has a food and the shown text otherwise."""
    shown = line.display or line.original_text or ""
    return shown, line.food.name if line.food else shown


def recipe_allergens(recipe: RecipeDraft | RecipeOut, corrections: dict[str, bool]) -> list[AllergenHit]:
    """The recipe's allergens, see lines_allergens."""
    return lines_allergens(recipe.recipe_ingredient, corrections)


def lines_allergens(lines: Iterable[RecipeIngredient], corrections: dict[str, bool]) -> list[AllergenHit]:
    """The allergens of ingredient LINES in spec order with the lines they come from (so a caller that has only the
    lines need not load a whole recipe). A correction False keeps the allergen in the list with corrected=False (so
    it can be undone); True adds one the rules did not find."""
    found_in: dict[str, list[str]] = {}
    for line in lines:
        shown, text = line_text(line)
        for allergen in allergens_of_line(text):
            found_in.setdefault(allergen, []).append(shown or text)
    return [
        AllergenHit(allergen=allergen, lines=found_in.get(allergen, []), corrected=corrections.get(allergen))
        for allergen in ALLERGENS
        if allergen in found_in or allergen in corrections
    ]
