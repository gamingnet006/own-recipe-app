"""KH: the allergen tables' data access (D44): so far the cleanup when a recipe or a user is deleted."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.allergens.models import KhRecipeAllergen, KhUserAllergies


def delete_recipe_allergens(session: Session, recipe_ids: list[UUID4]) -> None:
    """Deletes the corrections of deleted recipes; SQLite in Mealie checks no foreign keys, so the cascade is not
    enough. Commits."""
    session.execute(sa.delete(KhRecipeAllergen).where(KhRecipeAllergen.recipe_id.in_(recipe_ids)))
    session.commit()


def delete_user_allergies(session: Session, user_id: UUID4) -> None:
    """Deletes a deleted user's "Ich vertrage nicht" list, for the same reason. Commits."""
    session.execute(sa.delete(KhUserAllergies).where(KhUserAllergies.user_id == user_id))
    session.commit()
