"""KH: reads German ingredient lines without AI (D39, A1): amount, range and unit, and the food when the group has it
exactly. Mealie's NLP library leaves German units in the name, so only Mealie's matching of the group's units and
foods is used. Also adds the German units Mealie's German set lacks, once per group."""

import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction

from mealie.db.models.recipe.ingredient import IngredientFoodModel, IngredientUnitModel
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe_ingredient import (
    CreateIngredientUnitAlias,
    IngredientFood,
    IngredientUnit,
    SaveIngredientUnit,
)
from mealie.services.parser_services._base import DataMatcher

VULGAR = "¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞"  # fraction characters, read as written in a step's text
# 1 1/2, 1/2, 1½ or 1 ½, 1.5, 3; never x/0. Lines are cleaned first; steps keep their characters, so links fit the text
NUMBER = rf"\d+\s+\d+/[1-9]\d*|\d+/[1-9]\d*|(?:\d+ ?)?[{VULGAR}]|\d+(?:\.\d+)?"
QUANTITY = re.compile(rf"(?P<value>{NUMBER})(?:\s*(?:-|–|—|bis)\s*(?P<upper>{NUMBER}))?")
WORD = re.compile(r"\S+")

FIXED_UNITS = {"prise", "messerspitze"}  # normalized unit names that never scale
FIXED_WORDS = re.compile(r"\b(?:etwas|nach geschmack)\b", re.IGNORECASE)
ENDINGS = ("en", "er", "e", "n", "s")  # up to two are cut off by stem(), the longest first

# Küchenhelfer's additions to Mealie's German units: name, plural, abbreviation
GERMAN_UNITS = (
    ("Messerspitze", "Messerspitzen", "Msp."),
    ("Stück", "Stück", "Stk."),
    ("Scheibe", "Scheiben", ""),
    ("Becher", "Becher", ""),
    ("Glas", "Gläser", ""),
    ("Würfel", "Würfel", ""),
    ("Blatt", "Blätter", ""),
)
PACK_ALIASES = ("Pck.", "Päckchen")


@dataclass(frozen=True)
class ParsedLine:
    """One ingredient line as read: amount and range, unit, food, the rest as note, and whether it never scales."""

    quantity: float | None  # None: no amount recognized
    upper: float | None  # upper end of a range ("2–3" → 3)
    unit: IngredientUnit | None
    food: IngredientFood | None  # only an exact match with the group's foods
    note: str  # the rest of the line; holds the name when no food matched
    fixed: bool  # never scaled: Prise, Messerspitze, "etwas", "nach Geschmack"


def clean(text: str) -> str:
    """The line in a form QUANTITY reads: plain spaces, fractions as 1/2 ("1½" → "1 1/2"), a decimal point instead of
    a comma, and a space between a number and a unit written onto it ("250g" → "250 g")."""
    chars = []
    for index, char in enumerate(text):
        value = unicodedata.numeric(char, 0) if unicodedata.category(char) == "No" else 0
        if 0 < value < 1:
            fraction = Fraction(value).limit_denominator(16)
            space = " " if index and text[index - 1].isdigit() else ""
            chars.append(f"{space}{fraction.numerator}/{fraction.denominator}")
        else:
            chars.append(" " if char.isspace() else char)
    text = re.sub(r"(?<=\d),(?=\d)", ".", "".join(chars))
    text = re.sub(r"(?<=\d)(?=[^\W\d_])", " ", text)
    return re.sub(r" {2,}", " ", text).strip()


def number(text: str) -> float:
    """The value of a NUMBER: "1 1/2" → 1.5, "1/2" → 0.5, "1½" → 1.5, "1.5" → 1.5."""
    if text[-1] in VULGAR:
        return float(text[:-1] or 0) + unicodedata.numeric(text[-1])
    return float(sum(Fraction(part) for part in text.split()))


