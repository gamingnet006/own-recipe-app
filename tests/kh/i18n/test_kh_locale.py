"""KH: tests for the language of a person: storing it on the account and on the installation, the public read, and
the server's choice (account, then Accept-Language, then installation, then German)."""

from collections.abc import Generator

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.i18n.locale import accept_language_locale, person_locale
from mealie.kh.navigation.models import KhUserNavigation
from mealie.kh.onboarding.models import KhAccountSettings
from tests.utils.fixture_schemas import TestUser

NAVIGATION = "/api/kh/navigation"
SETTINGS = "/api/kh/admin/account-settings"
PUBLIC = "/api/kh/onboarding/locale"


@pytest.fixture(autouse=True)
def no_locales(session) -> Generator[None]:
    """Every test starts and ends with no language chosen by anyone (the API cannot unset one)."""
    for table in (KhUserNavigation, KhAccountSettings):
        session.execute(sa.update(table).values(locale=None))
    session.commit()
    yield
    for table in (KhUserNavigation, KhAccountSettings):
        session.execute(sa.update(table).values(locale=None))
    session.commit()


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, None),
        ("", None),
        ("fr-FR,fr;q=0.9", None),
        ("de-AT,de;q=0.9,en;q=0.8", "de-DE"),
        ("fr, en-GB;q=0.8", "en-US"),
        ("en;q=0.4, de;q=0.9", "de-DE"),
        ("en;q=oops, fr", None),
    ],
)
def test_accept_language_picks_german_or_english(header, expected):
    assert accept_language_locale(header) == expected


def test_navigation_locale_round_trip_and_validation(api_client: TestClient, unique_user: TestUser):
    put = lambda body: api_client.put(NAVIGATION, json={"hidden": [], **body}, headers=unique_user.token)  # noqa: E731
    assert api_client.get(NAVIGATION, headers=unique_user.token).json()["locale"] is None
    assert put({"locale": "en-US"}).json()["locale"] == "en-US"
    assert put({}).json()["locale"] == "en-US"  # an older client keeps the choice
    assert put({"locale": "de-DE"}).json()["locale"] == "de-DE"
    assert put({"locale": "fr-FR"}).status_code == 422
    assert api_client.get(NAVIGATION, headers=unique_user.token).json()["locale"] == "de-DE"


def test_installation_locale_is_admin_only_and_public_to_read(api_client: TestClient, admin_token, unique_user):
    assert api_client.get(PUBLIC).json() == {"locale": None}
    assert api_client.put(SETTINGS, json={"locale": "en-US"}, headers=unique_user.token).status_code == 403
    assert api_client.put(SETTINGS, json={"locale": "xx"}, headers=admin_token).status_code == 422
    answer = api_client.put(SETTINGS, json={"locale": "en-US"}, headers=admin_token)
    assert answer.status_code == 200 and answer.json()["locale"] == "en-US"
    assert api_client.get(PUBLIC).json() == {"locale": "en-US"}  # no sign-in needed, nothing else revealed


def test_person_locale_order(api_client: TestClient, admin_token, unique_user: TestUser, session):
    user_id = unique_user.user_id
    assert person_locale(session, user_id, None) == "de-DE"  # existing installs stay German
    api_client.put(SETTINGS, json={"locale": "en-US"}, headers=admin_token)
    session.expire_all()
    assert person_locale(session, user_id, None) == "en-US"  # installation
    assert person_locale(session, user_id, "de;q=0.9") == "de-DE"  # request beats installation
    assert person_locale(session, user_id, "fr") == "en-US"  # no de/en in the request
    api_client.put(NAVIGATION, json={"hidden": [], "locale": "de-DE"}, headers=unique_user.token)
    session.expire_all()
    assert person_locale(session, user_id, "en") == "de-DE"  # the account beats everything
    assert person_locale(session, None, "en") == "en-US"  # nobody signed in


def test_manifest_name_follows_the_installation_language(api_client: TestClient, admin_token):
    from mealie.routes.spa.manifest import build_manifest

    assert build_manifest()["name"] == "Kochheft"
    api_client.put(SETTINGS, json={"locale": "en-US"}, headers=admin_token)
    manifest = build_manifest()
    assert (manifest["name"], manifest["short_name"]) == ("Cookbook", "Cookbook")
    assert manifest["description"].startswith("Cookbook ")
    api_client.put(SETTINGS, json={"locale": "de-DE"}, headers=admin_token)
    assert build_manifest()["name"] == "Kochheft"
