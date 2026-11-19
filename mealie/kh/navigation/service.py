"""KH: reading and storing a person's own side menu (D58)."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.navigation.models import KhUserNavigation


def load_hidden(session: Session, user_id: UUID4) -> list[str]:
    """The side-menu entries the user hid (empty when never set)."""
    row = session.execute(sa.select(KhUserNavigation).where(KhUserNavigation.user_id == user_id)).scalar_one_or_none()
    return list(row.hidden) if row else []


def save_hidden(session: Session, user_id: UUID4, hidden: list[str]) -> None:
    """Stores the user's list, replacing the old one. Commits."""
    row = session.execute(sa.select(KhUserNavigation).where(KhUserNavigation.user_id == user_id)).scalar_one_or_none()
    if row is None:
        session.add(KhUserNavigation(session=session, user_id=user_id, hidden=hidden))
    else:
        row.hidden = hidden
    session.commit()


def delete_user_navigation(session: Session, user_id: UUID4) -> None:
    """Deletes a deleted user's row; SQLite in Mealie checks no foreign keys, so the cascade is not enough. Commits."""
    session.execute(sa.delete(KhUserNavigation).where(KhUserNavigation.user_id == user_id))
    session.commit()
