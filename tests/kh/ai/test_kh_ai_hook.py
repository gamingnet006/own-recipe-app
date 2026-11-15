"""KH: tests for hooking the AI priority list into Mealie (D39): Mealie's AI requests without a given provider go
through the list, the provider test and saving a provider set its state, and drafts show the outcome."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import openai
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

import mealie
from mealie.db.models.group.ai_providers import AIProviderSettings
from mealie.kh.ai.models import KhAiProviderState
from mealie.kh.ai.state import END_POSITION, in_order, load_states, save_state, sync_mealie_roles
from mealie.lang import get_locale_provider
from mealie.schema.group.ai_providers import AIProviderCreate
from mealie.schema.openai.general import OpenAIText
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.services.openai.openai import OpenAILocalAudio, OpenAIService
from mealie.services.recipe.ai_recipe_service import AIRecipeService
from mealie.services.scraper import scraper
from tests.kh.ai.conftest import ANSWER, FakeAI
from tests.kh.drafts.helpers import get_draft, png, post_draft
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

REQUEST = httpx.Request("POST", "https://ai.example/v1/chat/completions")
DRAFT_DATA = Path(__file__).parent.parent / "drafts" / "data"
KH0002 = (
    Path(mealie.__file__).parent
    / "kh"
    / "alembic"
    / "versions"
    / "2026-11-04-00.00.00_kh0002_add_ai_state_and_notices.py"
)


def kh0002() -> ModuleType:
    """The migration that added the list, loaded from its file like Alembic does."""
    spec = importlib.util.spec_from_file_location("kh0002", KH0002)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def status_error(cls: type[openai.APIStatusError], code: int):
    """An error of the openai package as a provider's answer with this status raises it."""
    return cls("provider error", response=httpx.Response(code, request=REQUEST), body=None)


def roles(user: TestUser) -> tuple:
    """Mealie's default and image provider of the user's group."""
    settings = user.repos.session.execute(
        sa.select(AIProviderSettings).where(AIProviderSettings.group_id == user.group_id)
    ).scalar_one()
    return settings.default_provider_id, settings.image_provider_id


