"""KH: reads ingredient lines without AI (D39, A1), German and English: amount, range and unit, and the food when
the group has it exactly. Mealie's NLP library leaves German units in the name, so only Mealie's matching of the
group's units and foods is used. Also adds the units Mealie's German or English set lacks, once per group."""

import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction

from mealie.db.models.recipe.ingredient import IngredientFoodModel, IngredientUnitModel
from mealie.kh.i18n.locale import DEFAULT_LOCALE
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe_ingredient import (
    IngredientFoodOut,
    IngredientUnitAliasCreate,
    IngredientUnitOut,
    IngredientUnitSave,
)
from mealie.services.parser_services._base import DataMatcher

VULGAR = "¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞"  # fraction characters, read as written in a step's text
# 1 1/2, 1/2, 1½ or 1 ½, 1.5, 3; never x/0. Lines are cleaned first; steps keep their characters, so links fit the text
NUMBER = rf"\d+\s+\d+/[1-9]\d*|\d+/[1-9]\d*|(?:\d+ ?)?[{VULGAR}]|\d+(?:\.\d+)?"
QUANTITY = re.compile(rf"(?P<value>{NUMBER})(?:\s*(?:-|–|—|bis|to)\s*(?P<upper>{NUMBER}))?")
WORD = re.compile(r"\S+")

FIXED_UNITS = {"prise", "messerspitze", "pinch", "dash"}  # normalized unit names that never scale
FIXED_WORDS = re.compile(r"\b(?:etwas|nach geschmack|some|to taste|as needed)\b", re.IGNORECASE)
ABOUT = re.compile(
    r"^(?:ca\.?|circa|etwa|ungefähr|rund|about|approx\.?|approximately|around)\s+(?=\d)", re.IGNORECASE
)  # "ca. 200 g": the amount follows
THOUSANDS = re.compile(r"(?<![\d.])([1-9]\d{0,2})((?:\.\d{3})+)(?![\d.])")  # "1.000" and "1.250,5", never "1.5"
PLURAL_MARKER = re.compile(r"(?<=[^\W\d_])\((?:n|en|e|er|s|nen)\)")  # a plural ending in brackets, glued on
ENDINGS = ("en", "er", "e", "n", "s")  # up to two are cut off by stem(), the longest first

# Kochheft's additions to Mealie's German units: name, plural, abbreviation
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
# the same for a group using Mealie's English units: name, plural, abbreviation
ENGLISH_UNITS = (
    ("piece", "pieces", "pc."),
    ("slice", "slices", ""),
    ("pot", "pots", ""),
    ("jar", "jars", ""),
    ("cube", "cubes", ""),
    ("sheet", "sheets", ""),
)
ENGLISH_PACK_ALIASES = ("pkg.", "packet", "package")
# English writes a comma between thousands ("1,000 g"), German a point ("1.000 g") and a comma for decimals
ENGLISH_THOUSANDS = re.compile(r"(?<![\d,.])([1-9]\d{0,2})((?:,\d{3})+)(?![\d,])")


@dataclass(frozen=True)
class ParsedLine:
    """One ingredient line as read: amount and range, unit, food, the rest as note, and whether it never scales."""

    quantity: float | None  # None: no amount recognized
    upper: float | None  # upper end of a range ("2–3" → 3)
    unit: IngredientUnitOut | None
    food: IngredientFoodOut | None  # only an exact match with the group's foods
    note: str  # the rest of the line; holds the name when no food matched
    fixed: bool  # never scaled: Prise, Messerspitze, "etwas", "nach Geschmack"


def is_english(locale: str) -> bool:
    """Whether numbers are written the English way (comma between thousands, point for decimals) in LOCALE."""
    return locale.startswith("en")


