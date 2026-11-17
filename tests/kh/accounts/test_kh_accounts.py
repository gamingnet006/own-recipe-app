"""KH: tests for switching households (D52): linked accounts created by the admin, the switch endpoint, the
permissions and allergies that follow the primary account, and the clean-up when an account is deleted."""

from collections.abc import Callable, Generator
from uuid import UUID

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.db.models.users.users import User
from mealie.kh.accounts.models import KhAccountLink
from mealie.kh.allergens.models import KhUserAllergies
from tests import utils
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

LIST = "/api/kh/accounts"
SWITCH = "/api/kh/accounts/switch"
ADMIN = "/api/kh/admin/accounts"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_link(api_client: TestClient, admin_token, unique_user: TestUser) -> Generator[Callable[..., dict]]:
    """Links a person to a household as the admin and returns the new account; every account made is deleted again."""
    made: list[str] = []

    def link(household_id: UUID, user_id: UUID | None = None, expect: int = 201) -> dict:
        response = api_client.post(
            ADMIN,
            json={"userId": str(user_id or unique_user.user_id), "householdId": str(household_id)},
            headers=admin_token,
        )
        assert response.status_code == expect, response.text
        body = response.json()
        if expect == 201:
            made.append(body["userId"])
        return body

    yield link
    for user_id in made:
        api_client.delete(api_routes.admin_users_item_id(user_id), headers=admin_token)


@pytest.fixture(scope="module")
def third_household(api_client: TestClient, admin_token, unique_user: TestUser) -> UUID:
    """An empty household in unique_user's group, for the chain test."""
    body = {"name": utils.random_string(12), "groupId": str(unique_user.group_id)}
    response = api_client.post(api_routes.admin_households, json=body, headers=admin_token)
    return UUID(response.json()["id"])


def switch(api_client: TestClient, token: dict[str, str], user_id: UUID | str):
    return api_client.post(SWITCH, json={"userId": str(user_id)}, headers=token)


