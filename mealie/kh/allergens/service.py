"""KH: the allergen tables' data access (D44): corrections per recipe, and the cleanup when a recipe or a user is
deleted."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.recipe.recipe import RecipeModel
from mealie.kh.allergens.models import KhRecipeAllergen, KhUserAllergies
from mealie.schema.recipe.recipe import Recipe


def delete_recipe_allergens(session: Session, recipe_ids: list[UUID4]) -> None:
    """Deletes the corrections of deleted recipes; SQLite in Mealie checks no foreign keys, so the cascade is not
    enough. Commits."""
    session.execute(sa.delete(KhRecipeAllergen).where(KhRecipeAllergen.recipe_id.in_(recipe_ids)))
    session.commit()


def delete_user_allergies(session: Session, user_id: UUID4) -> None:
    """Deletes a deleted user's "Ich vertrage nicht" list, for the same reason. Commits."""
    session.execute(sa.delete(KhUserAllergies).where(KhUserAllergies.user_id == user_id))
    session.commit()


def corrections_of(session: Session, recipe_id: UUID4) -> dict[str, bool]:
    """The recipe's corrections by allergen key."""
    rows = session.execute(sa.select(KhRecipeAllergen).where(KhRecipeAllergen.recipe_id == recipe_id)).scalars()
    return {row.allergen: row.present for row in rows}


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


def group_recipes(session: Session, group_id: UUID4) -> list[Recipe]:
    """All recipes of the group with their ingredients, of every household (the repository's list gives summaries
    without ingredients)."""
    rows = session.execute(
        sa.select(RecipeModel).where(RecipeModel.group_id == group_id).options(*Recipe.loader_options())
    )
    return [Recipe.model_validate(row) for row in rows.unique().scalars()]
