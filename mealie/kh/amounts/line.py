"""KH: reads one line typed on the shopping page (D60), "2 Liter Milch 3,5 %": amount, unit and the article, which is
the group's food when it has one, else the text that is left. The name never holds a digit, a percentage or a unit
word, even when the group has neither the unit nor the food. Built on parse_ingredient."""

import json
import re
from dataclasses import dataclass
from functools import lru_cache

from mealie.db.models.recipe.ingredient import IngredientFoodModel, IngredientUnitModel
from mealie.kh.amounts.parse import parse_ingredient, stem
from mealie.repos.seed._abstract_seeder import AbstractSeeder
from mealie.schema.recipe.recipe_ingredient import IngredientFoodOut, IngredientUnitOut

PERCENT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")  # "3,5%", "1.5 %"
DECIMAL_POINT = re.compile(r"(?<=\d)\.(?=\d)")  # parse_ingredient turned "3,5" into "3.5"; the note is read by Germans

# The units the amount chips use, by every way of writing them: the abbreviation the client asks the server to ensure
STANDARD_UNIT_WORDS = {
    "g": "g", "gramm": "g", "kg": "kg", "kilo": "kg", "kilogramm": "kg", "ml": "ml", "milliliter": "ml",
    "l": "l", "liter": "l",
}  # fmt: skip
# Words of the shopping list that are no standard unit: kept in the note when the group has no such unit
SHOPPING_WORDS = (
    "Packung", "Packungen", "Pck.", "Flasche", "Flaschen", "Becher", "Dose", "Dosen", "Glas", "Gläser", "Stück", "Stk.",
    "Beutel", "Netz", "Kiste", "Kasten", "Tüte", "Tüten", "Rolle", "Rollen",
)  # fmt: skip


@dataclass(frozen=True)
class ShoppingLine:
    """What a typed line says: amount (None without one), the unit (the group's, or the abbreviation of a standard
    unit it lacks), the food if the group has it, the article's name, and the rest as note."""

    quantity: float | None
    unit: IngredientUnitOut | None
    unit_abbreviation: str | None
    food: IngredientFoodOut | None
    name: str
    note: str


def key(word: str) -> str:
    """A unit word as compared: normalized by Mealie, without a closing point ("Stk." is "stk")."""
    return IngredientUnitModel.normalize(word.rstrip("."))


@lru_cache(maxsize=1)
def unit_words() -> frozenset[str]:
    """Every unit word of Mealie's German seed (names, plurals, abbreviations) and of the shopping list."""
    path = AbstractSeeder.resources / "units" / "locales" / "de-DE.json"
    words = list(SHOPPING_WORDS)
    for unit in json.loads(path.read_text(encoding="utf-8")).values():
        words += [unit.get("name", ""), unit.get("plural_name", ""), unit.get("abbreviation", "")]
    return frozenset(key(word) for word in words if word) | frozenset(STANDARD_UNIT_WORDS)


def find_food(rest: str, foods: dict[str, IngredientFoodOut]) -> tuple[IngredientFoodOut | None, str]:
    """The food the longest start of REST names (also in another number: "Eier" for "Ei") and the words after it."""
    by_stem = {stem(key): food for key, food in foods.items()}
    words = rest.split()
    for count in range(len(words), 0, -1):
        normalized = IngredientFoodModel.normalize(" ".join(words[:count]))
        food = foods.get(normalized) or by_stem.get(stem(normalized))
        if food:
            return food, " ".join(words[count:])
    return None, rest


def parse_shopping_line(
    text: str, units: dict[str, IngredientUnitOut], foods: dict[str, IngredientFoodOut]
) -> ShoppingLine:
    """Reads TEXT; UNITS and FOODS are the group's, keyed like Mealie's DataMatcher. Percentages and other digits go to
    the note, a unit word the group lacks is split off too (a standard one as abbreviation, any other into the note).
    Raises ValueError when no article is left."""
    notes = [f"{value.replace('.', ',')} %" for value in PERCENT.findall(text)]
    parsed = parse_ingredient(PERCENT.sub(" ", text), units, foods)
    unit, abbreviation, rest = parsed.unit, None, parsed.note
    food = parsed.food
    if food is None and parsed.quantity is not None and unit is None:
        first, _, after = rest.strip().partition(" ")
        if key(first) in unit_words():
            abbreviation = STANDARD_UNIT_WORDS.get(key(first))
            if not abbreviation:
                notes.insert(0, first)
            rest = after
    if food is None:
        food, rest = find_food(rest.strip(), foods)
    words = rest.split()
    # digits never stay in the name, with the unit word behind them: "Toilettenpapier 8 Rollen" has the name
    # Toilettenpapier and the note "8 Rollen"
    article: list[str] = []
    for index, word in enumerate(words):
        if re.search(r"\d", word):
            notes.append(DECIMAL_POINT.sub(",", word))
        elif index and re.search(r"\d", words[index - 1]) and key(word) in unit_words():
            notes.append(word)
        else:
            article.append(word)
    if food:
        name, notes = food.name, [*notes, *article]
    else:
        name = " ".join(article)
        name = name[:1].upper() + name[1:]
    if not name:
        raise ValueError("no article")
    return ShoppingLine(parsed.quantity, unit, abbreviation, food, name, " ".join(notes))