def test_only_the_admin_links_and_unlinks(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    body = {"userId": str(unique_user.user_id), "householdId": str(h2_user.household_id)}
    assert api_client.post(ADMIN, json=body, headers=unique_user.token).status_code == 403
    assert api_client.get(ADMIN, headers=unique_user.token).status_code == 403
    assert api_client.delete(f"{ADMIN}/{h2_user.user_id}", headers=unique_user.token).status_code == 403


def test_the_linked_account_lives_in_the_chosen_household(
    api_client: TestClient, admin_token, unique_user: TestUser, h2_user: TestUser, make_link
):
    account = make_link(h2_user.household_id)
    user = api_client.get(api_routes.admin_users_item_id(account["userId"]), headers=admin_token).json()
    assert user["householdId"] == str(h2_user.household_id) == account["householdId"]
    assert user["fullName"].startswith(f"{unique_user.full_name} (") and user["fullName"].endswith(")")
    assert user["email"].endswith(".invalid")


def test_the_linked_account_copies_permissions_and_allergies(
    api_client: TestClient, admin_token, unique_user: TestUser, h2_user: TestUser, make_link
):
    primary = api_client.get(api_routes.admin_users_item_id(unique_user.user_id), headers=admin_token).json()
    flags = ("canInvite", "canManage", "canManageHousehold", "canOrganize")
    session = unique_user.repos.session
    session.add(KhUserAllergies(session=session, user_id=unique_user.user_id, allergens=["gluten"]))
    session.commit()
    try:
        account = make_link(h2_user.household_id)
        copy = api_client.get(api_routes.admin_users_item_id(account["userId"]), headers=admin_token).json()
        assert {name: copy[name] for name in flags} == {name: primary[name] for name in flags}
        assert copy["admin"] == primary["admin"]
        row = session.execute(sa.select(KhUserAllergies).where(KhUserAllergies.user_id == UUID(account["userId"])))
        assert row.scalar_one().allergens == ["gluten"]
    finally:
        session.execute(sa.delete(KhUserAllergies).where(KhUserAllergies.user_id == unique_user.user_id))
        session.commit()


def test_rejected_links(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, third_household: UUID, make_link
):
    make_link(unique_user.household_id, expect=400)  # the person already is in this household
    account = make_link(h2_user.household_id)
    make_link(h2_user.household_id, expect=400)  # twice
    make_link(third_household, user_id=UUID(account["userId"]), expect=400)  # a linked account is no primary


def test_switching_both_ways(api_client: TestClient, unique_user: TestUser, h2_user: TestUser, make_link):
    account = make_link(h2_user.household_id)
    there = switch(api_client, unique_user.token, account["userId"])
    assert there.status_code == 200
    token_b = bearer(there.json()["access_token"])
    me = api_client.get(api_routes.users_self, headers=token_b).json()
    assert me["id"] == account["userId"] and me["householdId"] == str(h2_user.household_id)

    back = switch(api_client, token_b, unique_user.user_id)
    assert back.status_code == 200
    me = api_client.get(api_routes.users_self, headers=bearer(back.json()["access_token"])).json()
    assert me["id"] == str(unique_user.user_id) and me["householdId"] == str(unique_user.household_id)


def test_the_list_marks_the_current_account(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, make_link
):
    assert api_client.get(LIST, headers=unique_user.token).json() == []
    account = make_link(h2_user.household_id)
    rows = api_client.get(LIST, headers=unique_user.token).json()
    assert {row["userId"]: row["current"] for row in rows} == {str(unique_user.user_id): True, account["userId"]: False}
    token_b = bearer(switch(api_client, unique_user.token, account["userId"]).json()["access_token"])
    rows = api_client.get(LIST, headers=token_b).json()
    assert {row["userId"]: row["current"] for row in rows} == {str(unique_user.user_id): False, account["userId"]: True}


def test_a_foreign_account_is_404_and_an_api_token_is_400(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, make_link
):
    account = make_link(h2_user.household_id)
    assert switch(api_client, unique_user.token, h2_user.user_id).status_code == 404
    assert switch(api_client, h2_user.token, account["userId"]).status_code == 404
    api_token = api_client.post(api_routes.users_api_tokens, json={"name": "kh"}, headers=unique_user.token)
    assert switch(api_client, bearer(api_token.json()["token"]), account["userId"]).status_code == 400


def test_a_permission_taken_from_the_primary_is_gone_at_the_target(
    api_client: TestClient, admin_token, unique_user: TestUser, h2_user: TestUser, make_link
):
    primary = api_client.get(api_routes.admin_users_item_id(unique_user.user_id), headers=admin_token).json()
    account = make_link(h2_user.household_id)
    try:
        primary["canInvite"] = True
        api_client.put(api_routes.admin_users_item_id(unique_user.user_id), json=primary, headers=admin_token)
        token_b = bearer(switch(api_client, unique_user.token, account["userId"]).json()["access_token"])
        assert api_client.get(api_routes.users_self, headers=token_b).json()["canInvite"] is True

        primary["canInvite"] = False
        api_client.put(api_routes.admin_users_item_id(unique_user.user_id), json=primary, headers=admin_token)
        token_b = bearer(switch(api_client, unique_user.token, account["userId"]).json()["access_token"])
        assert api_client.get(api_routes.users_self, headers=token_b).json()["canInvite"] is False
    finally:
        primary["canInvite"] = False
        api_client.put(api_routes.admin_users_item_id(unique_user.user_id), json=primary, headers=admin_token)


def test_a_recipe_made_in_the_linked_account_belongs_to_that_household(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, make_link
):
    account = make_link(h2_user.household_id)
    token_b = bearer(switch(api_client, unique_user.token, account["userId"]).json()["access_token"])
    slug = api_client.post(api_routes.recipes, json={"name": utils.random_string()}, headers=token_b).json()
    recipe = api_client.get(api_routes.recipes_slug(slug), headers=token_b).json()
    assert recipe["householdId"] == str(h2_user.household_id)
    token_a = bearer(switch(api_client, token_b, unique_user.user_id).json()["access_token"])
    recipe = api_client.get(api_routes.recipes_slug(slug), headers=token_a).json()
    assert recipe["householdId"] != str(unique_user.household_id)
    api_client.delete(api_routes.recipes_slug(slug), headers=token_b)


def test_the_admin_sees_persons_and_unlinks(
    api_client: TestClient, admin_token, unique_user: TestUser, h2_user: TestUser, make_link
):
    account = make_link(h2_user.household_id)
    people = api_client.get(ADMIN, headers=admin_token).json()
    person = next(p for p in people if p["userId"] == str(unique_user.user_id))
    assert {a["userId"] for a in person["accounts"]} == {str(unique_user.user_id), account["userId"]}
    assert all(p["userId"] != account["userId"] for p in people)  # a linked account is no person of its own

    assert api_client.delete(f"{ADMIN}/{account['userId']}", headers=admin_token).status_code == 204
    assert api_client.get(api_routes.admin_users_item_id(account["userId"]), headers=admin_token).status_code == 200
    assert api_client.get(LIST, headers=unique_user.token).json() == []


def test_deleting_an_account_removes_its_link(
    api_client: TestClient, admin_token, unique_user: TestUser, h2_user: TestUser, make_link
):
    account = make_link(h2_user.household_id)
    api_client.delete(api_routes.admin_users_item_id(account["userId"]), headers=admin_token)
    session = unique_user.repos.session
    assert (
        session.execute(sa.select(KhAccountLink).where(KhAccountLink.user_id == UUID(account["userId"]))).first()
        is None
    )


def _rights(api_client: TestClient, admin_token, user_id: str | UUID) -> dict[str, bool]:
    body = api_client.get(api_routes.admin_users_item_id(user_id), headers=admin_token).json()
    return {key: body[key] for key in ("admin", "canInvite", "canManage", "canManageHousehold", "canOrganize")}


def test_a_right_changed_at_the_primary_reaches_linked_accounts_at_once(
    api_client: TestClient, admin_token, unique_user: TestUser, h2_user: TestUser, make_link
):
    primary = api_client.get(api_routes.admin_users_item_id(unique_user.user_id), headers=admin_token).json()
    account = make_link(h2_user.household_id)
    try:
        primary["canInvite"] = not primary["canInvite"]
        api_client.put(api_routes.admin_users_item_id(unique_user.user_id), json=primary, headers=admin_token)
        assert _rights(api_client, admin_token, account["userId"])["canInvite"] is primary["canInvite"]
    finally:
        primary["canInvite"] = not primary["canInvite"]
        api_client.put(api_routes.admin_users_item_id(unique_user.user_id), json=primary, headers=admin_token)


def test_unlinking_takes_every_right_from_the_account(
    api_client: TestClient, admin_token, unique_user: TestUser, h2_user: TestUser, make_link
):
    primary = api_client.get(api_routes.admin_users_item_id(unique_user.user_id), headers=admin_token).json()
    account = make_link(h2_user.household_id)
    try:
        primary["canOrganize"] = True
        api_client.put(api_routes.admin_users_item_id(unique_user.user_id), json=primary, headers=admin_token)
        assert _rights(api_client, admin_token, account["userId"])["canOrganize"] is True
        api_client.delete(f"{ADMIN}/{account['userId']}", headers=admin_token)
        assert not any(_rights(api_client, admin_token, account["userId"]).values())
    finally:
        primary["canOrganize"] = False
        api_client.put(api_routes.admin_users_item_id(unique_user.user_id), json=primary, headers=admin_token)


def test_a_deleted_primary_leaves_its_linked_accounts_without_rights(
    api_client: TestClient, admin_token, unique_user: TestUser, h2_user: TestUser, make_link
):
    from mealie.kh.accounts.service import delete_links

    account = make_link(h2_user.household_id)
    session = unique_user.repos.session
    session.execute(sa.update(User).where(User.id == UUID(account["userId"])).values(can_organize=True))
    session.commit()
    delete_links(session, unique_user.user_id)  # what deleting the primary does after the user row is gone
    session.expire_all()
    assert not any(_rights(api_client, admin_token, account["userId"]).values())
