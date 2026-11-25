"""KH: changes to a draft's recognized recipe JSON made line by line in the review (D55). Each function takes the
recipe dict, changes it in place and raises a 422 for a place that does not exist."""

from typing import Any

from fastapi import HTTPException, status

from mealie.kh.amounts.parse import parse_ingredient
from mealie.kh.amounts.schemas import DraftAmounts, DraftStepAmount, IngredientExtraOut
from mealie.kh.amounts.service import amount_key
from mealie.kh.amounts.steps import recheck_link
from mealie.kh.i18n.locale import DEFAULT_LOCALE
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.services.parser_services._base import DataMatcher


def _line(recipe: dict[str, Any], key: str, index: int) -> dict[str, Any]:
    """The ingredient line or step at INDEX; 422 when the recipe has none there."""
    lines = recipe.get(key) or []
    if index >= len(lines):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail={"code": "index"})
    return lines[index]


def _amounts(recipe: dict[str, Any]) -> DraftAmounts:
    """The draft's amounts (range ends, fixed lines, step links) from its recipe JSON."""
    return DraftAmounts.model_validate(recipe.get("khAmounts") or {})


def _store(recipe: dict[str, Any], amounts: DraftAmounts) -> None:
    """Writes AMOUNTS back into the recipe JSON."""
    recipe["khAmounts"] = amounts.model_dump(mode="json", by_alias=True)


def edit_name(recipe: dict[str, Any], name: str) -> None:
    """Sets the recipe's name."""
    recipe["name"] = name


def edit_ingredient(
    recipe: dict[str, Any], index: int, text: str, matcher: DataMatcher, locale: str = DEFAULT_LOCALE
) -> None:
    """Reads TEXT the way the recognition reads a line and replaces the line at INDEX, keeping its reference ID and
    title; a text without an amount stays whole as the note. Its range end or fixed
    mark is replaced too, and its step links go when its amount changed."""
    line = _line(recipe, "recipeIngredient", index)
    parsed = parse_ingredient(text, matcher.units_by_alias, matcher.foods_by_alias, locale)
    if parsed.quantity is None:
        changes: dict[str, Any] = {"quantity": None, "unit": None, "food": None, "note": text}
    else:
        changes = {"quantity": parsed.quantity, "unit": parsed.unit, "food": parsed.food, "note": parsed.note}
    # validated anew so Mealie writes the display from the new fields
    new = RecipeIngredient.model_validate(line | changes | {"originalText": text, "display": ""})
    recipe["recipeIngredient"][index] = new.model_dump(mode="json", by_alias=True)
    amounts = _amounts(recipe)
    amounts.extras = [extra for extra in amounts.extras if extra.reference_id != new.reference_id]
    if amount_key(new) != amount_key(RecipeIngredient.model_validate(line)):
        # a step link's fraction refers to the old amount
        amounts.step_amounts = [link for link in amounts.step_amounts if link.reference_id != new.reference_id]
    if parsed.upper is not None or parsed.fixed:
        amounts.extras.append(IngredientExtraOut(reference_id=new.reference_id, upper=parsed.upper, fixed=parsed.fixed))
    _store(recipe, amounts)


def edit_step(recipe: dict[str, Any], index: int, text: str) -> None:
    """Sets the text of the step at INDEX and re-checks its links to ingredients: a link whose amount is gone from the
    text is dropped, the others follow their text."""
    _line(recipe, "recipeInstructions", index)["text"] = text
    amounts = _amounts(recipe)
    # recheck_link copies the link it gets, so a draft link keeps its "linked" mark
    rechecked = [link if link.step != index else recheck_link(text, link) for link in amounts.step_amounts]
    amounts.step_amounts = [link for link in rechecked if isinstance(link, DraftStepAmount)]
    _store(recipe, amounts)
