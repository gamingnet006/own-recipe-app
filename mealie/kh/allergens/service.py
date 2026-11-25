"""KH: the allergen tables' data access (D44): corrections per recipe, and the cleanup when a recipe or a user is
deleted."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session, joinedload, selectinload

from mealie.db.models.recipe.ingredient import RecipeIngredientModel, RecipeIngredientSubstitutionModel
from mealie.db.models.recipe.recipe import RecipeModel
from mealie.kh.allergens.models import KhRecipeAllergen, KhSubstitution, KhUserAllergies
from mealie.schema.recipe.recipe_ingredient import IngredientFoodOut, IngredientUnitOut, RecipeIngredient


def delete_recipe_allergens(session: Session, recipe_ids: list[UUID4]) -> None:
    """Deletes the corrections of deleted recipes; SQLite in Mealie checks no foreign keys, so the cascade is not
    enough. Commits."""
    session.execute(sa.delete(KhRecipeAllergen).where(KhRecipeAllergen.recipe_id.in_(recipe_ids)))
    session.commit()


def delete_user_allergies(session: Session, user_id: UUID4) -> None:
    """Deletes a deleted user's "Ich vertrage nicht" list, for the same reason. Commits."""
    session.execute(sa.delete(KhUserAllergies).where(KhUserAllergies.user_id == user_id))
    session.commit()


def corrections_by_recipe(session: Session, recipe_ids: list[UUID4]) -> dict[UUID4, dict[str, bool]]:
    """The corrections of all RECIPE_IDS by recipe and allergen key, in one query."""
    rows = session.execute(sa.select(KhRecipeAllergen).where(KhRecipeAllergen.recipe_id.in_(recipe_ids))).scalars()
    found: dict[UUID4, dict[str, bool]] = {}
    for row in rows:
        found.setdefault(row.recipe_id, {})[row.allergen] = row.present
    return found


def corrections_of(session: Session, recipe_id: UUID4) -> dict[str, bool]:
    """The recipe's corrections by allergen key."""
    return corrections_by_recipe(session, [recipe_id]).get(recipe_id, {})


def set_correction(session: Session, recipe_id: UUID4, allergen: str, present: bool | None) -> None:
    """Stores a correction for the recipe's allergen, or removes it when PRESENT is None. Commits."""
    row = session.execute(
        sa.select(KhRecipeAllergen).where(
            KhRecipeAllergen.recipe_id == recipe_id, KhRecipeAllergen.allergen == allergen
        )
    ).scalar_one_or_none()
    if present is None:
        if row is not None:
            session.delete(row)
    elif row is None:
        session.add(KhRecipeAllergen(session=session, recipe_id=recipe_id, allergen=allergen, present=present))
    else:
        row.present = present
    session.commit()


def group_ingredient_lines(session: Session, group_id: UUID4) -> list[tuple[UUID4, str, list[RecipeIngredient]]]:
    """Every recipe of the group, of every household, as (id, slug, ingredient lines in order): the warnings read
    nothing else, so the full RecipeOut (tags, instructions, nutrition, ...) is not loaded. Recipes without
    ingredients are kept, a correction can still mark them."""
    recipes = session.execute(sa.select(RecipeModel.id, RecipeModel.slug).where(RecipeModel.group_id == group_id))
    lines: dict[UUID4, list[RecipeIngredient]] = {}
    rows = session.execute(
        sa.select(RecipeIngredientModel)
        .join(RecipeModel, RecipeModel.id == RecipeIngredientModel.recipe_id)
        .where(RecipeModel.group_id == group_id)
        .order_by(RecipeIngredientModel.recipe_id, RecipeIngredientModel.position)
        .options(
            joinedload(RecipeIngredientModel.unit).options(*IngredientUnitOut.loader_options()),
            joinedload(RecipeIngredientModel.food).options(*IngredientFoodOut.loader_options()),
            selectinload(RecipeIngredientModel.substitutions).joinedload(
                RecipeIngredientSubstitutionModel.substitute_food
            ),
        )
    )
    for row in rows.unique().scalars():
        lines.setdefault(row.recipe_id, []).append(RecipeIngredient.model_validate(row))
    return [(recipe_id, slug, lines.get(recipe_id, [])) for recipe_id, slug in recipes]


def delete_household_substitutions(session: Session, household_id: UUID4) -> None:
    """Deletes a deleted household's own substitution rules, for the same reason. Commits."""
    session.execute(sa.delete(KhSubstitution).where(KhSubstitution.household_id == household_id))
    session.commit()


def household_rules(session: Session, household_id: UUID4) -> list[KhSubstitution]:
    """The household's own substitution rules, oldest first."""
    return list(
        session.execute(
            sa.select(KhSubstitution)
            .where(KhSubstitution.household_id == household_id)
            .order_by(KhSubstitution.created_at, KhSubstitution.id)
        ).scalars()
    )


def add_rule(session: Session, household_id: UUID4, match: str, replacement: str, allergen: str) -> KhSubstitution:
    """Stores a new own rule for the household. Commits."""
    row = KhSubstitution(
        session=session, household_id=household_id, match=match, replacement=replacement, allergen=allergen
    )
    session.add(row)
    session.commit()
    return row


def delete_rule(session: Session, household_id: UUID4, rule_id: UUID4) -> KhSubstitution | None:
    """Removes the household's rule and returns it; None when the household has no such rule. Commits."""
    row = session.execute(
        sa.select(KhSubstitution).where(KhSubstitution.id == rule_id, KhSubstitution.household_id == household_id)
    ).scalar_one_or_none()
    if row is not None:
        session.delete(row)
        session.commit()
    return row
