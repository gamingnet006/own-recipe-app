"""KH: reading, writing and deleting a household's note on a recipe (D82)."""

import sqlalchemy as sa
from fastapi import HTTPException, status
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mealie.db.models.recipe.recipe import RecipeModel
from mealie.db.models.users.users import User
from mealie.kh.notes.models import KhRecipeNote
from mealie.kh.notes.schemas import NoteOut


def _row(session: Session, household_id: UUID4, recipe_id: UUID4) -> KhRecipeNote | None:
    return session.execute(
        sa.select(KhRecipeNote).where(KhRecipeNote.household_id == household_id, KhRecipeNote.recipe_id == recipe_id)
    ).scalar_one_or_none()


def _check_recipe(session: Session, group_id: UUID4, recipe_id: UUID4) -> None:
    """404 unless the recipe is one of the group's (a household may annotate any recipe of its group)."""
    found = session.execute(
        sa.select(RecipeModel.id).where(RecipeModel.id == recipe_id, RecipeModel.group_id == group_id)
    ).first()
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipe not found")


def _update(session: Session, row: KhRecipeNote, text: str, user_id: UUID4) -> None:
    """Replaces the text and author of an existing note. Commits."""
    row.text, row.updated_by = text, user_id
    session.commit()


def get_note(session: Session, group_id: UUID4, household_id: UUID4, recipe_id: UUID4) -> NoteOut | None:
    """The household's note on the recipe, None when it has none."""
    _check_recipe(session, group_id, recipe_id)
    row = _row(session, household_id, recipe_id)
    if row is None:
        return None
    author = session.get(User, row.updated_by) if row.updated_by else None
    return NoteOut(
        text=row.text,
        updated_by=row.updated_by,
        updated_by_name=(author.full_name or author.username) if author else "",
        updated_at=row.update_at,
    )


def set_note(
    session: Session, group_id: UUID4, household_id: UUID4, user_id: UUID4, recipe_id: UUID4, text: str
) -> NoteOut | None:
    """Stores the text as the household's note (replacing the old one); empty text deletes it. Commits."""
    _check_recipe(session, group_id, recipe_id)
    text = text.strip()
    row = _row(session, household_id, recipe_id)
    if not text:
        if row:
            session.delete(row)
            session.commit()
        return None
    if row is None:
        session.add(
            KhRecipeNote(
                session=session,
                group_id=group_id,
                household_id=household_id,
                recipe_id=recipe_id,
                text=text,
                updated_by=user_id,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            # two first saves at once: the other one won the unique (household, recipe), so this one updates its row
            session.rollback()
            row = _row(session, household_id, recipe_id)
            if row is None:
                raise
            _update(session, row, text, user_id)
    else:
        _update(session, row, text, user_id)
    return get_note(session, group_id, household_id, recipe_id)


def delete_note(session: Session, group_id: UUID4, household_id: UUID4, recipe_id: UUID4) -> None:
    """Deletes the household's note on the recipe; nothing to delete is fine. Commits."""
    _check_recipe(session, group_id, recipe_id)
    session.execute(
        sa.delete(KhRecipeNote).where(KhRecipeNote.household_id == household_id, KhRecipeNote.recipe_id == recipe_id)
    )
    session.commit()


def delete_recipe_notes(session: Session, recipe_ids: list[UUID4]) -> None:
    """Deletes the notes of deleted recipes; SQLite in Mealie checks no foreign keys, so the cascade is not enough.
    Commits."""
    session.execute(sa.delete(KhRecipeNote).where(KhRecipeNote.recipe_id.in_(recipe_ids)))
    session.commit()


def delete_household_notes(session: Session, household_id: UUID4) -> None:
    """Deletes a deleted household's notes, for the same reason. Commits."""
    session.execute(sa.delete(KhRecipeNote).where(KhRecipeNote.household_id == household_id))
    session.commit()
