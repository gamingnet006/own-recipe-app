"""KH: tests for hooking the AI priority list into Mealie (D39): Mealie's AI requests without a given provider go
through the list, the provider test and saving a provider set its state, and drafts show the outcome."""

import json
from pathlib import Path
from typing import Any

import httpx
import openai
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.db.models.group.ai_providers import AIProviderSettings
from mealie.kh.ai.state import load_states, save_state, sync_mealie_roles
from mealie.schema.openai.general import OpenAIText
from mealie.schema.recipe.recipe import Recipe
from mealie.services.openai.openai import OpenAILocalAudio, OpenAIService
from mealie.services.recipe.ai_recipe_service import AIRecipeService
from mealie.services.scraper import scraper
from tests.kh.ai.conftest import ANSWER, FakeAI
from tests.kh.drafts.helpers import get_draft, post_draft
from tests.utils.fixture_schemas import TestUser

REQUEST = httpx.Request("POST", "https://ai.example/v1/chat/completions")
DRAFT_DATA = Path(__file__).parent.parent / "drafts" / "data"


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
    unique_user.repos.group_ai_providers.update(providers["A"].id, {"name": "A", "model": "model-a2"})
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


def test_draft_names_the_provider_that_answered(
    api_client: TestClient, unique_user: TestUser, providers, fake_ai_calls: FakeAI, monkeypatch: pytest.MonkeyPatch
):
    async def build_recipe(self: AIRecipeService, **kwargs: Any) -> Recipe:
        await OpenAIService(self.repos).get_response("p", "m", response_schema=OpenAIText)
        recorded = Recipe.model_validate(json.loads((DRAFT_DATA / "recipe.json").read_text()))
        return await scraper.finalize_scraped_recipe(recorded, self.translator)

    monkeypatch.setattr(AIRecipeService, "build_recipe", build_recipe)
    fake_ai_calls.behavior["A"] = status_error(openai.RateLimitError, 429)
    draft = post_draft(api_client, unique_user, data={"text": "Testkuchen: 200 g Mehl, 2 Eier."}).json()
    assert get_draft(api_client, unique_user, draft["id"]).json()["aiModel"] == "B (model-b)"
