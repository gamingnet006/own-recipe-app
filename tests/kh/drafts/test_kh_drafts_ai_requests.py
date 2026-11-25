"""KH: tests that recognizing a draft asks the AI no more often than needed: one page without recipe data costs
one request, a page with recipe data none, and a long recognition keeps its draft alive (fake AI only, D23)."""

import asyncio
from datetime import timedelta
from typing import Any

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.drafts.models import KhDraft
from mealie.kh.drafts.recognize import heartbeat
from mealie.kh.drafts.repository import drafts_repo
from mealie.services.recipe.import_workflow.exceptions import NoRecipeDataError
from mealie.services.scraper.scraper_strategies import RecipeScraperOpenAI
from tests.kh.drafts.helpers import DRAFTS, get_draft, post_draft
from tests.utils.fixture_schemas import TestUser

LINK = "https://example.org/testkuchen"


@pytest.fixture
def workflow_runs(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Mealie's AI page reader switched on and counting: a run of it would be an AI request of its own."""
    runs: list[str] = []

    async def parse(self: RecipeScraperOpenAI, on_progress: Any = None) -> None:
        runs.append(self.url)

    monkeypatch.setattr(RecipeScraperOpenAI, "can_scrape", lambda self: True)
    monkeypatch.setattr(RecipeScraperOpenAI, "parse", parse)
    return runs


def test_page_without_recipe_data_asks_the_ai_once(
    api_client: TestClient, unique_user: TestUser, fake_page, fake_ai, workflow_runs
):
    fake_page(None)
    calls = fake_ai("recipe.json")
    draft_id = post_draft(api_client, unique_user, data={"url": LINK}).json()["id"]
    assert get_draft(api_client, unique_user, draft_id).json()["status"] == "ready"
    assert workflow_runs == []
    assert len(calls) == 1


def test_page_without_recipe_data_never_becomes_an_opengraph_stub(
    api_client: TestClient, unique_user: TestUser, fake_page, fake_ai, workflow_runs
):
    fake_page(None)  # the page has OpenGraph tags
    fake_ai(NoRecipeDataError())
    draft_id = post_draft(api_client, unique_user, data={"url": LINK}).json()["id"]
    draft = get_draft(api_client, unique_user, draft_id).json()
    assert (draft["status"], draft["error"], draft["recipe"]) == ("failed", "no_recipe_data", None)
    assert workflow_runs == []


def test_page_with_recipe_data_asks_no_ai(
    api_client: TestClient, unique_user: TestUser, fake_page, fake_ai, workflow_runs
):
    fake_page("page.html")
    calls = fake_ai("recipe.json")
    draft_id = post_draft(api_client, unique_user, data={"url": LINK}).json()["id"]
    assert get_draft(api_client, unique_user, draft_id).json()["recipe"]["name"] == "Testkuchen"
    assert workflow_runs == []
    assert calls == []


def test_heartbeat_refreshes_the_update_time(session: Session, unique_user: TestUser):
    repo = drafts_repo(session, unique_user.group_id, unique_user.household_id)
    draft = repo.create(
        {
            "user_id": unique_user.user_id,
            "status": "working",
            "source_type": "text",
            "source_text": "Testkuchen",
            "group_id": unique_user.group_id,
            "household_id": unique_user.household_id,
        }
    )
    old = get_utc_now() - timedelta(minutes=20)
    session.execute(sa.update(KhDraft).where(KhDraft.id == draft.id).values(update_at=old))
    session.commit()

    asyncio.run(heartbeat(session, draft.id)("step"))
    session.expire_all()
    assert session.get(KhDraft, draft.id).update_at > get_utc_now() - timedelta(minutes=1)  # type: ignore[union-attr]


def test_retry_refuses_a_recognition_that_is_still_running(
    api_client: TestClient, session: Session, unique_user: TestUser
):
    repo = drafts_repo(session, unique_user.group_id, unique_user.household_id)
    draft = repo.create(
        {
            "user_id": unique_user.user_id,
            "status": "working",
            "source_type": "text",
            "source_text": "Testkuchen",
            "group_id": unique_user.group_id,
            "household_id": unique_user.household_id,
        }
    )
    response = api_client.post(f"{DRAFTS}/{draft.id}/retry", headers=unique_user.token)
    assert response.status_code == 409
