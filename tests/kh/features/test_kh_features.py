"""KH: tests for the Mealie parts Küchenhelfer hides (PLAN.md phase 1): share links stay off unless
KH_SHARE_LINKS=true, and new groups are private and show no Mealie announcements."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from mealie.kh.features.settings import KhSettings, get_kh_settings
from mealie.routes import spa
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


@pytest.fixture
def share_links(monkeypatch: pytest.MonkeyPatch):
    """Sets the switch for one test; Mealie's own tests run with share links on (tests/conftest.py)."""

    def switch(on: bool) -> None:
        monkeypatch.setattr(get_kh_settings(), "share_links", on)

    return switch


@pytest.fixture
def share_token(api_client: TestClient, unique_user: TestUser) -> Generator[str]:
    """A recipe with a share token, created the way Mealie's recipe download creates one."""
    response = api_client.post(api_routes.recipes, json={"name": random_string()}, headers=unique_user.token)
    assert response.status_code == 201
    recipe = unique_user.repos.recipes.get_one(response.json())
    assert recipe

    response = api_client.post(api_routes.shared_recipes, json={"recipeId": str(recipe.id)}, headers=unique_user.token)
    assert response.status_code == 201
    yield response.json()["id"]

    unique_user.repos.recipes.delete(recipe.slug)


def test_share_links_are_off_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("KH_SHARE_LINKS", raising=False)
    assert KhSettings().share_links is False


def test_features_report_the_switch(api_client: TestClient, share_links):
    for on in (False, True):
        share_links(on)
        response = api_client.get("/api/kh/features")
        assert response.status_code == 200
        assert response.json() == {
            "shareLinks": on,
            "noticePollMinutes": 5,
            "sourceUrl": get_kh_settings().source_url,
            "clockShortcutUrl": None,
        }


def test_shared_recipe_is_hidden_when_off(api_client: TestClient, share_token: str, share_links):
    share_links(False)
    assert api_client.get(api_routes.recipes_shared_token_id(share_token)).status_code == 404


def test_recipe_download_still_works_when_off(api_client: TestClient, share_token: str, share_links):
    share_links(False)
    assert api_client.get(api_routes.recipes_shared_token_id_zip(share_token)).status_code == 200


def test_shared_recipe_is_visible_when_on(api_client: TestClient, share_token: str, share_links):
    share_links(True)
    assert api_client.get(api_routes.recipes_shared_token_id(share_token)).status_code == 200


@pytest.mark.asyncio
async def test_shared_recipe_page_shows_no_recipe_when_off(unique_user: TestUser, share_token: str, share_links):
    share_links(False)
    spa.__contents = "<!DOCTYPE html><html><head></head><body></body></html>"
    group = unique_user.repos.groups.get_by_slug_or_id(unique_user.group_id)
    assert group

    response = await spa.serve_shared_recipe_with_meta(group.slug, share_token, session=unique_user.repos.session)
    assert response.status_code == 404


def test_new_group_is_private_and_shows_no_announcements(api_client: TestClient, admin_user: TestUser):
    response = api_client.post(api_routes.admin_groups, json={"name": random_string()}, headers=admin_user.token)
    assert response.status_code == 201
    group = response.json()

    assert group["preferences"]["privateGroup"] is True
    assert group["preferences"]["showAnnouncements"] is False
    assert api_client.get(api_routes.explore_groups_group_slug_recipes(group["slug"])).status_code == 404


def test_features_name_the_poll_interval(api_client: TestClient):
    assert api_client.get("/api/kh/features").json()["noticePollMinutes"] == 5


VALID_SHORTCUT = "https://www.icloud.com/shortcuts/0123456789abcdefABCDEF"


def test_clock_shortcut_url_is_unset_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("KH_CLOCK_SHORTCUT_URL", raising=False)
    assert KhSettings().clock_shortcut_url is None


@pytest.mark.parametrize("url", [VALID_SHORTCUT, VALID_SHORTCUT + "/"])
def test_clock_shortcut_url_passes_a_shortcuts_link(monkeypatch: pytest.MonkeyPatch, url: str):
    monkeypatch.setenv("KH_CLOCK_SHORTCUT_URL", url)
    assert KhSettings().clock_shortcut_url == url


@pytest.mark.parametrize(
    "url",
    [
        "http://www.icloud.com/shortcuts/abc123",
        "https://example.com/shortcuts/abc123",
        "https://www.icloud.com.evil.test/shortcuts/abc123",
        "https://www.icloud.com/shortcuts/",
        "https://www.icloud.com/shortcuts/abc123?x=1",
        "javascript:alert(1)",
    ],
)
def test_clock_shortcut_url_drops_anything_else_and_warns(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, url: str
):
    monkeypatch.setenv("KH_CLOCK_SHORTCUT_URL", url)
    with caplog.at_level("WARNING"):
        assert KhSettings().clock_shortcut_url is None
    assert "KH_CLOCK_SHORTCUT_URL" in caplog.text
    assert url not in caplog.text


def test_features_report_the_shortcut_url(api_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(get_kh_settings(), "clock_shortcut_url", VALID_SHORTCUT)
    assert api_client.get("/api/kh/features").json()["clockShortcutUrl"] == VALID_SHORTCUT
