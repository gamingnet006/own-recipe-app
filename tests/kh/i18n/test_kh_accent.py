"""KH: tests for the accent colour: a person's own choice and the installation's, the public read, the manifest's
theme colour, and that the server's colour list matches the frontend table."""

import re
from collections.abc import Generator
from pathlib import Path

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.accent import ACCENTS, LIGHT_PRIMARY
from mealie.kh.navigation.models import KhUserNavigation
from mealie.kh.onboarding.models import KhAccountSettings
from mealie.routes.spa.manifest import build_manifest
from tests.utils.fixture_schemas import TestUser

NAVIGATION = "/api/kh/navigation"
SETTINGS = "/api/kh/admin/account-settings"
PUBLIC = "/api/kh/onboarding/accent"
TABLE = Path(__file__).parents[3] / "frontend/kh/app/lib/accent-colours.ts"


@pytest.fixture(autouse=True)
def no_accents(session) -> Generator[None]:
    """Every test starts and ends with no colour chosen by anyone (the installation's API cannot unset one)."""
    for table in (KhUserNavigation, KhAccountSettings):
        session.execute(sa.update(table).values(accent=None))
    session.commit()
    yield
    for table in (KhUserNavigation, KhAccountSettings):
        session.execute(sa.update(table).values(accent=None))
    session.commit()


def test_person_accent_round_trip_validation_and_giving_it_up(api_client: TestClient, unique_user: TestUser):
    put = lambda body: api_client.put(NAVIGATION, json={"hidden": [], **body}, headers=unique_user.token)  # noqa: E731
    assert api_client.get(NAVIGATION, headers=unique_user.token).json()["accent"] is None
    assert put({"accent": "beere"}).json()["accent"] == "beere"
    assert put({}).json()["accent"] == "beere"  # an older client keeps the choice
    assert put({"accent": "pink"}).status_code == 422
    assert put({"accent": "installation"}).json()["accent"] is None  # back to the installation's colour


def test_installation_accent_is_admin_only_and_public_to_read(api_client: TestClient, admin_token, unique_user):
    assert api_client.get(PUBLIC).json() == {"accent": None}
    assert api_client.put(SETTINGS, json={"accent": "petrol"}, headers=unique_user.token).status_code == 403
    assert api_client.put(SETTINGS, json={"accent": "pink"}, headers=admin_token).status_code == 422
    answer = api_client.put(SETTINGS, json={"accent": "petrol"}, headers=admin_token)
    assert answer.status_code == 200 and answer.json()["accent"] == "petrol"
    assert api_client.get(PUBLIC).json() == {"accent": "petrol"}


def test_manifest_theme_color_follows_the_installation(api_client: TestClient, admin_token):
    assert build_manifest()["theme_color"] == "#2F7A55"
    api_client.put(SETTINGS, json={"accent": "indigo"}, headers=admin_token)
    assert build_manifest()["theme_color"] == LIGHT_PRIMARY["indigo"]


def test_server_colours_match_the_frontend_table():
    table = TABLE.read_text()
    found = dict(re.findall(r'^\s+(\w+): \{ light: \{ primary: "(#\w+)"', table, re.MULTILINE))
    expected = dict(LIGHT_PRIMARY)
    found["salbei"] = "#2F7A55"  # written there from the look's constants
    assert tuple(expected) == ACCENTS
    assert {key: found.get(key) for key in expected} == expected
