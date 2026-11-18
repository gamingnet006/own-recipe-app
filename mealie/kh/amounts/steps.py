"""KH: amounts in the step text (D39, A2, D19): where a step names an ingredient's amount or a part of it
("125 g Mehl" for 250 g Mehl), the place is linked to that ingredient so the view can scale it; the text itself stays
as written. After an edit a link follows its text or goes."""

import re
from itertools import dropwhile

from mealie.kh.amounts.parse import QUANTITY, WORD, amount_of, stem, unit_at
from mealie.kh.amounts.schemas import DraftStepAmount, StepAmountOut
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut
from mealie.schema.recipe.recipe_ingredient import IngredientUnitOut, RecipeIngredient
from mealie.schema.recipe.recipe_step import IngredientReferences

PARTS = (1, 1 / 2, 1 / 3, 1 / 4, 2 / 3, 3 / 4)  # what a step may take of an ingredient
PART_WORDS = ("gelb", "weiß", "dotter", "klar")  # a step names the part of an egg it uses: "2 Eigelbe"
LETTERS = re.compile(r"[^\W\d_]+")  # the words of a text, without numbers and punctuation
# a first step that only says what the recipe makes, as pages read without AI carry it: "Für 12 Muffins."
YIELD_STEP = re.compile(r"^\s*(?:für|ergibt)\s+(?:ca\.\s*)?(\d+)\s+([^\W\d_][\w-]*)\s*[.:]?\s*$", re.IGNORECASE)
UNIT_WORD_MAX = 3  # a short lowercase word before a note's name is a unit (g, ml, kg)
TOLERANCE = 0.02  # how far, relative, a step's amount may be from such a part (83 g of 250 g is ⅓)


def readable(text: str) -> str:
    """The text in the same length, written so QUANTITY reads it: plain spaces and decimal points."""
    text = "".join(" " if char.isspace() else char for char in text)
    return re.sub(r"(?<=\d),(?=\d)", ".", text)


def name_stems(ingredient: RecipeIngredient, units: dict[str, IngredientUnitOut] | None = None) -> set[str]:
    """The stems a step names the ingredient by: its food, else the first word of its note after a unit left there
    ("ml Milch" names Milch; UNITS are the group's, a short lowercase word counts too), and that word joined with a
    part of it ("Eigelb" for "Ei"); empty without a name."""
    text = ingredient.food.name if ingredient.food else ingredient.note or ""
    found = unit_at(text, units) if units and not ingredient.food else None
    words = LETTERS.findall(text[found[1] :] if found else text)
    if not ingredient.food:  # a unit the group does not know ("g", "ml"): German food names start with a capital
        words = list(dropwhile(lambda word: word.islower() and len(word) <= UNIT_WORD_MAX, words))
    if not words:
        return set()
    base = stem(words[0])
    return {base, *(stem(base + part) for part in PART_WORDS)}


def part_of(value: float, quantity: float | None) -> float | None:
    """Which of PARTS VALUE is of QUANTITY, within TOLERANCE; None for any other share."""
    if not quantity:
        return None
    share = value / quantity
    return next((part for part in PARTS if abs(share - part) <= TOLERANCE * part), None)


def same_unit(ingredient: RecipeIngredient, unit: IngredientUnitOut | None) -> bool:
    """Whether the step's unit is the ingredient's, or neither has one."""
    own = getattr(ingredient.unit, "id", None)
    return own == (unit.id if unit else None)


def link_quantities(recipe: RecipeDraft | RecipeOut, units: dict[str, IngredientUnitOut]) -> list[DraftStepAmount]:
    """Every place in the steps that names an ingredient's amount or a part of it: number, then the ingredient's
    unit (or none for both), then a word with the stem of the ingredient's name. A range in a step stays free."""
    links: list[DraftStepAmount] = []
    for place, step in enumerate(recipe.recipe_instructions or []):
        text = readable(step.text)
        for match in QUANTITY.finditer(text):
            value, upper = amount_of(match)
            after = text[match.end() :]
            found = unit_at(after, units)
            unit, end = found if found else (None, 0)
            words = WORD.findall(after[end:])
            if upper is not None or not words:
                continue
            for ingredient in recipe.recipe_ingredient:
                part = part_of(value, ingredient.quantity)
                if part and same_unit(ingredient, unit) and stem(words[0]) in name_stems(ingredient, units):
                    start, stop = match.start(), match.end() + end
                    links.append(
                        DraftStepAmount(
                            step=place,
                            start=start,
                            end=stop,
                            text=step.text[start:stop],
                            reference_id=ingredient.reference_id,
                            fraction=part,
                        )
                    )
                    break
    return links


def recheck_link(text: str, link: StepAmountOut) -> StepAmountOut | None:
    """The link for the step's text as it is now: at the place of its text nearest the old one (the old place where
    it still stands), and None when the text is gone. Never inside another number ("1250 g")."""
    pattern = re.compile(rf"(?<![\d.,/]){re.escape(link.text)}(?![\d.,/])")
    places = [match.start() for match in pattern.finditer(text)]
    if not places:
        return None
    start = min(places, key=lambda place: abs(place - link.start))
    return link.model_copy(update={"start": start, "end": start + len(link.text)})


def link_steps(recipe: RecipeDraft | RecipeOut, units: dict[str, IngredientUnitOut]) -> None:
    """Links each step to the ingredients its text names, for recipes whose steps came without links (pages read
    without AI). Steps that are linked already, by the AI or a person, leave the whole recipe as it is."""
    steps = recipe.recipe_instructions or []
    if any(step.ingredient_references for step in steps):
        return
    for step in steps:
        named = {stem(word) for word in LETTERS.findall(step.text)}
        step.ingredient_references = [
            IngredientReferences(reference_id=line.reference_id)
            for line in recipe.recipe_ingredient
            if line.reference_id and name_stems(line, units) & named
        ]


def yield_from_steps(recipe: RecipeDraft | RecipeOut) -> None:
    """Turns a first step that only names the yield ("Für 12 Muffins.") into servings and yield, when the recipe has
    no servings of its own (none or 1); otherwise the steps stay as they are."""
    steps = recipe.recipe_instructions or []
    found = YIELD_STEP.match(steps[0].text) if steps else None
    if found is None or (recipe.recipe_servings or 0) > 1:
        return
    count = float(found.group(1))
    recipe.recipe_servings, recipe.recipe_yield_quantity, recipe.recipe_yield = count, count, found.group(2)
    recipe.recipe_instructions = steps[1:]
