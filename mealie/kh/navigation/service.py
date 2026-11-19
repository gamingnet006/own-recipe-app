"""KH: reading and storing a person's own side menu (D58) and simple view switch (D79)."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.navigation.models import KhUserNavigation
from mealie.kh.navigation.schemas import NavigationSettings


def _row(session: Session, user_id: UUID4) -> KhUserNavigation | None:
    return session.execute(sa.select(KhUserNavigation).where(KhUserNavigation.user_id == user_id)).scalar_one_or_none()


def load_navigation(session: Session, user_id: UUID4) -> NavigationSettings:
    """The user's hidden side-menu entries and simple view switch (nothing hidden, off, when never set)."""
    row = _row(session, user_id)
    return NavigationSettings(hidden=list(row.hidden) if row else [], simple=bool(row and row.simple))


def save_navigation(
    session: Session, user_id: UUID4, hidden: list[str] | None = None, simple: bool | None = None
) -> None:
    """Stores the given parts for the user (None keeps the stored part). Commits."""
    row = _row(session, user_id)
    if row is None:
        row = KhUserNavigation(session=session, user_id=user_id, hidden=[], simple=False)
        session.add(row)
    if hidden is not None:
        row.hidden = hidden
    if simple is not None:
        row.simple = simple
    session.commit()


def delete_user_navigation(session: Session, user_id: UUID4) -> None:
    """Deletes a deleted user's row; SQLite in Mealie checks no foreign keys, so the cascade is not enough. Commits."""
    session.execute(sa.delete(KhUserNavigation).where(KhUserNavigation.user_id == user_id))
    session.commit()
