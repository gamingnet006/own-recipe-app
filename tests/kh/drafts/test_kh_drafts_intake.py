"""KH: tests for the drafts intake (phase 2, task 2): links, text and images become drafts that are
recognized in the background; bad input creates nothing, failures carry a code, and only the own
household sees a draft. Starlette's TestClient runs background tasks before the request returns."""

from datetime import timedelta

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from mealie.core.exceptions import RateLimitError
from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.drafts.files import draft_dir
from mealie.kh.drafts.models import KhDraft
from mealie.kh.drafts.repository import drafts_repo
from mealie.kh.features.settings import get_kh_settings
from mealie.pkgs.safehttp.transport import InvalidDomainError
from mealie.schema.group.ai_providers import AIProviderCreate
from mealie.services.openai.openai import OpenAINotEnabledException
from mealie.services.recipe.ai_recipe_service import AIProviderNotEnabledError
from mealie.services.recipe.import_workflow.exceptions import NoRecipeDataError
from tests.kh.drafts.helpers import DRAFTS, get_draft, heic, open_ids, png, post_draft
from tests.utils.fixture_schemas import TestUser

LINK = "https://example.org/testkuchen"
TEXT = "Testkuchen: 200 g Mehl, 100 g Zucker, 3 Eier, 1 Prise Salz. 30 Minuten backen."


def validation_error() -> ValidationError:
    """A real pydantic ValidationError, as an AI answer that does not fit the schema raises it."""
    try:
        TypeAdapter(int).validate_python("not a number")
    except ValidationError as error:
        return error
    raise AssertionError("expected a ValidationError")


def test_link_with_recipe_data_needs_no_ai(api_client: TestClient, unique_user: TestUser, fake_page, fake_ai):
    fake_page("page.html")
    calls = fake_ai("recipe.json")
    response = post_draft(api_client, unique_user, data={"url": LINK})
    assert response.status_code == 201
    assert response.json()["status"] == "working"

    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "ready"
    assert draft["recipe"]["name"] == "Testkuchen"
    assert draft["sourceUrl"] == LINK
    assert draft["aiModel"] is None
    assert calls == []


def test_link_without_recipe_data_falls_back_to_ai(api_client: TestClient, unique_user: TestUser, fake_page, fake_ai):
    fake_page(None)
    calls = fake_ai("recipe.json")
    response = post_draft(api_client, unique_user, data={"url": LINK})
    assert get_draft(api_client, unique_user, response.json()["id"]).json()["status"] == "ready"
    assert calls == [{"url": LINK, "translate_language": None}]


def test_text_uses_ai(api_client: TestClient, unique_user: TestUser, fake_ai):
    calls = fake_ai("recipe.json")
    response = post_draft(api_client, unique_user, data={"text": TEXT})
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "ready"
    assert draft["sourceText"] == TEXT
    assert calls == [{"content": TEXT, "translate_language": None}]


def test_image_is_stored_as_webp(api_client: TestClient, unique_user: TestUser, fake_ai):
    calls = fake_ai("recipe.json")
    response = post_draft(api_client, unique_user, files=[("images", ("zettel.png", png(3000, 2000), "image/png"))])
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "ready"
    assert draft["sourceType"] == "image"
    assert draft["originalFiles"] == ["original-1.webp"]
    with Image.open(draft_dir(draft["id"]) / "original-1.webp") as image:
        assert image.format == "WEBP"
        assert max(image.size) == 2048
    assert len(calls) == 1
    assert [path.name for path in calls[0]["images"]] == ["original-1.webp"]


def test_heic_is_accepted(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    response = post_draft(api_client, unique_user, files=[("images", ("IMG_0001.HEIC", heic(400, 300), "image/heic"))])
    assert response.status_code == 201


@pytest.mark.parametrize(
    ("form", "files", "code"),
    [
        ({}, [("images", ("x.jpg", b"not an image", "image/jpeg"))], "not_an_image"),  # content, not name
        ({}, [("images", (f"p{n}.png", png(10, 10), "image/png")) for n in range(6)], "too_many_images"),
        ({}, [], "no_source"),
        ({"url": "https://example.org", "text": "x"}, [], "several_sources"),
        ({"text": "x" * 20001}, [], "text_too_long"),
    ],
)
def test_rejected_input_creates_no_draft(api_client: TestClient, unique_user: TestUser, fake_ai, form, files, code):
    fake_ai("recipe.json")
    before = open_ids(api_client, unique_user)
    response = post_draft(api_client, unique_user, data=form, files=files)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == code
    assert open_ids(api_client, unique_user) == before


def test_too_large_image_creates_no_draft(
    api_client: TestClient, unique_user: TestUser, fake_ai, monkeypatch: pytest.MonkeyPatch
):
    fake_ai("recipe.json")
    monkeypatch.setattr(get_kh_settings(), "draft_max_image_mb", 1)
    before = open_ids(api_client, unique_user)
    big = png(1200, 1200, noise=True)
    assert len(big) > 2 * 1024 * 1024
    response = post_draft(api_client, unique_user, files=[("images", ("big.png", big, "image/png"))])
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "too_large"
    assert open_ids(api_client, unique_user) == before


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (RateLimitError(), "quota_exceeded"),
        (OpenAINotEnabledException(), "ai_not_configured"),
        (AIProviderNotEnabledError(), "ai_not_configured"),
        (NoRecipeDataError(), "no_recipe_data"),
        (InvalidDomainError("blocked"), "address_blocked"),
        (validation_error(), "invalid_result"),
        (RuntimeError("anything else"), "unknown"),
    ],
)
def test_failure_codes(api_client: TestClient, unique_user: TestUser, fake_ai, error, code):
    fake_ai(error)
    response = post_draft(api_client, unique_user, data={"text": TEXT})
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "failed"
    assert draft["error"] == code


