"""KH: tests for the household wish list (D72): wishing and taking back, several people, other households never
see wishes, planning (through the wish route or Mealie's own) ends a wish, past entries do not, the planner add-on
guards the routes, and a deleted user's wishes go."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.addons.models import KhHouseholdAddons
from mealie.kh.addons.schemas import AddonFlags
from mealie.kh.addons.service import save_flags
from tests.kh.cooked.test_kh_cooked import make_recipe
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

WISHES = "/api/kh/wishes"


def wishes_of(api_client: TestClient, user: TestUser, recipe: dict) -> list[dict]:
    """The open wishes of the user's household for this recipe (a list of zero or one groups)."""
    response = api_client.get(WISHES, headers=user.token)
    assert response.status_code == 200
    return [wish for wish in response.json() if wish["recipe"]["id"] == recipe["id"]]


def wish(api_client: TestClient, user: TestUser, recipe: dict) -> None:
    """The user wishes the recipe."""
    assert api_client.put(f"{WISHES}/{recipe['id']}", headers=user.token).status_code == 204


def day(offset: int) -> str:
    """The date OFFSET days from today, as the API takes it."""
    return (datetime.now(UTC).date() + timedelta(days=offset)).isoformat()


@pytest.fixture
def planner_off(unique_user: TestUser) -> Generator[None]:
    """The planner add-on off for the household of UNIQUE_USER during one test."""
    session = unique_user.repos.session
    save_flags(session, unique_user.household_id, AddonFlags(planner=False))
    yield
    session.execute(sa.delete(KhHouseholdAddons).where(KhHouseholdAddons.household_id == unique_user.household_id))
    session.commit()


def test_wish_and_take_it_back(api_client: TestClient, unique_user: TestUser):
    recipe = make_recipe(api_client, unique_user)
    wish(api_client, unique_user, recipe)
    wish(api_client, unique_user, recipe)  # twice is still one wish
    [open_wish] = wishes_of(api_client, unique_user, recipe)
    assert [person["id"] for person in open_wish["people"]] == [str(unique_user.user_id)]
    assert open_wish["recipe"]["slug"] == recipe["slug"]
    assert api_client.delete(f"{WISHES}/{recipe['id']}", headers=unique_user.token).status_code == 204
    assert wishes_of(api_client, unique_user, recipe) == []


def test_two_people_wish_one_recipe_and_each_takes_back_only_their_own(
    api_client: TestClient, user_tuple: list[TestUser]
):
    anna, opa = user_tuple
    recipe = make_recipe(api_client, anna)
    wish(api_client, anna, recipe)
    wish(api_client, opa, recipe)
    [open_wish] = wishes_of(api_client, anna, recipe)
    assert {person["id"] for person in open_wish["people"]} == {str(anna.user_id), str(opa.user_id)}
    api_client.delete(f"{WISHES}/{recipe['id']}", headers=anna.token)
    [open_wish] = wishes_of(api_client, opa, recipe)
    assert [person["id"] for person in open_wish["people"]] == [str(opa.user_id)]


def test_the_longest_wished_recipe_comes_first(api_client: TestClient, unique_user: TestUser):
    first, second = make_recipe(api_client, unique_user), make_recipe(api_client, unique_user)
    wish(api_client, unique_user, first)
    wish(api_client, unique_user, second)
    ids = [w["recipe"]["id"] for w in api_client.get(WISHES, headers=unique_user.token).json()]
    assert ids.index(first["id"]) < ids.index(second["id"])


def test_another_household_does_not_see_the_wish(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    recipe = make_recipe(api_client, unique_user)
    wish(api_client, unique_user, recipe)
    assert wishes_of(api_client, h2_user, recipe) == []


def test_planning_through_the_wish_route_ends_the_wish_for_everybody(
    api_client: TestClient, user_tuple: list[TestUser]
):
    anna, opa = user_tuple
    recipe = make_recipe(api_client, anna)
    wish(api_client, anna, recipe)
    wish(api_client, opa, recipe)
    response = api_client.post(f"{WISHES}/{recipe['id']}/plan", json={"date": day(2)}, headers=opa.token)
    assert response.status_code == 201
    assert (response.json()["entryType"], response.json()["recipe"]["slug"]) == ("dinner", recipe["slug"])
    assert wishes_of(api_client, anna, recipe) == [] == wishes_of(api_client, opa, recipe)


def test_planning_through_mealies_own_route_ends_the_wish_when_listed(api_client: TestClient, unique_user: TestUser):
    recipe = make_recipe(api_client, unique_user)
    wish(api_client, unique_user, recipe)
    body = {"date": day(0), "entryType": "lunch", "recipeId": recipe["id"]}
    assert api_client.post(api_routes.households_mealplans, json=body, headers=unique_user.token).status_code == 201
    assert wishes_of(api_client, unique_user, recipe) == []


def test_a_past_entry_does_not_fulfil_a_wish(api_client: TestClient, unique_user: TestUser):
    recipe = make_recipe(api_client, unique_user)
    wish(api_client, unique_user, recipe)
    body = {"date": day(-3), "entryType": "dinner", "recipeId": recipe["id"]}
    assert api_client.post(api_routes.households_mealplans, json=body, headers=unique_user.token).status_code == 201
    assert len(wishes_of(api_client, unique_user, recipe)) == 1


def test_a_recipe_of_another_group_cannot_be_wished(api_client: TestClient, unique_user: TestUser, g2_user: TestUser):
    theirs = make_recipe(api_client, g2_user)
    assert api_client.put(f"{WISHES}/{theirs['id']}", headers=unique_user.token).status_code == 404
    body = {"date": day(1)}
    assert api_client.post(f"{WISHES}/{theirs['id']}/plan", json=body, headers=unique_user.token).status_code == 404


def test_the_routes_answer_403_while_the_planner_is_off(api_client: TestClient, unique_user: TestUser, planner_off):
    recipe_id = "00000000-0000-0000-0000-000000000000"
    assert api_client.get(WISHES, headers=unique_user.token).status_code == 403
    assert api_client.put(f"{WISHES}/{recipe_id}", headers=unique_user.token).status_code == 403
    assert api_client.delete(f"{WISHES}/{recipe_id}", headers=unique_user.token).status_code == 403
    assert (
        api_client.post(f"{WISHES}/{recipe_id}/plan", json={"date": day(1)}, headers=unique_user.token).status_code
        == 403
    )


def test_the_wishes_of_a_deleted_user_or_recipe_no_longer_show(
    api_client: TestClient, user_tuple: list[TestUser], admin_token: dict
):
    anna, opa = user_tuple
    gone_recipe, kept = make_recipe(api_client, anna), make_recipe(api_client, anna)
    wish(api_client, anna, gone_recipe)
    wish(api_client, opa, kept)
    wish(api_client, anna, kept)
    assert api_client.delete(api_routes.recipes_slug(gone_recipe["slug"]), headers=anna.token).status_code == 200
    assert api_client.delete(api_routes.admin_users_item_id(opa.user_id), headers=admin_token).status_code == 200
    assert wishes_of(api_client, anna, gone_recipe) == []
    [open_wish] = wishes_of(api_client, anna, kept)
    assert [person["id"] for person in open_wish["people"]] == [str(anna.user_id)]
