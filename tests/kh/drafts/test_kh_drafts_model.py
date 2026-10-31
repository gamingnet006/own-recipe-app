"""KH: tests for the drafts foundation (phase 2, task 1): settings with defaults, the kh_drafts table
on our own migration branch next to Mealie's, and a repository that sees only its household."""

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.db.init_db import ALEMBIC_DIR, db_is_at_head
from mealie.kh.drafts.repository import drafts_repo
from mealie.kh.features.settings import KhSettings
from tests.utils.fixture_schemas import TestUser


def alembic_config() -> Config:
    """The config Mealie's init_db upgrades with."""
    return Config(str(ALEMBIC_DIR / "alembic.ini"))


def test_settings_defaults_and_override(monkeypatch: pytest.MonkeyPatch):
    assert KhSettings().draft_max_images == 5
    assert KhSettings().duplicate_title == 0.85
    monkeypatch.setenv("KH_DRAFT_MAX_IMAGES", "2")
    assert KhSettings().draft_max_images == 2
    monkeypatch.setenv("KH_DRAFT_MAX_IMAGES", "")  # compose passes unset values as empty
    assert KhSettings().draft_max_images == 5


def test_table_exists_with_columns(api_client: TestClient, session: Session):
    columns = {c["name"] for c in sa.inspect(session.get_bind()).get_columns("kh_drafts")}
    assert {"status", "source_type", "recipe", "warnings", "recipe_id", "approved_by"} <= columns


def test_kh_branch_on_mealies_newest_and_database_at_heads(api_client: TestClient):
    # One head today; a new Mealie migration on the same parent makes a second, which "heads" upgrades too
    script = ScriptDirectory.from_config(alembic_config())
    mealie_newest = sorted((ALEMBIC_DIR / "versions").glob("*.py"))[-1].name.split("_")[1]
    kh0001 = script.get_revision("kh0001")
    assert kh0001 is not None
    assert kh0001.branch_labels == {"kh"}
    assert kh0001.down_revision == mealie_newest
    assert "kh0001" in script.get_heads()
    assert db_is_at_head(alembic_config())


def test_repo_is_scoped_to_household(session: Session, unique_user: TestUser, h2_user: TestUser):
    mine = drafts_repo(session, unique_user.group_id, unique_user.household_id)
    theirs = drafts_repo(session, h2_user.group_id, h2_user.household_id)
    draft = mine.create(
        {
            "user_id": unique_user.user_id,
            "status": "ready",
            "source_type": "text",
            "source_text": "x",
            "group_id": unique_user.group_id,
            "household_id": unique_user.household_id,
        }
    )
    try:
        assert mine.get_one(draft.id)
        assert theirs.get_one(draft.id) is None
        assert draft.user_name == unique_user.full_name
    finally:
        mine.delete(draft.id)
