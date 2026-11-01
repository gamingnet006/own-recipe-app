"""KH: tests for the recipe language (phase 2): what the AI reads is translated into KH_RECIPE_LANGUAGE by Mealie's
translate step; without one, recipes stay in the language they came in, and links with recipe data need no AI."""

import pytest
from fastapi.testclient import TestClient

from mealie.kh.features.settings import get_kh_settings
from tests.kh.drafts.helpers import png, post_draft
from tests.utils.fixture_schemas import TestUser

LINK = "https://example.org/poffertjes"
TEXT = "Poffertjes: 250 g bloem, 10 g gist, 2 eieren, 5 g zout."
SOURCES = {
    "text": {"data": {"text": TEXT}},
    "image": {"files": {"images": ("zettel.png", png(400, 300), "image/png")}},
    "link": {"data": {"url": LINK}},
}


@pytest.mark.parametrize("source", SOURCES)
def test_ai_translates_into_the_recipe_language(
    api_client: TestClient, unique_user: TestUser, fake_ai, fake_page, monkeypatch: pytest.MonkeyPatch, source: str
):
    monkeypatch.setattr(get_kh_settings(), "recipe_language", "German")
    fake_page(None)  # the link has no recipe data, so the AI reads it
    calls = fake_ai("recipe.json")
    post_draft(api_client, unique_user, **SOURCES[source])
    assert calls[0]["translate_language"] == "German"


def test_without_a_recipe_language_nothing_is_translated(api_client: TestClient, unique_user: TestUser, fake_ai):
    calls = fake_ai("recipe.json")
    post_draft(api_client, unique_user, data={"text": TEXT})
    assert calls[0]["translate_language"] is None


def test_a_link_with_recipe_data_still_needs_no_ai(
    api_client: TestClient, unique_user: TestUser, fake_ai, fake_page, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(get_kh_settings(), "recipe_language", "German")
    fake_page("page.html")
    calls = fake_ai("recipe.json")
    post_draft(api_client, unique_user, data={"url": LINK})
    assert calls == []
