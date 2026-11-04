"""KH: tests for the AI list's foundation (v0.2 plan 1, task 1): the settings' defaults and the tables for the
providers' state and the notices on Küchenhelfer's migration branch (D39)."""

import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.db.init_db import ALEMBIC_DIR
from mealie.kh.features.settings import KhSettings


def test_settings_have_the_spec_defaults():
    s = KhSettings()
    assert (s.ai_short_pause_seconds, s.ai_quota_pause_minutes, s.ai_down_pause_minutes) == (120, 60, 10)
    assert (s.notice_days, s.notice_poll_minutes) == (30, 5)


def test_kh_branch_head_is_kh0002():
    script = ScriptDirectory.from_config(Config(str(ALEMBIC_DIR / "alembic.ini")))
    assert "kh0002" in script.get_heads()
    assert script.get_revision("kh0002").down_revision == "kh0001"


def test_new_tables_exist(api_client: TestClient, session: Session):
    inspector = sa.inspect(session.get_bind())
    columns = {
        table: {column["name"] for column in inspector.get_columns(table)}
        for table in ("kh_ai_provider_state", "kh_notices", "kh_notice_reads")
    }
    assert {"provider_id", "position", "status", "paused_until", "supports_images"} <= columns["kh_ai_provider_state"]
    assert {"id", "group_id", "kind", "provider", "next_provider", "until", "created_at"} <= columns["kh_notices"]
    assert {"user_id", "last_read_at"} <= columns["kh_notice_reads"]
