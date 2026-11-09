"""KH: "Ich vertrage nicht" and the warnings (D44): the profile round trip, warnings that name only members of the
viewer's own household, corrections that remove a warning, and the warnings map."""

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from tests.kh.nutrition.helpers import new_recipe
from tests.utils.fixture_schemas import TestUser

KH = "/api/kh"
SELF = f"{KH}/users/self/allergies"


def set_allergies(api_client: TestClient, user: TestUser, allergens: list[str]):
    return api_client.put(SELF, json={"allergens": allergens}, headers=user.token)


def report(api_client: TestClient, user: TestUser, slug: str) -> dict:
    return api_client.get(f"{KH}/recipes/{slug}/allergens", headers=user.token).json()


def nut_recipe(api_client: TestClient, user: TestUser) -> str:
    return new_recipe(api_client, user, [(100, "g", "Haselnüsse", ""), (1, "Prise", "Salz", "")])["slug"]


@pytest.fixture(autouse=True)
def empty_profiles(api_client: TestClient, unique_user: TestUser, household_member: TestUser, h2_user: TestUser):
    """The users live for the whole module: every test starts and ends with empty profiles."""
    for user in (unique_user, household_member, h2_user):
        set_allergies(api_client, user, [])
    yield
    for user in (unique_user, household_member, h2_user):
        set_allergies(api_client, user, [])


def test_profile_round_trip_and_bad_key(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(SELF, headers=unique_user.token).json() == {"allergens": []}
    put = set_allergies(api_client, unique_user, ["nuts", "gluten", "nuts"])
    assert put.status_code == 200 and put.json() == {"allergens": ["gluten", "nuts"]}  # spec order, no duplicates
    assert api_client.get(SELF, headers=unique_user.token).json() == {"allergens": ["gluten", "nuts"]}
    assert set_allergies(api_client, unique_user, ["zimt"]).status_code == 422
    assert api_client.get(SELF, headers=unique_user.token).json() == {"allergens": ["gluten", "nuts"]}


def test_member_allergic_to_nuts_makes_the_recipe_warn_with_their_name(
    api_client: TestClient, unique_user: TestUser, household_member: TestUser
):
    slug = nut_recipe(api_client, unique_user)
    assert report(api_client, unique_user, slug)["warnings"] == []
    set_allergies(api_client, household_member, ["nuts", "milk"])
    warnings = report(api_client, unique_user, slug)["warnings"]
    assert warnings == [{"allergen": "nuts", "names": [household_member.full_name]}]  # milk is not in the recipe


def test_a_member_of_another_household_is_not_named(
    api_client: TestClient, unique_user: TestUser, household_member: TestUser, h2_user: TestUser
):
    slug = nut_recipe(api_client, unique_user)
    set_allergies(api_client, h2_user, ["nuts"])
    assert report(api_client, unique_user, slug)["warnings"] == []
    set_allergies(api_client, household_member, ["nuts"])
    assert report(api_client, unique_user, slug)["warnings"][0]["names"] == [household_member.full_name]
    # the other household sees its own member, not ours
    assert report(api_client, h2_user, slug)["warnings"] == [{"allergen": "nuts", "names": [h2_user.full_name]}]


def test_a_correction_that_removes_the_allergen_removes_the_warning(
    api_client: TestClient, unique_user: TestUser, household_member: TestUser
):
    slug = nut_recipe(api_client, unique_user)
    set_allergies(api_client, household_member, ["nuts"])
    api_client.put(f"{KH}/recipes/{slug}/allergens/nuts", json={"present": False}, headers=unique_user.token)
    assert report(api_client, unique_user, slug)["warnings"] == []
    api_client.put(f"{KH}/recipes/{slug}/allergens/nuts", json={"present": None}, headers=unique_user.token)
    assert len(report(api_client, unique_user, slug)["warnings"]) == 1


def test_added_by_hand_allergen_warns(api_client: TestClient, unique_user: TestUser, household_member: TestUser):
    slug = new_recipe(api_client, unique_user, [(1, "Prise", "Salz", "")])["slug"]
    set_allergies(api_client, household_member, ["sesame"])
    api_client.put(f"{KH}/recipes/{slug}/allergens/sesame", json={"present": True}, headers=unique_user.token)
    assert report(api_client, unique_user, slug)["warnings"] == [
        {"allergen": "sesame", "names": [household_member.full_name]}
    ]


def test_warnings_map_holds_only_recipes_with_warnings(
    api_client: TestClient, unique_user: TestUser, household_member: TestUser, h2_user: TestUser
):
    nuts = nut_recipe(api_client, unique_user)
    plain = new_recipe(api_client, unique_user, [(1, "Prise", "Salz", "")])["slug"]
    other = new_recipe(api_client, h2_user, [(100, "g", "Haselnüsse", "")])["slug"]  # readable in the group
    assert api_client.get(f"{KH}/allergens/warnings", headers=unique_user.token).json() == {}

    set_allergies(api_client, household_member, ["nuts"])
    found = api_client.get(f"{KH}/allergens/warnings", headers=unique_user.token).json()
    assert found[nuts] == ["nuts"] and found[other] == ["nuts"] and plain not in found


def test_warnings_map_reads_the_corrections_in_one_query(api_client: TestClient, unique_user: TestUser):
    """Not one query per recipe (N+1) for the corrections."""
    for _ in range(3):
        new_recipe(api_client, unique_user, [(200, "ml", "Milch", "")])
    set_allergies(api_client, unique_user, ["milk"])
    seen: list[str] = []

    def count(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        if "FROM kh_recipe_allergen" in statement:
            seen.append(statement)

    sa.event.listen(sa.engine.Engine, "before_cursor_execute", count)
    try:
        response = api_client.get(f"{KH}/allergens/warnings", headers=unique_user.token)
    finally:
        sa.event.remove(sa.engine.Engine, "before_cursor_execute", count)
    assert len(response.json()) >= 3
    assert len(seen) == 1
