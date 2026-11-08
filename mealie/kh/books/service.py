"""KH: the family cookbook's data access (D43): print settings per cookbook and the own-photo flag per recipe."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.books.models import KhCookbookPrint, KhRecipeFlags


def delete_print_settings(session: Session, cookbook_id: UUID4) -> None:
    """Deletes a deleted cookbook's print settings; SQLite in Mealie checks no foreign keys, so the cascade is not
    enough. Commits."""
    session.execute(sa.delete(KhCookbookPrint).where(KhCookbookPrint.cookbook_id == cookbook_id))
    session.commit()


def delete_flags(session: Session, recipe_ids: list[UUID4]) -> None:
    """Deletes the flags of deleted recipes, for the same reason. Commits."""
    session.execute(sa.delete(KhRecipeFlags).where(KhRecipeFlags.recipe_id.in_(recipe_ids)))
    session.commit()
