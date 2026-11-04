"""KH: tests for the bell's routes (D39): a manager reads the own group's notices, newest first, with the number of
unread ones, and opening the bell marks them read."""

import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.notices.models import KhNotice
from mealie.kh.notices.service import notify
from tests.utils.fixture_schemas import TestUser

NOTICES = "/api/kh/notices"


def test_unread_counts_after_the_last_read(api_client: TestClient, unique_user: TestUser, clean_ai):
    session = unique_user.repos.session
    notify(session, unique_user.group_id, "ai_quota", provider="Gemini", next_provider="Groq")
    notify(session, unique_user.group_id, "ai_ready", provider="Gemini")
    answer = api_client.get(NOTICES, headers=unique_user.token).json()
    assert answer["unread"] == 2
    assert [(n["kind"], n["provider"], n["nextProvider"]) for n in answer["items"]] == [
        ("ai_ready", "Gemini", None),
        ("ai_quota", "Gemini", "Groq"),
    ]
    assert api_client.post(f"{NOTICES}/read", headers=unique_user.token).status_code == 204
    assert api_client.get(NOTICES, headers=unique_user.token).json()["unread"] == 0
    notify(session, unique_user.group_id, "ai_none")
    assert api_client.get(NOTICES, headers=unique_user.token).json()["unread"] == 1


def test_other_groups_notices_stay_hidden(api_client: TestClient, unique_user: TestUser, g2_user: TestUser, clean_ai):
    session = g2_user.repos.session
    notify(session, g2_user.group_id, "ai_none")
    try:
        assert api_client.get(NOTICES, headers=unique_user.token).json() == {"items": [], "unread": 0}
    finally:
        session.execute(sa.delete(KhNotice).where(KhNotice.group_id == g2_user.group_id))
        session.commit()
