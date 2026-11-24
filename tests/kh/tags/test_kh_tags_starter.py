"""KH: tests for seeding the 24 starter tags once per group: language, no doubles, deleted tags stay deleted."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.kh.tags import starter
from mealie.kh.tags.starter import STARTER_TAGS, seed_all_groups, seed_group
from mealie.schema.recipe.recipe_organizers import TagSave
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser


def names(user: TestUser) -> set[str]:
    return {tag.name for tag in user.repos.tags.get_all()}


@pytest.fixture
def clean_group(unique_user: TestUser) -> TestUser:
    """The user's group with no tags."""
    for tag in unique_user.repos.tags.get_all():
        unique_user.repos.tags.delete(tag.id)
    return unique_user


def test_seed_in_english_then_never_again(session: Session, clean_group: TestUser, tmp_path: Path) -> None:
    assert seed_group(session, clean_group._group_id, "en-US", tmp_path) == 24
    assert names(clean_group) == {tag.en for tag in STARTER_TAGS}
    assert seed_group(session, clean_group._group_id, "en-US", tmp_path) == 0
    assert len(names(clean_group)) == 24


def test_deleted_tag_does_not_come_back(session: Session, clean_group: TestUser, tmp_path: Path) -> None:
    seed_group(session, clean_group._group_id, "de-DE", tmp_path)
    assert "Suppe" in names(clean_group)
    soup = next(tag for tag in clean_group.repos.tags.get_all() if tag.name == "Suppe")
    clean_group.repos.tags.delete(soup.id)
    seed_group(session, clean_group._group_id, "de-DE", tmp_path)
    assert "Suppe" not in names(clean_group)


def test_families_own_tag_is_not_doubled_or_renamed(session: Session, clean_group: TestUser, tmp_path: Path) -> None:
    clean_group.repos.tags.create(TagSave(name="Vegan", group_id=clean_group._group_id))
    clean_group.repos.tags.create(TagSave(name="Omas Rezepte", group_id=clean_group._group_id))
    assert seed_group(session, clean_group._group_id, "de-DE", tmp_path) == 23  # "Vegan" counts as the vegan tag
    assert {"Vegan", "Omas Rezepte"} <= names(clean_group)
    assert "vegan" not in names(clean_group)


def test_fresh_installation_waits_for_the_language(
    session: Session, clean_group: TestUser, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(starter, "installation_locale", lambda _: None)
    seed_all_groups(session, tmp_path)  # the user's group has no recipes: nothing yet
    assert names(clean_group) == set()
    monkeypatch.setattr(starter, "installation_locale", lambda _: "en-US")
    seed_all_groups(session, tmp_path)
    assert "Breakfast" in names(clean_group)


def test_existing_installation_without_language_gets_german(
    api_client: TestClient, session: Session, clean_group: TestUser, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(starter, "installation_locale", lambda _: None)
    api_client.post(api_routes.recipes, json={"name": "Etwas"}, headers=clean_group.token)
    seed_all_groups(session, tmp_path)
    assert "Frühstück" in names(clean_group)
