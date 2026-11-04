"""KH: the amounts in a recipe's life (D39): read when a draft is recognized, saved with the approval under the saved
recipe's IDs, read for the views, and deleted with the recipe."""

from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.amounts.models import KhIngredientExtra, KhStepAmount
from mealie.kh.amounts.parse import ensure_german_units, parse_ingredient
from mealie.kh.amounts.schemas import AmountsOut, DraftAmounts, IngredientExtraOut, StepAmountOut
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.services.parser_services._base import DataMatcher


@dataclass
class ReadAmounts:
    """What reading a recipe's lines found beyond Mealie's fields, and the lines without an amount."""

    extras: list[IngredientExtraOut]
    unparsed: list[str]


def text_only(ingredient: RecipeIngredient) -> bool:
    """Whether a line is still text, as imports leave it: no quantity, unit or food, but a note."""
    return not ingredient.quantity and not ingredient.unit and not ingredient.food and bool(ingredient.note)


def read_amounts(repos: AllRepositories, recipe: Recipe) -> ReadAmounts:
    """Reads the recipe's text-only lines in place, with the group's units and foods; adds the German units once
    first. A line without an amount stays as it was."""
    ensure_german_units(repos)
    matcher = DataMatcher(repos)
    extras: list[IngredientExtraOut] = []
    unparsed: list[str] = []
    for index, ingredient in enumerate(recipe.recipe_ingredient):
        if not text_only(ingredient):
            continue
        line = ingredient.note or ""
        parsed = parse_ingredient(line, matcher.units_by_alias, matcher.foods_by_alias)
        if parsed.upper is not None or parsed.fixed:
            extras.append(
                IngredientExtraOut(reference_id=ingredient.reference_id, upper=parsed.upper, fixed=parsed.fixed)
            )
        if parsed.quantity is None:
            if not parsed.fixed:
                unparsed.append(line)
            continue
        changes = {"quantity": parsed.quantity, "unit": parsed.unit, "food": parsed.food, "note": parsed.note}
        # validated anew so Mealie writes the display from the new fields
        recipe.recipe_ingredient[index] = RecipeIngredient.model_validate(
            ingredient.model_dump() | changes | {"original_text": line, "display": ""}
        )
    return ReadAmounts(extras, unparsed)


def saved_ids(draft_recipe: dict[str, Any], saved: Recipe) -> dict[str, UUID4]:
    """The draft's ingredient IDs mapped to the saved recipe's, by position in the list."""
    pairs = zip(draft_recipe.get("recipeIngredient") or [], saved.recipe_ingredient, strict=False)
    return {str(line.get("referenceId")): ingredient.reference_id for line, ingredient in pairs}


def save_amounts(session: Session, draft_recipe: dict[str, Any], saved: Recipe) -> None:
    """Saves what the draft carries under the saved recipe's IDs; commits."""
    amounts = DraftAmounts.model_validate(draft_recipe.get("khAmounts") or {})
    ids = saved_ids(draft_recipe, saved)
    for extra in amounts.extras:
        if (reference_id := ids.get(str(extra.reference_id))) is not None:
            session.add(
                KhIngredientExtra(
                    session=session,
                    recipe_id=saved.id,
                    reference_id=reference_id,
                    upper=extra.upper,
                    fixed=extra.fixed,
                )
            )
    session.commit()


def load_amounts(session: Session, recipe_id: UUID4) -> AmountsOut:
    """A saved recipe's amounts, links in the order of their steps and places."""
    extras = session.execute(sa.select(KhIngredientExtra).where(KhIngredientExtra.recipe_id == recipe_id)).scalars()
    steps = session.execute(
        sa.select(KhStepAmount).where(KhStepAmount.recipe_id == recipe_id).order_by(KhStepAmount.start)
    ).scalars()
    return AmountsOut(
        extras=[IngredientExtraOut.model_validate(row) for row in extras],
        step_amounts=[StepAmountOut.model_validate(row) for row in steps],
    )


def delete_amounts(session: Session, recipe_ids: list[UUID4]) -> None:
    """Deletes the amounts of deleted recipes; SQLite in Mealie checks no foreign keys, so the cascade is not enough.
    Commits."""
    for model in (KhIngredientExtra, KhStepAmount):
        session.execute(sa.delete(model).where(model.recipe_id.in_(recipe_ids)))
    session.commit()