def clean(text: str, locale: str = DEFAULT_LOCALE) -> str:
    """The line in a form QUANTITY reads: plain spaces, fractions as 1/2 ("1½" → "1 1/2"), in German a decimal point
    instead of a comma (thousands points dropped), in English the thousands commas dropped, a space between a
    number and a unit written onto it ("250g" → "250 g"), and
    no plural endings in brackets ("Birne(n)" → "Birne")."""
    chars = []
    for index, char in enumerate(text):
        value = unicodedata.numeric(char, 0) if unicodedata.category(char) == "No" else 0
        if 0 < value < 1:
            fraction = Fraction(value).limit_denominator(16)
            space = " " if index and text[index - 1].isdigit() else ""
            chars.append(f"{space}{fraction.numerator}/{fraction.denominator}")
        else:
            chars.append(" " if char.isspace() else char)
    text = "".join(chars)
    if is_english(locale):
        text = ENGLISH_THOUSANDS.sub(lambda m: m.group(1) + m.group(2).replace(",", ""), text)
    else:
        text = THOUSANDS.sub(lambda m: m.group(1) + m.group(2).replace(".", ""), text)  # German: point groups
        text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    text = re.sub(r"(?<=\d)(?=[^\W\d_])", " ", text)
    text = PLURAL_MARKER.sub("", text)  # Chefkoch writes "Birne(n)", "Ei(er)", "Prise(n)"
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


def unit_at(text: str, units: dict[str, IngredientUnitOut]) -> tuple[IngredientUnitOut, int] | None:
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


def food_and_note(rest: str, foods: dict[str, IngredientFoodOut]) -> tuple[IngredientFoodOut | None, str]:
    """The food the rest names before a comma or parenthesis, if the group has it, and what remains as note; without
    such a food the whole rest is the note."""
    split = re.search(r"[,(]", rest)
    food = foods.get(IngredientFoodModel.normalize(rest[: split.start()] if split else rest))
    if food is None:
        return None, rest
    # a comma only separates; a parenthesis stays with what it encloses, "(Type 405)"
    return food, rest[split.start() :].lstrip(",").strip() if split else ""


def parse_ingredient(
    line: str, units: dict[str, IngredientUnitOut], foods: dict[str, IngredientFoodOut], locale: str = DEFAULT_LOCALE
) -> ParsedLine:
    """Reads one ingredient line; UNITS and FOODS are the group's, keyed like Mealie's DataMatcher, LOCALE decides
    how numbers are written. A line without an amount stays as it was, as note."""
    text = ABOUT.sub("", clean(line, locale))
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


def _add_units(
    repos: AllRepositories, extras: tuple[tuple[str, str, str], ...], known: dict[str, IngredientUnitOut]
) -> None:
    """Creates the units of EXTRAS the group does not have."""
    for name, plural, abbreviation in extras:
        if IngredientUnitModel.normalize(name) not in known:
            repos.ingredient_units.create(
                IngredientUnitSave(name=name, plural_name=plural, abbreviation=abbreviation, group_id=repos.group_id)
            )


def _add_pack_aliases(repos: AllRepositories, pack: IngredientUnitOut | None, wanted: tuple[str, ...]) -> None:
    """Adds the aliases WANTED to the group's pack unit (if it has one) that it does not know yet."""
    if pack is None:
        return
    known = {alias.name for alias in pack.aliases}
    aliases = [*pack.aliases, *(IngredientUnitAliasCreate(name=a) for a in wanted if a not in known)]
    data = pack.model_dump() | {"aliases": [alias.model_dump() for alias in aliases], "group_id": repos.group_id}
    repos.ingredient_units.update(pack.id, IngredientUnitSave.model_validate(data))


def ensure_german_units(repos: AllRepositories) -> None:
    """Adds Messerspitze, Stück, Scheibe, Becher, Glas, Würfel and Blatt, and the aliases "Pck." and "Päckchen" of
    Packung, to a group using Mealie's German units (it has "Esslöffel"). Once: a group with a Messerspitze is done,
    so a unit deleted on purpose stays deleted."""
    units = DataMatcher(repos).units_by_alias
    if "essloffel" not in units or "messerspitze" in units:
        return
    _add_units(repos, GERMAN_UNITS, units)
    _add_pack_aliases(repos, units.get("packung"), PACK_ALIASES)


def ensure_english_units(repos: AllRepositories) -> None:
    """Adds piece, slice, pot, jar, cube and sheet, and the aliases "pkg.", "packet" and "package" of pack, to a group
    using Mealie's English units (it has "teaspoon" and no "Esslöffel"). Once: a group with a piece is done."""
    units = DataMatcher(repos).units_by_alias
    if "teaspoon" not in units or "essloffel" in units or "piece" in units:
        return
    _add_units(repos, ENGLISH_UNITS, units)
    _add_pack_aliases(repos, units.get("pack"), ENGLISH_PACK_ALIASES)


def ensure_extra_units(repos: AllRepositories) -> None:
    """Adds Kochheft's extra units for the group's language, German or English, once."""
    ensure_german_units(repos)
    ensure_english_units(repos)