def amount_of(match: re.Match[str]) -> tuple[float, float | None]:
    """The value and the upper end of a QUANTITY match; no upper end for a single amount."""
    upper = match.group("upper")
    return number(match.group("value")), number(upper) if upper else None


def unit_at(text: str, units: dict[str, IngredientUnit]) -> tuple[IngredientUnit, int] | None:
    """The unit at the start of TEXT and where it ends: the next two words if they name one, else the next word."""
    words = list(WORD.finditer(text))[:2]
    for count in (2, 1):
        if len(words) >= count:
            unit = units.get(IngredientUnitModel.normalize(" ".join(w.group() for w in words[:count])))
            if unit:
                return unit, words[count - 1].end()
    return None


def cut_ending(word: str) -> str:
    """The word without one ending -en, -er, -e, -n or -s, keeping at least two letters."""
    for ending in ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= 2:
            return word[: -len(ending)]
    return word


def stem(word: str) -> str:
    """The word normalized like Mealie's names and without up to two endings, so "Eier" and "Eiern" meet "Ei" and
    "Möhren" meets "Möhre". Both sides of a comparison go through it, so a rough cut is enough."""
    return cut_ending(cut_ending(IngredientFoodModel.normalize(word)))


def food_and_note(rest: str, foods: dict[str, IngredientFood]) -> tuple[IngredientFood | None, str]:
    """The food the rest names before a comma or parenthesis, if the group has it, and what remains as note; without
    such a food the whole rest is the note."""
    split = re.search(r"[,(]", rest)
    food = foods.get(IngredientFoodModel.normalize(rest[: split.start()] if split else rest))
    if food is None:
        return None, rest
    # a comma only separates; a parenthesis stays with what it encloses, "(Type 405)"
    return food, rest[split.start() :].lstrip(",").strip() if split else ""


def parse_ingredient(line: str, units: dict[str, IngredientUnit], foods: dict[str, IngredientFood]) -> ParsedLine:
    """Reads one ingredient line; UNITS and FOODS are the group's, keyed like Mealie's DataMatcher. A line without an
    amount stays as it was, as note."""
    text = clean(line)
    match = QUANTITY.match(text)
    if match is None:  # "etwas Öl": only a line without an amount is fixed by its words
        return ParsedLine(None, None, None, None, line, bool(FIXED_WORDS.search(line)))
    quantity, upper = amount_of(match)
    rest = text[match.end() :]
    unit = None
    fixed = False
    if found := unit_at(rest, units):
        unit, end = found
        rest = rest[end:]
        fixed = IngredientUnitModel.normalize(unit.name) in FIXED_UNITS
    food, note = food_and_note(rest.strip(), foods)
    return ParsedLine(quantity, upper, unit, food, note, fixed)


def ensure_german_units(repos: AllRepositories) -> None:
    """Adds Messerspitze, Stück, Scheibe, Becher, Glas, Würfel and Blatt, and the aliases "Pck." and "Päckchen" of
    Packung, to a group using Mealie's German units (it has "Esslöffel"). Once: a group with a Messerspitze is done,
    so a unit deleted on purpose stays deleted."""
    units = DataMatcher(repos).units_by_alias
    if "essloffel" not in units or "messerspitze" in units:
        return
    for name, plural, abbreviation in GERMAN_UNITS:
        if IngredientUnitModel.normalize(name) not in units:
            repos.ingredient_units.create(
                SaveIngredientUnit(name=name, plural_name=plural, abbreviation=abbreviation, group_id=repos.group_id)
            )
    pack = units.get("packung")
    if pack is None:
        return
    known = {alias.name for alias in pack.aliases}
    aliases = [*pack.aliases, *(CreateIngredientUnitAlias(name=a) for a in PACK_ALIASES if a not in known)]
    data = pack.model_dump() | {"aliases": [alias.model_dump() for alias in aliases], "group_id": repos.group_id}
    repos.ingredient_units.update(pack.id, SaveIngredientUnit.model_validate(data))
