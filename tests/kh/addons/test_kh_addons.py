"""KH: tests for the add-ons page (D46): defaults, who may change them, the limits set by the host, and the 403 that
every add-on's own endpoints answer while the household has it switched off."""

from collections.abc import Callable, Generator

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.addons.models import KhHouseholdAddons
from mealie.kh.addons.schemas import AddonFlags
from mealie.kh.addons.service import save_flags
from mealie.kh.features.settings import get_kh_settings
from tests.utils.fixture_schemas import TestUser

URL = "/api/kh/addons"


@pytest.fixture
def host(monkeypatch: pytest.MonkeyPatch):
    """A host with nothing optional set up: no share links, Telegram, Whisper or Clock shortcut."""
    settings = get_kh_settings()
    monkeypatch.setattr(settings, "share_links", False)
    monkeypatch.setattr(settings, "telegram_token", None)
    monkeypatch.setattr(settings, "whisper_url", None)
    monkeypatch.setattr(settings, "clock_shortcut_url", None)
    return settings


@pytest.fixture
def addons(unique_user: TestUser) -> Generator[Callable[..., None]]:
    """Stores the household's switches for one test (given as snake_case names); the row is removed afterwards."""

    def clear() -> None:
        unique_user.repos.session.execute(
            sa.delete(KhHouseholdAddons).where(KhHouseholdAddons.household_id == unique_user.household_id)
        )
        unique_user.repos.session.commit()

    def switch(**flags: bool) -> None:
        save_flags(unique_user.repos.session, unique_user.household_id, AddonFlags(**flags))

    clear()
    yield switch
    clear()


def test_defaults(api_client: TestClient, unique_user: TestUser, host, addons):
    body = api_client.get(URL, headers=unique_user.token).json()
    assert body["flags"] == body["enabled"]
    assert body["flags"]["shopping"] and body["flags"]["planner"] and body["flags"]["books"]
    assert body["flags"]["substitutions"] and body["flags"]["offline"] and body["flags"]["oven"]
    assert body["flags"]["clock"]  # as before v1.0: the button shows wherever the device's own switch is on
    assert not any(body["flags"][name] for name in ("shareLinks", "telegram", "whisper", "voice"))
    assert body["unavailable"] == ["shareLinks", "telegram", "whisper"]


def test_a_set_up_host_starts_those_add_ons_on(
    api_client: TestClient, unique_user: TestUser, host, addons, monkeypatch
):
    """Existing installs that set up Telegram, Whisper, share links or the Clock shortcut see no change (G5)."""
    monkeypatch.setattr(host, "share_links", True)
    monkeypatch.setattr(host, "telegram_token", "t")
    monkeypatch.setattr(host, "whisper_url", "http://w")
    monkeypatch.setattr(host, "clock_shortcut_url", "https://www.icloud.com/shortcuts/abc")
    body = api_client.get(URL, headers=unique_user.token).json()
    assert all(body["enabled"][name] for name in ("clock", "shareLinks", "telegram", "whisper"))
    assert body["unavailable"] == []


def test_only_admins_change_the_switches(api_client: TestClient, unique_user: TestUser, unique_admin: TestUser, host):
    flags = api_client.get(URL, headers=unique_admin.token).json()["flags"]
    flags["books"] = False
    assert api_client.put(URL, json=flags, headers=unique_user.token).status_code == 403
    answer = api_client.put(URL, json=flags, headers=unique_admin.token)
    assert answer.status_code == 200
    assert answer.json()["enabled"]["books"] is False
    # it is the admin's household that changed; everyone in it can read it
    assert api_client.get(URL, headers=unique_admin.token).json()["flags"]["books"] is False
    assert api_client.get(URL, headers=unique_user.token).json()["flags"]["books"] is True
    flags["books"] = True
    api_client.put(URL, json=flags, headers=unique_admin.token)


def test_what_the_host_does_not_offer_stays_off(api_client: TestClient, unique_user: TestUser, host, addons):
    addons(share_links=True, telegram=True, whisper=True)
    body = api_client.get(URL, headers=unique_user.token).json()
    assert body["flags"]["shareLinks"] is True  # the choice is kept for when the host sets it up
    assert not any(body["enabled"][name] for name in ("shareLinks", "telegram", "whisper"))


def test_variants_need_allergens(api_client: TestClient, unique_user: TestUser, host, addons):
    addons(allergens=False, substitutions=True)
    body = api_client.get(URL, headers=unique_user.token).json()
    assert body["flags"]["substitutions"] is True
    assert body["enabled"]["substitutions"] is False


