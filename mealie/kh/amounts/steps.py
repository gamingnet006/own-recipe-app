"""KH: amounts in the step text (D39, A2, D19): where a step names an ingredient's amount or a part of it
("125 g Mehl" for 250 g Mehl), the place is linked to that ingredient so the view can scale it; the text itself stays
as written. After an edit a link follows its text or goes."""

import re

from mealie.kh.amounts.parse import QUANTITY, WORD, amount_of, stem, unit_at
from mealie.kh.amounts.schemas import DraftStepAmount, StepAmountOut
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_ingredient import IngredientUnit, RecipeIngredient

PARTS = (1, 1 / 2, 1 / 3, 1 / 4, 2 / 3, 3 / 4)  # what a step may take of an ingredient
TOLERANCE = 0.02  # how far, relative, a step's amount may be from such a part (83 g of 250 g is ⅓)


def readable(text: str) -> str:
    """The text in the same length, written so QUANTITY reads it: plain spaces and decimal points."""
    text = "".join(" " if char.isspace() else char for char in text)
    return re.sub(r"(?<=\d),(?=\d)", ".", text)


def name_stem(ingredient: RecipeIngredient) -> str:
    """The stem a step names the ingredient by: its food, else the first word of its note."""
    words = WORD.findall(ingredient.food.name if ingredient.food else ingredient.note or "")
    return stem(words[0]) if words else ""


def part_of(value: float, quantity: float | None) -> float | None:
    """Which of PARTS VALUE is of QUANTITY, within TOLERANCE; None for any other share."""
    if not quantity:
        return None
    share = value / quantity
    return next((part for part in PARTS if abs(share - part) <= TOLERANCE * part), None)


def same_unit(ingredient: RecipeIngredient, unit: IngredientUnit | None) -> bool:
    """Whether the step's unit is the ingredient's, or neither has one."""
    own = getattr(ingredient.unit, "id", None)
    return own == (unit.id if unit else None)


def link_quantities(recipe: Recipe, units: dict[str, IngredientUnit]) -> list[DraftStepAmount]:
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
                if part and same_unit(ingredient, unit) and stem(words[0]) == name_stem(ingredient):
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