@pytest.mark.asyncio
async def test_without_a_provider_the_chain_answers(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = status_error(openai.AuthenticationError, 401)
    assert await OpenAIService(unique_user.repos).get_response("p", "m", response_schema=OpenAIText) == ANSWER
    assert fake_ai_calls.calls == ["A", "B"]


@pytest.mark.asyncio
async def test_a_given_provider_skips_the_chain(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = openai.APIConnectionError(request=REQUEST)
    with pytest.raises(Exception, match="OpenAI Request Failed"):
        await OpenAIService(unique_user.repos).get_response(
            "p", "m", response_schema=OpenAIText, provider=providers["A"]
        )
    assert fake_ai_calls.calls == ["A"]


@pytest.mark.asyncio
async def test_audio_keeps_mealies_way(
    unique_user: TestUser, providers, fake_ai_calls: FakeAI, monkeypatch: pytest.MonkeyPatch
):
    picked: list[Any] = []

    def get_provider(self, attachments=None):
        picked.append(attachments)
        return providers["C"]

    monkeypatch.setattr(OpenAIService, "_get_provider", get_provider)
    audio = OpenAILocalAudio(data="UklGRg==", format="wav")
    answer = await OpenAIService(unique_user.repos).get_response(
        "p", "m", response_schema=OpenAIText, attachments=[audio]
    )
    assert answer == ANSWER
    assert len(picked) == 1
    assert fake_ai_calls.calls == ["C"]


@pytest.mark.asyncio
async def test_green_test_stores_images_and_ready(
    unique_user: TestUser, providers, fake_ai_calls: FakeAI, monkeypatch: pytest.MonkeyPatch
):
    async def reads_images(self, provider):
        return True

    monkeypatch.setattr(OpenAIService, "_check_image_support", reads_images)
    save_state(unique_user.repos.session, providers["A"].id, status="key")
    result = await OpenAIService(unique_user.repos).test_connection(providers["A"])
    assert result.success
    state = load_states(unique_user.repos.session, [providers["A"].id])[providers["A"].id]
    assert (state.status, state.supports_images) == ("ready", True)


@pytest.mark.asyncio
async def test_red_test_marks_the_key(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = status_error(openai.AuthenticationError, 401)
    result = await OpenAIService(unique_user.repos).test_connection(providers["A"])
    assert not result.success
    assert load_states(unique_user.repos.session, [providers["A"].id])[providers["A"].id].status == "key"


@pytest.mark.asyncio
async def test_a_test_of_unsaved_edits_stores_nothing(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = status_error(openai.AuthenticationError, 401)
    edited = providers["A"].model_copy(update={"model": "model-new"})
    await OpenAIService(unique_user.repos).test_connection(edited)
    assert load_states(unique_user.repos.session, [providers["A"].id])[providers["A"].id].status == "ready"


def test_saving_a_provider_makes_it_ready(unique_user: TestUser, providers):
    save_state(unique_user.repos.session, providers["A"].id, status="key")
    unique_user.repos.group_ai_providers.update(providers["A"].id, AIProviderCreate(name="A", model="model-a2"))
    state = load_states(unique_user.repos.session, [providers["A"].id])[providers["A"].id]
    assert (state.status, state.paused_until) == ("ready", None)


def test_roles_follow_the_order(unique_user: TestUser, providers):
    session = unique_user.repos.session
    save_state(session, providers["B"].id, position=0, supports_images=False)
    save_state(session, providers["A"].id, position=1, supports_images=True)
    save_state(session, providers["C"].id, position=2, supports_images=False)
    sync_mealie_roles(session, unique_user.group_id)
    assert roles(unique_user) == (providers["B"].id, providers["A"].id)


def test_new_providers_get_mealies_roles(unique_user: TestUser, providers):
    assert roles(unique_user) == (providers["A"].id, providers["A"].id)


def test_saving_settings_keeps_the_list_roles(api_client: TestClient, unique_user: TestUser, providers):
    stale = {"defaultProviderId": str(providers["C"].id), "imageProviderId": str(providers["C"].id)}
    response = api_client.put(
        "/api/groups/ai-providers/settings",
        json={**stale, "audioProviderId": str(providers["C"].id)},
        headers=unique_user.token,
    )
    assert response.status_code == 200
    saved = response.json()
    assert (saved["defaultProviderId"], saved["imageProviderId"]) == (str(providers["A"].id), str(providers["A"].id))
    assert saved["audioProviderId"] == str(providers["C"].id)


def test_draft_shows_ai_unavailable(api_client: TestClient, unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    for name in providers:
        fake_ai_calls.behavior[name] = openai.APIConnectionError(request=REQUEST)
    draft = post_draft(api_client, unique_user, data={"text": "Testkuchen: 200 g Mehl, 2 Eier."}).json()
    assert get_draft(api_client, unique_user, draft["id"]).json()["error"] == "ai_unavailable"


@pytest.mark.parametrize(
    ("failure", "code"),
    [
        (lambda: openai.APIConnectionError(request=REQUEST), "ai_unavailable"),
        (lambda: status_error(openai.RateLimitError, 429), "quota_exceeded"),
    ],
)
def test_photo_draft_tells_an_outage_from_a_missing_recipe(
    api_client: TestClient, unique_user: TestUser, providers, fake_ai_calls: FakeAI, failure, code
):
    # reading a photo is the AI request itself: Mealie's import must not take an outage for "no recipe found"
    for name in providers:
        fake_ai_calls.behavior[name] = failure
    draft = post_draft(api_client, unique_user, files=[("images", ("zettel.png", png(400, 300), "image/png"))]).json()
    assert get_draft(api_client, unique_user, draft["id"]).json()["error"] == code


def test_saving_a_new_model_forgets_image_support(unique_user: TestUser, providers):
    session = unique_user.repos.session
    save_state(session, providers["A"].id, supports_images=True)
    unique_user.repos.group_ai_providers.update(providers["A"].id, AIProviderCreate(name="A2", model="model-a"))
    assert load_states(session, [providers["A"].id])[providers["A"].id].supports_images is True
    unique_user.repos.group_ai_providers.update(providers["A"].id, AIProviderCreate(name="A2", model="model-a2"))
    assert load_states(session, [providers["A"].id])[providers["A"].id].supports_images is None


def test_a_new_provider_goes_last(unique_user: TestUser, providers):
    session = unique_user.repos.session
    new = unique_user.repos.group_ai_providers.create({"name": "0 Neu", "api_key": "test-key", "model": "model-new"})
    every = [*providers.values(), new]
    ordered = in_order(every, load_states(session, [p.id for p in every]))
    assert [p.name for p in ordered] == ["A", "B", "C", "0 Neu"]


def test_upgrade_starts_with_mealies_roles(unique_user: TestUser, providers):
    session = unique_user.repos.session
    settings = session.execute(
        sa.select(AIProviderSettings).where(AIProviderSettings.group_id == unique_user.group_id)
    ).scalar_one()
    settings.default_provider_id = providers["C"].id
    settings.image_provider_id = providers["B"].id
    ids = [p.id for p in providers.values()]
    session.execute(sa.delete(KhAiProviderState).where(KhAiProviderState.provider_id.in_(ids)))
    session.commit()
    kh0002().seed_order(session.connection())
    session.commit()
    states = load_states(session, ids)
    assert (states[providers["C"].id].position, states[providers["C"].id].supports_images) == (0, None)
    assert (states[providers["B"].id].position, states[providers["B"].id].supports_images) == (1, True)
    assert states[providers["A"].id].position == END_POSITION


def test_draft_names_the_provider_that_answered(
    api_client: TestClient, unique_user: TestUser, providers, fake_ai_calls: FakeAI, monkeypatch: pytest.MonkeyPatch
):
    async def build_recipe(self: AIRecipeService, **kwargs: Any) -> RecipeDraft:
        await OpenAIService(self.repos).get_response("p", "m", response_schema=OpenAIText)
        recorded = RecipeDraft.model_validate(json.loads((DRAFT_DATA / "recipe.json").read_text()))
        return await scraper.finalize_scraped_recipe(recorded, self.translator)

    monkeypatch.setattr(AIRecipeService, "build_recipe", build_recipe)
    fake_ai_calls.behavior["A"] = status_error(openai.RateLimitError, 429)
    draft = post_draft(api_client, unique_user, data={"text": "Testkuchen: 200 g Mehl, 2 Eier."}).json()
    assert get_draft(api_client, unique_user, draft["id"]).json()["aiModel"] == "B (model-b)"


def test_draft_names_every_provider_that_answered(
    api_client: TestClient, unique_user: TestUser, providers, fake_ai_calls: FakeAI, monkeypatch: pytest.MonkeyPatch
):
    async def build_recipe(self: AIRecipeService, **kwargs: Any) -> RecipeDraft:
        ai = OpenAIService(self.repos)
        await ai.get_response("p", "m", response_schema=OpenAIText)  # A reads the source
        fake_ai_calls.behavior["A"] = status_error(openai.RateLimitError, 429)
        await ai.get_response("p", "m", response_schema=OpenAIText)  # A's quota is gone: B builds the recipe
        recorded = RecipeDraft.model_validate(json.loads((DRAFT_DATA / "recipe.json").read_text()))
        return await scraper.finalize_scraped_recipe(recorded, self.translator)

    monkeypatch.setattr(AIRecipeService, "build_recipe", build_recipe)
    draft = post_draft(api_client, unique_user, data={"text": "Testkuchen: 200 g Mehl, 2 Eier."}).json()
    assert get_draft(api_client, unique_user, draft["id"]).json()["aiModel"] == "A (model-a), B (model-b)"


def test_mealies_import_page_names_an_outage(
    api_client: TestClient, unique_user: TestUser, providers, fake_ai_calls: FakeAI
):
    # Mealie's own AI import says "AI request failed", not "unknown error", when no provider of the list answers
    for name in providers:
        fake_ai_calls.behavior[name] = openai.APIConnectionError(request=REQUEST)
    response = api_client.post(
        api_routes.recipes_create_ai, data={"content": "Testkuchen: 200 g Mehl, 2 Eier."}, headers=unique_user.token
    )
    assert response.status_code == 400
    expected = get_locale_provider("en-US").t("recipe.import-errors.ai-request-failed")
    assert response.json()["detail"]["message"] == expected
