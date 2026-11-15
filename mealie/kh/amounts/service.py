"""KH: the amounts in a recipe's life (D39): read and linked when a draft is recognized, saved with the approval under
the saved recipe's IDs, followed after an edit, read for the views, and deleted with the recipe."""

from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.amounts.models import KhIngredientExtra, KhStepAmount
from mealie.kh.amounts.parse import ensure_german_units, parse_ingredient
from mealie.kh.amounts.schemas import AmountsOut, DraftAmounts, DraftStepAmount, IngredientExtraOut, StepAmountOut
from mealie.kh.amounts.steps import link_quantities, recheck_link
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.schema.recipe.recipe_step import RecipeStep
from mealie.services.parser_services._base import DataMatcher


@dataclass
class ReadAmounts:
    """What reading a recipe's lines found beyond Mealie's fields, the lines without an amount, and the amounts in the
    steps linked to a line."""

    extras: list[IngredientExtraOut]
    unparsed: list[str]
    links: list[DraftStepAmount]


def text_only(ingredient: RecipeIngredient) -> bool:
    """Whether a line is still text, as imports leave it: no quantity, unit or food, but a note."""
    return not ingredient.quantity and not ingredient.unit and not ingredient.food and bool(ingredient.note)


def read_amounts(repos: AllRepositories, recipe: RecipeDraft | RecipeOut) -> ReadAmounts:
    """Reads the recipe's text-only lines in place, with the group's units and foods, and links the steps' amounts
    to the lines; adds the German units once first. A line without an amount stays as it was."""
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
    return ReadAmounts(extras, unparsed, link_quantities(recipe, matcher.units_by_alias))


def saved_ids(draft_recipe: dict[str, Any], saved: RecipeOut) -> dict[str, UUID4]:
    """The draft's ingredient IDs mapped to the saved recipe's, by position in the list."""
    pairs = zip(draft_recipe.get("recipeIngredient") or [], saved.recipe_ingredient, strict=False)
    return {str(line.get("referenceId")): ingredient.reference_id for line, ingredient in pairs}


def save_amounts(session: Session, draft_recipe: dict[str, Any], saved: RecipeOut, linked: list[int] | None) -> None:
    """Saves what the draft carries under the saved recipe's IDs; LINKED are the indices of its step links the review
    kept, None keeps those the recognition linked. Commits."""
    amounts = DraftAmounts.model_validate(draft_recipe.get("khAmounts") or {})
    ids = saved_ids(draft_recipe, saved)
    kept = linked if linked is not None else [i for i, link in enumerate(amounts.step_amounts) if link.linked]
    for link in (amounts.step_amounts[i] for i in kept):
        if (reference_id := ids.get(str(link.reference_id))) is not None:
            fields = link.model_dump(include={"step", "start", "end", "text", "fraction"})
            session.add(KhStepAmount(session=session, recipe_id=saved.id, reference_id=reference_id, **fields))
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
    """A saved recipe's amounts; the links by step and place."""
    extras = session.execute(sa.select(KhIngredientExtra).where(KhIngredientExtra.recipe_id == recipe_id)).scalars()
    steps = session.execute(
        sa.select(KhStepAmount)
        .where(KhStepAmount.recipe_id == recipe_id)
        .order_by(KhStepAmount.step, KhStepAmount.start)
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


def new_places(before: RecipeOut, sent: list[RecipeStep]) -> dict[int, int]:
    """Where each step of BEFORE stands in SENT, the steps as the editor sent them: they carry the old IDs in the new
    order, while Mealie gives the saved steps new IDs."""
    sent_ids = [step.id for step in sent]
    return {
        old: sent_ids.index(step.id)
        for old, step in enumerate(before.recipe_instructions or [])
        if step.id is not None and step.id in sent_ids
    }


def amount_key(ingredient: RecipeIngredient) -> tuple[float | None, UUID4 | None]:
    """What a line's range end, fixed mark and step links depend on: its quantity and unit."""
    return ingredient.quantity, ingredient.unit.id if ingredient.unit else None


def kept_lines(before: RecipeOut, saved: RecipeOut) -> set[UUID4]:
    """The lines of SAVED that BEFORE had with the same quantity and unit."""
    old = {ingredient.reference_id: amount_key(ingredient) for ingredient in before.recipe_ingredient}
    return {
        i.reference_id
        for i in saved.recipe_ingredient
        if i.reference_id in old and old[i.reference_id] == amount_key(i)
    }


def recheck_amounts(session: Session, before: RecipeOut, sent: list[RecipeStep], saved: RecipeOut) -> None:
    """Follows an edit of a recipe from BEFORE to SAVED: a link moves with its step and its text or goes, and links
    and extras of a line that is gone or has a new quantity or unit go too ("2–3 EL" edited to 4 EL). Commits."""
    places = new_places(before, sent)
    texts = [step.text for step in saved.recipe_instructions or []]
    references = kept_lines(before, saved)
    rows = session.execute(sa.select(KhStepAmount).where(KhStepAmount.recipe_id == saved.id)).scalars().all()
    for row in rows:
        place = places.get(row.step)
        known = place is not None and place < len(texts) and row.reference_id in references
        moved = recheck_link(texts[place], StepAmountOut.model_validate(row)) if known and place is not None else None
        if moved is None or place is None:
            session.delete(row)
        else:
            row.step, row.start, row.end = place, moved.start, moved.end
    session.execute(
        sa.delete(KhIngredientExtra).where(
            KhIngredientExtra.recipe_id == saved.id, KhIngredientExtra.reference_id.not_in(references)
        )
    )
    session.commit()
