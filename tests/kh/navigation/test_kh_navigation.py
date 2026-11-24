"""KH: tests for each person's own side menu (D58) and the
simple view switch (D79): nothing hidden by default, the round trip, unknown keys refused,
other users unaffected, and the row gone when the user is deleted."""

from collections.abc import Generator
from uuid import uuid4

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.navigation.models import KhUserNavigation
from tests import utils
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

NAVIGATION = "/api/kh/navigation"


def put(api_client: TestClient, user: TestUser, hidden: list[str], **extra):
    return api_client.put(NAVIGATION, json={"hidden": hidden, **extra}, headers=user.token)


def hidden_of(api_client: TestClient, user: TestUser) -> list[str]:
    return api_client.get(NAVIGATION, headers=user.token).json()["hidden"]


@pytest.fixture(autouse=True)
def nothing_hidden(api_client: TestClient, unique_user: TestUser, household_member: TestUser) -> Generator[None]:
    """The users live for the whole module: every test starts and ends with the default."""
    for user in (unique_user, household_member):
        put(api_client, user, [], simple=False)
    yield
    for user in (unique_user, household_member):
        put(api_client, user, [], simple=False)


def test_default_hides_nothing(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(NAVIGATION, headers=unique_user.token).json() == {
        "hidden": [],
        "simple": False,
        "locale": None,
    }


def test_round_trip_without_duplicates_in_the_menus_order(api_client: TestClient, unique_user: TestUser):
    answer = put(api_client, unique_user, ["timeline", "finder", "timeline"])
    assert answer.status_code == 200 and answer.json() == {
        "hidden": ["finder", "timeline"],
        "simple": False,
        "locale": None,
    }
    assert hidden_of(api_client, unique_user) == ["finder", "timeline"]
    assert put(api_client, unique_user, []).json() == {"hidden": [], "simple": False, "locale": None}


@pytest.mark.parametrize("key", ["recipes", "more", "nonsense", ""])
def test_unknown_or_fixed_keys_are_refused(api_client: TestClient, unique_user: TestUser, key: str):
    put(api_client, unique_user, ["finder"])
    assert put(api_client, unique_user, [key]).status_code == 422
    assert hidden_of(api_client, unique_user) == ["finder"]


def test_other_users_are_unaffected(api_client: TestClient, unique_user: TestUser, household_member: TestUser):
    put(api_client, unique_user, ["cookbooks"])
    assert hidden_of(api_client, household_member) == []


def test_simple_view_is_stored_and_kept_by_a_hidden_only_request(api_client: TestClient, unique_user: TestUser):
    assert put(api_client, unique_user, ["finder"], simple=True).json() == {
        "hidden": ["finder"],
        "simple": True,
        "locale": None,
    }
    # an older client sends no "simple": the stored switch stays
    assert put(api_client, unique_user, []).json() == {"hidden": [], "simple": True, "locale": None}
    assert api_client.get(NAVIGATION, headers=unique_user.token).json()["simple"] is True


def test_admin_switches_simple_view_for_another_person(
    api_client: TestClient, admin_token, unique_user: TestUser, household_member: TestUser
):
    url = f"/api/kh/admin/navigation/{household_member.user_id}"
    assert api_client.get(url, headers=admin_token).json() == {"simple": False}
    assert api_client.put(url, json={"simple": True}, headers=admin_token).json() == {"simple": True}
    assert api_client.get(NAVIGATION, headers=household_member.token).json()["simple"] is True
    assert api_client.get(NAVIGATION, headers=unique_user.token).json()["simple"] is False


def test_only_the_admin_uses_the_admin_route(api_client: TestClient, admin_token, unique_user: TestUser):
    url = f"/api/kh/admin/navigation/{unique_user.user_id}"
    assert api_client.put(url, json={"simple": True}, headers=unique_user.token).status_code == 403
    missing = f"/api/kh/admin/navigation/{uuid4()}"
    assert api_client.put(missing, json={"simple": True}, headers=admin_token).status_code == 404


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
