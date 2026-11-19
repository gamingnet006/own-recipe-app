"""KH: tests for each person's own side menu (D58): nothing hidden by default, the round trip, unknown keys refused,
other users unaffected, and the row gone when the user is deleted."""

from collections.abc import Generator

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.navigation.models import KhUserNavigation
from tests import utils
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

NAVIGATION = "/api/kh/navigation"


def put(api_client: TestClient, user: TestUser, hidden: list[str]):
    return api_client.put(NAVIGATION, json={"hidden": hidden}, headers=user.token)


def hidden_of(api_client: TestClient, user: TestUser) -> list[str]:
    return api_client.get(NAVIGATION, headers=user.token).json()["hidden"]


@pytest.fixture(autouse=True)
def nothing_hidden(api_client: TestClient, unique_user: TestUser, household_member: TestUser) -> Generator[None]:
    """The users live for the whole module: every test starts and ends with the default."""
    for user in (unique_user, household_member):
        put(api_client, user, [])
    yield
    for user in (unique_user, household_member):
        put(api_client, user, [])


def test_default_hides_nothing(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(NAVIGATION, headers=unique_user.token).json() == {"hidden": []}


def test_round_trip_without_duplicates_in_the_menus_order(api_client: TestClient, unique_user: TestUser):
    answer = put(api_client, unique_user, ["timeline", "finder", "timeline"])
    assert answer.status_code == 200 and answer.json() == {"hidden": ["finder", "timeline"]}
    assert hidden_of(api_client, unique_user) == ["finder", "timeline"]
    assert put(api_client, unique_user, []).json() == {"hidden": []}


@pytest.mark.parametrize("key", ["recipes", "more", "nonsense", ""])
def test_unknown_or_fixed_keys_are_refused(api_client: TestClient, unique_user: TestUser, key: str):
    put(api_client, unique_user, ["finder"])
    assert put(api_client, unique_user, [key]).status_code == 422
    assert hidden_of(api_client, unique_user) == ["finder"]


def test_other_users_are_unaffected(api_client: TestClient, unique_user: TestUser, household_member: TestUser):
    put(api_client, unique_user, ["cookbooks"])
    assert hidden_of(api_client, household_member) == []


def test_needs_a_signed_in_user(api_client: TestClient):
    assert api_client.get(NAVIGATION).status_code == 401
    assert api_client.put(NAVIGATION, json={"hidden": []}).status_code == 401


def test_deleting_a_user_removes_the_row(api_client: TestClient, admin_token, unique_user: TestUser, session):
    group = api_client.get(api_routes.groups_self, headers=unique_user.token).json()["name"]
    household = api_client.get(api_routes.households_self, headers=unique_user.token).json()["name"]
    body = {
        "fullName": utils.random_string(),
        "username": utils.random_string(),
        "email": utils.random_email(),
        "password": "useruser",
        "group": group,
        "household": household,
        "admin": False,
        "tokens": [],
    }
    user_id = api_client.post(api_routes.admin_users, json=body, headers=admin_token).json()["id"]
    token = utils.login({"username": body["email"], "password": "useruser"}, api_client)
    assert api_client.put(NAVIGATION, json={"hidden": ["finder"]}, headers=token).status_code == 200
    assert session.execute(sa.select(KhUserNavigation).where(KhUserNavigation.user_id == user_id)).first()

    assert api_client.delete(api_routes.admin_users_item_id(user_id), headers=admin_token).status_code in (200, 404)
    session.expire_all()
    assert session.execute(sa.select(KhUserNavigation).where(KhUserNavigation.user_id == user_id)).first() is None
