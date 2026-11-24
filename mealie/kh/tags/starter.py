"""KH: the 24 starter tags with their German and English names, and seeding them once per group in the
installation's language. A marker file per group (like the address notice) remembers the seeding, so a tag a family
deleted never comes back and one they renamed is never touched."""

from pathlib import Path
from typing import NamedTuple

import sqlalchemy as sa
from pydantic import UUID4
from slugify import slugify
from sqlalchemy.orm import Session

from mealie.core.config import get_app_dirs
from mealie.core.root_logger import get_logger
from mealie.db.db_setup import session_context
from mealie.db.models.group import Group
from mealie.db.models.recipe import RecipeModel
from mealie.kh.i18n.locale import DEFAULT_LOCALE, installation_locale
from mealie.repos.all_repositories import get_repositories
from mealie.schema.recipe.recipe_organizers import TagSave

logger = get_logger()


class StarterTag(NamedTuple):
    """One starter tag: a stable key (the rules and the tests use it) and its names in both languages."""

    key: str
    de: str
    en: str


STARTER_TAGS: tuple[StarterTag, ...] = (
    StarterTag("breakfast", "Frühstück", "Breakfast"),
    StarterTag("starter", "Vorspeise", "Starter"),
    StarterTag("main", "Hauptgericht", "Main course"),
    StarterTag("side", "Beilage", "Side dish"),
    StarterTag("soup", "Suppe", "Soup"),
    StarterTag("salad", "Salat", "Salad"),
    StarterTag("dessert", "Dessert", "Dessert"),
    StarterTag("snack", "Snack", "Snack"),
    StarterTag("drink", "Getränk", "Drink"),
    StarterTag("cake", "Kuchen", "Cake"),
    StarterTag("bread", "Brot & Brötchen", "Bread & rolls"),
    StarterTag("cookies", "Plätzchen & Gebäck", "Cookies & pastries"),
    StarterTag("vegetarian", "vegetarisch", "Vegetarian"),
    StarterTag("vegan", "vegan", "Vegan"),
    StarterTag("meat", "mit Fleisch", "With meat"),
    StarterTag("fish", "mit Fisch", "With fish"),
    StarterTag("quick", "schnell (bis 30 Min.)", "Quick (up to 30 min)"),
    StarterTag("easy", "einfach", "Easy"),
    StarterTag("guests", "für Gäste", "For guests"),
    StarterTag("kids", "Kinder mögen's", "Kids love it"),
    StarterTag("make_ahead", "gut vorzubereiten", "Make ahead"),
    StarterTag("holidays", "Festtage", "Holidays"),
    StarterTag("grill", "Grillen", "Barbecue"),
    StarterTag("leftovers", "Resteverwertung", "Leftovers"),
)

# every name and slug a starter tag has in either language, so a family's own "Vegan" is not made a second time
_KEY_BY_SLUG = {slugify(name): tag.key for tag in STARTER_TAGS for name in (tag.de, tag.en)}


def starter_key(tag_name: str) -> str | None:
    """The key of the starter tag a tag name stands for (in either language), None for the family's own tags."""
    return _KEY_BY_SLUG.get(slugify(tag_name))


def _marker(data_dir: Path, group_id: UUID4) -> Path:
    return data_dir / "kh" / "starter-tags" / str(group_id)


def seed_group(session: Session, group_id: UUID4, locale: str, data_dir: Path) -> int:
    """Makes the starter tags the group does not have yet, named in LOCALE, once; returns how many were made.
    A group with a marker is left alone, so deleted tags stay deleted."""
    marker = _marker(data_dir, group_id)
    if marker.exists():
        return 0
    repo = get_repositories(session, group_id=group_id).tags
    have = {starter_key(tag.name) for tag in repo.get_all()}
    made = 0
    for tag in STARTER_TAGS:
        if tag.key not in have:
            repo.create(TagSave(name=tag.de if locale == "de-DE" else tag.en, group_id=group_id))
            made += 1
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    return made


def seed_all_groups(session: Session, data_dir: Path) -> None:
    """Seeds every group that has no marker yet. While nobody has chosen a language, a group without recipes is
    skipped: it is a fresh installation, whose first setup asks for the language first. Everything else (existing
    installations) is seeded in German."""
    locale = installation_locale(session)
    for group_id in session.execute(sa.select(Group.id)).scalars():
        if _marker(data_dir, group_id).exists():
            continue
        in_use = session.execute(sa.select(RecipeModel.id).where(RecipeModel.group_id == group_id)).first()
        if locale is None and not in_use:
            continue
        made = seed_group(session, group_id, locale or DEFAULT_LOCALE, data_dir)
        logger.info(f"KH: seeded {made} starter tags for group {group_id}")


def run_seeding() -> None:
    """The scheduler's job (every 5 minutes, cheap once every group has its marker): seeds new groups, and a fresh
    installation right after its first setup chose the language."""
    try:
        with session_context() as session:
            seed_all_groups(session, get_app_dirs().DATA_DIR)
    except Exception:
        logger.exception("KH: seeding the starter tags failed")  # tried again in 5 minutes
