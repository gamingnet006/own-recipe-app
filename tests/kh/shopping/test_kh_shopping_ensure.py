"""KH: tests for the shopping page's ensure-food and ensure-unit routes (D60): a member without the permission to
organize can use them, an existing food or unit is reused, bad input and other groups' data are refused."""

from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient

from mealie.repos.all_repositories import get_repositories
from mealie.schema.recipe.recipe_ingredient import IngredientFoodSave
from tests.kh.addons.test_kh_addons import addons  # noqa: F401  the add-on switches of unique_user's household
from tests.utils.fixture_schemas import TestUser

FOOD = "/api/kh/shopping/ensure-food"
UNIT = "/api/kh/shopping/ensure-unit"


@pytest.fixture
def member(unique_user_fn_scoped: TestUser) -> Generator[TestUser]:
    """A user who may not organize; the premise is checked: Mealie's own food route refuses them."""
    repos = get_repositories(unique_user_fn_scoped.repos.session, group_id=None, household_id=None)
    repos.users.patch(unique_user_fn_scoped.user_id, {"can_organize": False})
    yield unique_user_fn_scoped


def make_label(user: TestUser, api_client: TestClient, name: str) -> str:
    """A label of the user's group, made with the group's own permissions."""
    return user.repos.group_multi_purpose_labels.create({"name": name, "group_id": user.group_id}).id.hex  # type: ignore[arg-type]


def test_the_premise_a_member_may_not_create_foods(api_client: TestClient, member: TestUser):
    assert api_client.post("/api/foods", json={"name": "Quark"}, headers=member.token).status_code == 403


def test_a_member_ensures_a_food_and_a_unit(api_client: TestClient, member: TestUser):
    food = api_client.post(FOOD, json={"name": "  Brot "}, headers=member.token)
    assert (food.status_code, food.json()["name"]) == (200, "Brot")
    unit = api_client.post(UNIT, json={"abbreviation": "kg"}, headers=member.token)
    assert (unit.status_code, unit.json()["name"], unit.json()["abbreviation"]) == (200, "Kilogramm", "kg")


def test_an_existing_food_is_reused_whatever_the_case_or_number(api_client: TestClient, member: TestUser):
    member.repos.ingredient_foods.create(IngredientFoodSave(name="Zwiebel", group_id=member.group_id))
    first = api_client.post(FOOD, json={"name": "zwiebel"}, headers=member.token).json()
    again = api_client.post(FOOD, json={"name": "Zwiebeln"}, headers=member.token).json()
    assert first["id"] == again["id"]
    assert first["name"] == "Zwiebel"


def test_a_new_food_gets_the_label_once_and_is_then_reused(api_client: TestClient, member: TestUser):
    label = make_label(member, api_client, "Backwaren")
    first = api_client.post(FOOD, json={"name": "Toast", "labelId": label}, headers=member.token).json()
    assert first["labelId"].replace("-", "") == label
    assert api_client.post(FOOD, json={"name": "TOAST"}, headers=member.token).json()["id"] == first["id"]


def test_an_existing_unit_is_reused_by_abbreviation_or_name(api_client: TestClient, member: TestUser):
    first = api_client.post(UNIT, json={"abbreviation": "l"}, headers=member.token).json()
    assert api_client.post(UNIT, json={"abbreviation": "l"}, headers=member.token).json()["id"] == first["id"]


def test_a_label_of_another_group_is_refused(api_client: TestClient, member: TestUser, g2_user: TestUser):
    foreign = make_label(g2_user, api_client, "Fremd")
    assert api_client.post(FOOD, json={"name": "Quark", "labelId": foreign}, headers=member.token).status_code == 422


@pytest.mark.parametrize("name", ["", "   ", "x" * 61])
def test_a_name_must_be_one_to_sixty_characters(api_client: TestClient, member: TestUser, name: str):
    assert api_client.post(FOOD, json={"name": name}, headers=member.token).status_code == 422


@pytest.mark.parametrize("abbreviation", ["EL", "kg ", "mg", ""])
def test_only_the_four_standard_units_are_made(api_client: TestClient, member: TestUser, abbreviation: str):
    assert api_client.post(UNIT, json={"abbreviation": abbreviation}, headers=member.token).status_code == 422


def test_another_groups_food_is_never_returned(api_client: TestClient, member: TestUser, g2_user: TestUser):
    other = g2_user.repos.ingredient_foods.create(IngredientFoodSave(name="Sauerkraut", group_id=g2_user.group_id))
    mine = api_client.post(FOOD, json={"name": "Sauerkraut"}, headers=member.token).json()
    assert mine["id"] != str(other.id)
    assert member.repos.ingredient_foods.get_one(mine["id"]) is not None


def test_both_routes_are_refused_while_the_shopping_list_is_off(
    api_client: TestClient,
    unique_user: TestUser,
    addons: Callable[..., None],  # noqa: F811
):
    addons(shopping=False)
    assert api_client.post(FOOD, json={"name": "Brot"}, headers=unique_user.token).status_code == 403
    assert api_client.post(UNIT, json={"abbreviation": "g"}, headers=unique_user.token).status_code == 403