@pytest.mark.parametrize("error", [OpenAINotEnabledException(), AIProviderNotEnabledError()])
def test_link_without_data_and_without_ai(api_client: TestClient, unique_user: TestUser, fake_page, fake_ai, error):
    fake_page(None)
    fake_ai(error)
    response = post_draft(api_client, unique_user, data={"url": LINK})
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "failed"
    assert draft["error"] == "no_recipe_data"


def test_retry_turns_failed_into_ready(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai(RuntimeError("first try fails"))
    draft_id = post_draft(api_client, unique_user, data={"text": TEXT}).json()["id"]
    assert get_draft(api_client, unique_user, draft_id).json()["status"] == "failed"

    fake_ai("recipe.json")
    response = api_client.post(f"{DRAFTS}/{draft_id}/retry", headers=unique_user.token)
    assert response.status_code == 200
    assert response.json()["status"] == "working"
    draft = get_draft(api_client, unique_user, draft_id).json()
    assert draft["status"] == "ready"
    assert draft["error"] is None


def test_retry_needs_failed(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    draft_id = post_draft(api_client, unique_user, data={"text": TEXT}).json()["id"]
    response = api_client.post(f"{DRAFTS}/{draft_id}/retry", headers=unique_user.token)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "not_failed"


def test_stale_working_draft_is_interrupted(api_client: TestClient, session: Session, unique_user: TestUser):
    repo = drafts_repo(session, unique_user.group_id, unique_user.household_id)
    draft = repo.create(
        {
            "user_id": unique_user.user_id,
            "status": "working",
            "source_type": "text",
            "source_text": TEXT,
            "group_id": unique_user.group_id,
            "household_id": unique_user.household_id,
        }
    )
    session.execute(
        sa.update(KhDraft).where(KhDraft.id == draft.id).values(update_at=get_utc_now() - timedelta(minutes=20))
    )
    session.commit()

    after = get_draft(api_client, unique_user, str(draft.id)).json()
    assert after["status"] == "failed"
    assert after["error"] == "interrupted"


def test_fresh_working_draft_stays_working(api_client: TestClient, session: Session, unique_user: TestUser):
    repo = drafts_repo(session, unique_user.group_id, unique_user.household_id)
    draft = repo.create(
        {
            "user_id": unique_user.user_id,
            "status": "working",
            "source_type": "text",
            "source_text": TEXT,
            "group_id": unique_user.group_id,
            "household_id": unique_user.household_id,
        }
    )
    assert get_draft(api_client, unique_user, str(draft.id)).json()["status"] == "working"


def test_other_household_and_group_see_nothing(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, g2_user: TestUser, fake_ai
):
    fake_ai("recipe.json")
    draft_id = post_draft(api_client, unique_user, data={"text": TEXT}).json()["id"]
    assert draft_id in open_ids(api_client, unique_user)
    assert draft_id not in open_ids(api_client, h2_user)
    assert get_draft(api_client, h2_user, draft_id).status_code == 404
    assert get_draft(api_client, g2_user, draft_id).status_code == 404


def test_ai_model_is_recorded(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    provider = unique_user.repos.group_ai_providers.create(
        AIProviderCreate(name="Testanbieter", model="test-model", api_key="test-key")
    )
    settings_url = "/api/groups/ai-providers/settings"
    choose = {"defaultProviderId": str(provider.id), "audioProviderId": None, "imageProviderId": None}
    assert api_client.put(settings_url, json=choose, headers=unique_user.token).status_code == 200
    try:
        draft_id = post_draft(api_client, unique_user, data={"text": TEXT}).json()["id"]
        assert get_draft(api_client, unique_user, draft_id).json()["aiModel"] == "Testanbieter (test-model)"
    finally:
        reset = {"defaultProviderId": None, "audioProviderId": None, "imageProviderId": None}
        api_client.put(settings_url, json=reset, headers=unique_user.token)
        unique_user.repos.group_ai_providers.delete(provider.id)