def test_a_stored_switch_this_version_does_not_know_is_ignored(api_client: TestClient, unique_user: TestUser, addons):
    addons(books=False)  # stores the row; then a newer version's switch appears in it, as after restoring its backup
    row = unique_user.repos.session.execute(
        sa.select(KhHouseholdAddons).where(KhHouseholdAddons.household_id == unique_user.household_id)
    ).scalar_one()
    row.flags = {**row.flags, "future_addon": True}
    unique_user.repos.session.commit()
    response = api_client.get(URL, headers=unique_user.token)
    assert response.status_code == 200
    assert response.json()["flags"]["books"] is False


def test_unknown_switches_are_refused(api_client: TestClient, unique_admin: TestUser):
    assert api_client.put(URL, json={"nonsense": True}, headers=unique_admin.token).status_code == 422


# (method, path, the add-on whose switch guards it)
GUARDED = [
    ("get", "/api/kh/cookbooks/00000000-0000-0000-0000-000000000000/print", "books"),
    ("get", "/api/kh/recipes/flags", "books"),
    ("get", "/api/kh/duplicates", "duplicates"),
    ("get", "/api/kh/nutrition/foods", "nutrition"),
    ("get", "/api/kh/recipes/x/nutrition", "nutrition"),
    ("get", "/api/kh/recipes/x/allergens", "allergens"),
    ("get", "/api/kh/users/self/allergies", "allergens"),
    ("get", "/api/kh/allergens/warnings", "allergens"),
    ("get", "/api/kh/substitutions", "substitutions"),
    ("post", "/api/kh/recipes/x/variant", "substitutions"),
]


@pytest.mark.parametrize(("method", "path", "name"), GUARDED)
def test_endpoints_answer_403_while_off(api_client: TestClient, unique_user: TestUser, addons, method, path, name):
    addons(**{name: False})
    answer = getattr(api_client, method)(path, headers=unique_user.token)
    assert answer.status_code == 403
    assert "Zusatzfunktionen" in answer.json()["detail"]["message"]


@pytest.mark.parametrize(("method", "path", "name"), GUARDED)
def test_endpoints_work_while_on(api_client: TestClient, unique_user: TestUser, addons, method, path, name):
    addons()
    assert getattr(api_client, method)(path, headers=unique_user.token).status_code != 403


def test_substitutions_follow_allergens(api_client: TestClient, unique_user: TestUser, addons):
    addons(allergens=False, substitutions=True)
    assert api_client.get("/api/kh/substitutions", headers=unique_user.token).status_code == 403


def test_recordings_need_whisper_on(api_client: TestClient, unique_user: TestUser, host, addons, monkeypatch):
    monkeypatch.setattr(host, "whisper_url", "http://whisper")
    addons(whisper=False)
    files = {"media": ("a.mp3", b"x", "audio/mpeg")}
    answer = api_client.post("/api/kh/drafts", files=files, headers=unique_user.token)
    assert answer.status_code == 403
    # without a recording the add-on is not asked (no source at all is refused for its own reason)
    assert api_client.post("/api/kh/drafts", headers=unique_user.token).status_code == 400


def test_telegram_drafts_need_telegram_on(api_client: TestClient, unique_user: TestUser, host, addons, monkeypatch):
    monkeypatch.setattr(host, "telegram_token", "t")
    addons(telegram=False)
    headers = {**unique_user.token, "X-KH-Via": "telegram"}
    assert api_client.post("/api/kh/drafts", data={"text": "Pfannkuchen"}, headers=headers).status_code == 403
    addons(telegram=True)
    assert api_client.post("/api/kh/drafts", headers=headers).status_code == 400  # past the add-on check


def test_a_shared_recipe_is_hidden_while_the_household_has_links_off(
    api_client: TestClient, unique_user: TestUser, host, addons, monkeypatch
):
    monkeypatch.setattr(host, "share_links", True)
    recipe = api_client.post("/api/recipes", json={"name": "Teilen"}, headers=unique_user.token)
    assert recipe.status_code == 201
    recipe_id = unique_user.repos.recipes.get_one(recipe.json()).id
    token = api_client.post("/api/shared/recipes", json={"recipeId": str(recipe_id)}, headers=unique_user.token)
    url = f"/api/recipes/shared/{token.json()['id']}"
    addons(share_links=True)
    assert api_client.get(url).status_code == 200
    addons(share_links=False)
    assert api_client.get(url).status_code == 404


def test_telegram_is_unavailable_in_the_local_profile(
    api_client: TestClient, unique_user: TestUser, host, addons, monkeypatch
):
    """Profile "lokal" keeps everything in the house; Telegram's servers are outside it."""
    monkeypatch.setattr(host, "telegram_token", "t")
    monkeypatch.setattr(host, "profile", "lokal")
    body = api_client.get(URL, headers=unique_user.token).json()
    assert "telegram" in body["unavailable"]
    assert not body["enabled"]["telegram"]
