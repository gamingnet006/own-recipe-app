"""KH: the duplicate report's data access (D43)."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.duplicates.models import KhDuplicateIgnored


def delete_ignored(session: Session, recipe_ids: list[UUID4]) -> None:
    """Deletes the ignored pairs of deleted recipes; SQLite in Mealie checks no foreign keys, so the cascade is not
    enough. Commits."""
    session.execute(
        sa.delete(KhDuplicateIgnored).where(
            KhDuplicateIgnored.recipe_a.in_(recipe_ids) | KhDuplicateIgnored.recipe_b.in_(recipe_ids)
        )
    )
    session.commit()
