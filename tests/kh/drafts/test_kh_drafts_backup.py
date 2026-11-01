"""KH: tests that drafts survive a backup and its restore (phase 2): their JSON columns come back as they were
saved, approved_at as a date, and the originals with them. Mealie's own tables have no JSON column, so its
restore never had to handle one."""

import copy
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.core.config import get_app_settings
from mealie.db.models._model_base import SqlAlchemyBase
from mealie.services.backups_v2.alchemy_exporter import AlchemyExporter
from mealie.services.backups_v2.backup_v2 import BackupV2
from tests.kh.drafts.helpers import DRAFTS, get_draft, png, post_draft
from tests.utils.fixture_schemas import TestUser

TEXT = "Testkuchen: 200 g Mehl, 100 g Zucker, 3 Eier, 1 Prise Salz. 30 Minuten backen."


def test_restore_keeps_json_columns_as_saved():
    row = {
        "id": str(uuid4()),
        "original_files": ["original-1.webp"],
        "recipe": {"id": str(uuid4()), "name": "Testkuchen", "recipeIngredient": [{"note": "200 g Mehl"}]},
        "warnings": [{"kind": "similar_title", "name": "Testkuchen", "recipeSlug": None, "draftId": str(uuid4())}],
        "approved_at": "2026-10-31T12:00:00",
    }
    exporter = AlchemyExporter(get_app_settings().DB_URL)
    restored = exporter.convert_types({"kh_drafts": [copy.deepcopy(row)]})["kh_drafts"][0]
    exporter.engine.dispose()

    for column in ("original_files", "recipe", "warnings"):
        assert restored[column] == row[column]
    assert restored["approved_at"] == datetime.fromisoformat(row["approved_at"])


def test_every_json_column_is_restored_as_saved():
    """Like Mealie's guard for datetime columns: a JSON column missing from look_for_json breaks restores."""
    json_columns = {
        column.name
        for table in SqlAlchemyBase.metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, sa.JSON)
    }
    assert json_columns <= AlchemyExporter.look_for_json


def test_drafts_survive_backup_and_restore(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    photo = post_draft(api_client, unique_user, files={"images": ("zettel.png", png(400, 300), "image/png")})
    text = post_draft(api_client, unique_user, data={"text": TEXT})
    saved = post_draft(api_client, unique_user, data={"text": TEXT})
    drafts = [response.json()["id"] for response in (photo, text, saved)]
    approved = api_client.post(f"{DRAFTS}/{drafts[2]}/approve", json={"force": True}, headers=unique_user.token)
    assert approved.status_code == 200
    before = [get_draft(api_client, unique_user, draft).json() for draft in drafts]
    assert before[0]["originalFiles"] and before[1]["warnings"] and before[2]["approvedAt"]  # every column is filled

    backup_v2 = BackupV2(get_app_settings().DB_URL)
    backup_v2.restore(backup_v2.backup())
    backup_v2.db_exporter.engine.dispose()

    assert [get_draft(api_client, unique_user, draft).json() for draft in drafts] == before
    assert api_client.get(f"{DRAFTS}/{drafts[0]}/originals/1", headers=unique_user.token).status_code == 200
