"""KH: hints for the review on what looks wrong (D39, A6): lines without a recognized amount, unusual amounts, times
over a day, temperatures out of an oven's range, ingredients no step uses, and units converted from American ones."""

import re

from mealie.db.models.recipe.ingredient import IngredientUnitModel
from mealie.kh.amounts.parse import stem
from mealie.kh.amounts.service import ReadAmounts
from mealie.kh.drafts.schemas import DraftWarning
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient

MAX_GRAMS = 5000  # g or ml
MAX_KILOS = 5  # kg or l
MAX_SPOONS = 20  # EL or TL
MAX_PINCHES = 3
MAX_PIECES = 30  # no unit, or Stück
MAX_HOURS = 24
MIN_CELSIUS = 30
MAX_CELSIUS = 300
IMPERIAL = ("cup", "cups", "oz", "lb", "tbsp", "tsp", "°F")

# the limit by the unit's normalized name; a line without a unit counts as pieces
LIMITS = {
    **dict.fromkeys(("gramm", "gram", "milliliter", "millilitre"), MAX_GRAMS),
    **dict.fromkeys(("kilogramm", "kilogram", "liter", "litre"), MAX_KILOS),
    **dict.fromkeys(("essloffel", "teeloffel", "tablespoon", "teaspoon"), MAX_SPOONS),
    **dict.fromkeys(("prise", "pinch"), MAX_PINCHES),
    **dict.fromkeys(("stuck", "piece"), MAX_PIECES),
}
METRIC = {"gramm", "gram", "milliliter", "millilitre", "kilogramm", "kilogram", "liter", "litre"}
TEMPERATURE = re.compile(r"(\d+)\s*°\s*([CF])\b")
IMPERIAL_WORDS = re.compile(
    "|".join(rf"\b{re.escape(w)}\b" if w[0].isalpha() else re.escape(w) for w in sorted(IMPERIAL, key=len)[::-1]),
    re.IGNORECASE,
)
LETTERS = re.compile(r"[^\W\d_]{2,}")  # words of two letters or more, without numbers
FILLERS = {
    stem(word)
    for word in (
        "etwas",
        "und",
        "oder",
        "nach",
        "Geschmack",
        "zum",
        "für",
        "eine",
        "ein",
        "some",
        "and",
        "or",
        "to",
        "taste",
        "for",
        "a",
        "an",
        "of",
        "the",
    )
}


def unit_name(ingredient: RecipeIngredient) -> str:
    """The line's unit name, normalized; empty without a unit."""
    return IngredientUnitModel.normalize(ingredient.unit.name) if ingredient.unit else ""


def line_text(ingredient: RecipeIngredient) -> str:
    """The line as the source wrote it, else as Mealie shows it."""
    return ingredient.original_text or ingredient.display or ingredient.note or ""


def unusual_amounts(recipe: RecipeDraft | RecipeOut) -> list[DraftWarning]:
    """Lines with more than their unit's limit, e.g. 6000 g or 25 EL."""
    found = []
    for ingredient in recipe.recipe_ingredient:
        limit = LIMITS.get(unit_name(ingredient)) if ingredient.unit else MAX_PIECES
        if ingredient.quantity and limit is not None and ingredient.quantity > limit:
            found.append(DraftWarning(kind="amount_unusual", name=line_text(ingredient)))
    return found


def unusual_times(recipe: RecipeDraft | RecipeOut) -> list[DraftWarning]:
    """Times over a day."""
    times = (
        (recipe.prep_time_seconds, recipe.prep_time),
        (recipe.perform_time_seconds, recipe.perform_time),
        (recipe.total_time_seconds, recipe.total_time),
    )
    return [
        DraftWarning(kind="time_unusual", name=text or f"{round(seconds / 3600)} h")
        for seconds, text in times
        if seconds and seconds > MAX_HOURS * 3600
    ]


def unusual_temperatures(recipe: RecipeDraft | RecipeOut) -> list[DraftWarning]:
    """Temperatures in the steps below or above an oven's range, and any in °F."""
    found = []
    for step in recipe.recipe_instructions or []:
        for match in TEMPERATURE.finditer(step.text):
            if match.group(2) == "F" or not MIN_CELSIUS <= int(match.group(1)) <= MAX_CELSIUS:
                found.append(DraftWarning(kind="temperature_unusual", name=match.group(0)))
    return found


def unused_ingredients(recipe: RecipeDraft | RecipeOut) -> list[DraftWarning]:
    """Lines whose name no step uses, compared by stem; filler words such as "etwas" name nothing."""
    used = {stem(word) for step in recipe.recipe_instructions or [] for word in LETTERS.findall(step.text)}
    found = []
    for ingredient in recipe.recipe_ingredient:
        name = ingredient.food.name if ingredient.food else ingredient.note or ""
        names = {stem(word) for word in LETTERS.findall(name)} - FILLERS
        if names and not names & used:
            found.append(DraftWarning(kind="ingredient_unused", name=name))
    return found


def converted_units(recipe: RecipeDraft | RecipeOut, source_text: str | None) -> list[DraftWarning]:
    """One hint when the source names American units and the result has metric ones: the AI converted them."""
    words = list(dict.fromkeys(match.group(0).lower() for match in IMPERIAL_WORDS.finditer(source_text or "")))
    metric = any(unit_name(ingredient) in METRIC for ingredient in recipe.recipe_ingredient)
    return [DraftWarning(kind="units_converted", name=", ".join(words))] if words and metric else []


def plausibility_warnings(
    recipe: RecipeDraft | RecipeOut, read: ReadAmounts, source_text: str | None
) -> list[DraftWarning]:
    """Every hint for the review on what looks wrong; SOURCE_TEXT is a text draft's own text, else None."""
    unparsed = [DraftWarning(kind="amount_unparsed", name=line) for line in read.unparsed]
    return (
        unparsed
        + unusual_amounts(recipe)
        + unusual_times(recipe)
        + unusual_temperatures(recipe)
        + unused_ingredients(recipe)
        + converted_units(recipe, source_text)
    )
