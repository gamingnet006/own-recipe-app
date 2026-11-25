"""KH: tests for the Mealie parts Kochheft hides (PLAN.md phase 1): share links stay off unless
KH_SHARE_LINKS=true, and new groups are private and show no Mealie announcements."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from mealie.core.config import get_app_settings
from mealie.kh.features.settings import DEFAULT_CLOCK_SHORTCUT_URL, DEFAULT_SHORTCUT_URLS, KhSettings, get_kh_settings
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
            "shortcutUrls": {
                "de-DE": {
                    "clock": DEFAULT_CLOCK_SHORTCUT_URL,
                    "import": DEFAULT_SHORTCUT_URLS["import_shortcut_url"],
                    "siri": DEFAULT_SHORTCUT_URLS["siri_shortcut_url"],
                },
                "en-US": {
                    "clock": DEFAULT_SHORTCUT_URLS["clock_shortcut_url_en"],
                    "import": DEFAULT_SHORTCUT_URLS["import_shortcut_url_en"],
                    "siri": DEFAULT_SHORTCUT_URLS["siri_shortcut_url_en"],
                },
            },
            "emailReady": get_app_settings().SMTP_ENABLE,  # CI sets up a test mail server
            "draftMaxText": get_kh_settings().draft_max_text,
            "baseUrl": None if get_app_settings().is_default_base_url else get_app_settings().BASE_URL,
            "addressChangedAt": None,
            "media": False,
            "profile": "leicht",
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


def test_clock_shortcut_url_is_the_kochheft_timer_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("KH_CLOCK_SHORTCUT_URL", raising=False)
    assert KhSettings().clock_shortcut_url == DEFAULT_CLOCK_SHORTCUT_URL
    assert DEFAULT_CLOCK_SHORTCUT_URL == "https://www.icloud.com/shortcuts/c6b533e1ee864389831f5a2d7801a9c9"


def test_an_empty_clock_shortcut_url_keeps_the_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KH_CLOCK_SHORTCUT_URL", "")  # what Compose passes for an empty line in .env
    assert KhSettings().clock_shortcut_url == DEFAULT_CLOCK_SHORTCUT_URL


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


def test_features_name_the_base_url_only_when_it_is_set(api_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(get_app_settings(), "BASE_URL", "https://kochen.example.com")
    assert api_client.get("/api/kh/features").json()["baseUrl"] == "https://kochen.example.com"
    monkeypatch.setattr(get_app_settings(), "BASE_URL", "http://localhost:8080")
    assert api_client.get("/api/kh/features").json()["baseUrl"] is None


def test_features_report_the_shortcut_url(api_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(get_kh_settings(), "clock_shortcut_url", VALID_SHORTCUT)
    assert api_client.get("/api/kh/features").json()["shortcutUrls"]["de-DE"]["clock"] == VALID_SHORTCUT


@pytest.mark.parametrize("field", ["clock", "import", "siri"])
def test_english_shortcut_urls_come_from_their_own_settings(monkeypatch: pytest.MonkeyPatch, field: str):
    monkeypatch.setenv(f"KH_{field.upper()}_SHORTCUT_URL_EN", VALID_SHORTCUT)
    settings = KhSettings()
    assert settings.shortcut_urls()["en-US"][field] == VALID_SHORTCUT
    assert settings.shortcut_urls()["de-DE"][field] != VALID_SHORTCUT  # the German link is untouched
    monkeypatch.setenv(f"KH_{field.upper()}_SHORTCUT_URL_EN", "https://example.com/x")
    assert KhSettings().shortcut_urls()["en-US"][field] is None


@pytest.mark.parametrize(
    "field, url",
    [
        ("import", "https://www.icloud.com/shortcuts/647f18573b364b2c883ee0d2d5e70fcf"),
        ("clock", "https://www.icloud.com/shortcuts/0b52561241d441cd8581de23b5250166"),
        ("siri", "https://www.icloud.com/shortcuts/7df86c46bd414d50a8c8355d8267405b"),
    ],
)
def test_english_shortcuts_are_built_in(monkeypatch: pytest.MonkeyPatch, field: str, url: str):
    monkeypatch.delenv(f"KH_{field.upper()}_SHORTCUT_URL_EN", raising=False)
    assert KhSettings().shortcut_urls()["en-US"][field] == url


@pytest.mark.parametrize("name", ["KH_IMPORT_SHORTCUT_URL", "KH_SIRI_SHORTCUT_URL"])
def test_import_and_siri_shortcut_urls_take_only_shortcuts_links(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, name: str
):
    field = name.removeprefix("KH_").lower()
    monkeypatch.setenv(name, VALID_SHORTCUT)
    assert getattr(KhSettings(), field) == VALID_SHORTCUT
    monkeypatch.setenv(name, "https://example.com/shortcuts/abc123")
    with caplog.at_level("WARNING"):
        assert getattr(KhSettings(), field) is None
    assert name in caplog.text
    monkeypatch.setenv(name, "")  # what Compose passes for an empty line in .env: the built-in link
    assert getattr(KhSettings(), field) == DEFAULT_SHORTCUT_URLS[field]


def test_import_and_siri_shortcuts_are_built_in(monkeypatch: pytest.MonkeyPatch):
    """The maintainer's shared shortcuts ask for address and key on adding, so every install can offer them."""
    monkeypatch.delenv("KH_IMPORT_SHORTCUT_URL", raising=False)
    monkeypatch.delenv("KH_SIRI_SHORTCUT_URL", raising=False)
    assert KhSettings().import_shortcut_url == "https://www.icloud.com/shortcuts/3fd264e8918848f7b1022edd57e2210c"
    assert KhSettings().siri_shortcut_url == "https://www.icloud.com/shortcuts/28389dd5c63c42d2bfb983ba09201d04"
