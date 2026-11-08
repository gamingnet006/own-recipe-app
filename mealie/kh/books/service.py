"""KH: the family cookbook's data access (D43): print settings per cookbook and the own-photo flag per recipe."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.recipe.recipe import RecipeModel
from mealie.kh.books.models import KhCookbookPrint, KhRecipeFlags
from mealie.kh.books.schemas import BookSettings


def delete_print_settings(session: Session, cookbook_id: UUID4) -> None:
    """Deletes a deleted cookbook's print settings; SQLite in Mealie checks no foreign keys, so the cascade is not
    enough. Commits."""
    session.execute(sa.delete(KhCookbookPrint).where(KhCookbookPrint.cookbook_id == cookbook_id))
    session.commit()


def delete_flags(session: Session, recipe_ids: list[UUID4]) -> None:
    """Deletes the flags of deleted recipes, for the same reason. Commits."""
    session.execute(sa.delete(KhRecipeFlags).where(KhRecipeFlags.recipe_id.in_(recipe_ids)))
    session.commit()


def own_photo_slugs(session: Session, group_id: UUID4, slugs: list[str]) -> dict[str, bool]:
    """For each of the group's recipes among SLUGS, whether its photo is marked as ours; unknown slugs are left out."""
    rows = session.execute(
        sa.select(RecipeModel.slug, KhRecipeFlags.own_photo)
        .outerjoin(KhRecipeFlags, KhRecipeFlags.recipe_id == RecipeModel.id)
        .where(RecipeModel.group_id == group_id, RecipeModel.slug.in_(slugs))
    ).all()
    return {slug: bool(own) for slug, own in rows}


def set_own_photo(session: Session, recipe_id: UUID4, own_photo: bool) -> None:
    """Sets or creates the recipe's own-photo flag. Commits."""
    row = session.execute(sa.select(KhRecipeFlags).where(KhRecipeFlags.recipe_id == recipe_id)).scalar_one_or_none()
    if row is None:
        row = KhRecipeFlags(session=session, recipe_id=recipe_id)
        session.add(row)
    row.own_photo = own_photo
    session.commit()


def _print_row(session: Session, cookbook_id: UUID4) -> KhCookbookPrint | None:
    """The cookbook's stored row, if it has one."""
    return session.execute(
        sa.select(KhCookbookPrint).where(KhCookbookPrint.cookbook_id == cookbook_id)
    ).scalar_one_or_none()


def _only_own_photos(session: Session, group_id: UUID4, settings: BookSettings) -> BookSettings:
    """SETTINGS with the photo switched off for every recipe not marked as ours (D43 F4)."""
    ours = own_photo_slugs(session, group_id, list(settings.recipes))
    return settings.model_copy(
        update={
            "recipes": {
                slug: recipe.model_copy(update={"photo": recipe.photo and ours.get(slug, False)})
                for slug, recipe in settings.recipes.items()
            }
        }
    )


def load_settings(session: Session, group_id: UUID4, cookbook_id: UUID4) -> BookSettings:
    """The cookbook's stored print settings, or the defaults when it has none. A photo whose own-photo flag was
    removed after saving is off, as on saving."""
    row = _print_row(session, cookbook_id)
    return _only_own_photos(session, group_id, BookSettings.model_validate(row.settings)) if row else BookSettings()


def save_settings(session: Session, group_id: UUID4, cookbook_id: UUID4, settings: BookSettings) -> BookSettings:
    """Stores the settings and returns them as stored: a photo is only allowed for a recipe marked as ours,
    so the others come back with photo off. Commits."""
    stored = _only_own_photos(session, group_id, settings)
    data = stored.model_dump(mode="json")
    row = _print_row(session, cookbook_id)
    if row is None:
        session.add(KhCookbookPrint(session=session, cookbook_id=cookbook_id, settings=data))
    else:
        row.settings = data
    session.commit()
    return stored
