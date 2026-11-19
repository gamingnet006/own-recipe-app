"""KH: tests for "always in the house" (D65): a member without the permission to organize sets and clears it for
the household only, a food of another group is 404, the add-on switch is respected, and Mealie's own reading of the
state (the households a food is on hand for) shows the change."""

from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient

from mealie.repos.all_repositories import get_repositories
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.schema.recipe.recipe_ingredient import IngredientFoodSave, RecipeIngredient
from tests import utils
from tests.kh.addons.test_kh_addons import addons  # noqa: F401  the add-on switches of unique_user's household
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

ON_HAND = "/api/kh/shopping/on-hand"


@pytest.fixture
def member(unique_user_fn_scoped: TestUser) -> Generator[TestUser]:
    """A user who may not organize, so that Mealie's own food update would be refused."""
    repos = get_repositories(unique_user_fn_scoped.repos.session, group_id=None, household_id=None)
    repos.users.patch(unique_user_fn_scoped.user_id, {"can_organize": False})
    yield unique_user_fn_scoped


def make_food(user: TestUser, name: str) -> str:
    return str(user.repos.ingredient_foods.create(IngredientFoodSave(name=name, group_id=user.group_id)).id)


def households_of(api_client: TestClient, user: TestUser, food_id: str) -> list[str]:
    """The slugs of the households the food is on hand for, as Mealie's add-to-list dialog reads them."""
    return api_client.get(f"/api/foods/{food_id}", headers=user.token).json()["householdsWithIngredientFood"]


def household_slug(api_client: TestClient, user: TestUser) -> str:
    return api_client.get("/api/households/self", headers=user.token).json()["slug"]


def test_a_member_without_organize_sets_and_clears_it(api_client: TestClient, member: TestUser):
    food = make_food(member, "Salz")
    slug = household_slug(api_client, member)
    on = api_client.post(ON_HAND, json={"foodId": food, "onHand": True}, headers=member.token)
    assert (on.status_code, on.json()["householdsWithIngredientFood"]) == (200, [slug])
    assert households_of(api_client, member, food) == [slug]
    off = api_client.post(ON_HAND, json={"foodId": food, "onHand": False}, headers=member.token)
    assert (off.status_code, off.json()["householdsWithIngredientFood"]) == (200, [])
    assert households_of(api_client, member, food) == []


def test_setting_twice_is_harmless(api_client: TestClient, member: TestUser):
    food = make_food(member, "Pfeffer")
    for _ in range(2):
        assert api_client.post(ON_HAND, json={"foodId": food, "onHand": True}, headers=member.token).status_code == 200
    assert len(households_of(api_client, member, food)) == 1


def test_another_household_keeps_its_own_state(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    food = make_food(unique_user, "Mehl")
    mine = household_slug(api_client, unique_user)
    theirs = household_slug(api_client, h2_user)
    assert mine != theirs
    api_client.post(ON_HAND, json={"foodId": food, "onHand": True}, headers=h2_user.token)
    api_client.post(ON_HAND, json={"foodId": food, "onHand": True}, headers=unique_user.token)
    api_client.post(ON_HAND, json={"foodId": food, "onHand": False}, headers=unique_user.token)
    assert households_of(api_client, unique_user, food) == [theirs]


def test_a_food_of_another_group_is_404_and_unchanged(api_client: TestClient, unique_user: TestUser, g2_user: TestUser):
    foreign = make_food(g2_user, "Sauerkraut")
    assert (
        api_client.post(ON_HAND, json={"foodId": foreign, "onHand": True}, headers=unique_user.token).status_code == 404
    )
    assert households_of(api_client, g2_user, foreign) == []


def test_an_unknown_food_is_404(api_client: TestClient, unique_user: TestUser):
    unknown = "00000000-0000-4000-8000-000000000000"
    assert (
        api_client.post(ON_HAND, json={"foodId": unknown, "onHand": True}, headers=unique_user.token).status_code == 404
    )


def test_refused_while_the_shopping_list_is_off(
    api_client: TestClient,
    unique_user: TestUser,
    addons: Callable[..., None],  # noqa: F811
):
    food = make_food(unique_user, "Zucker")
    addons(shopping=False)
    assert api_client.post(ON_HAND, json={"foodId": food, "onHand": True}, headers=unique_user.token).status_code == 403


def test_mealies_add_recipe_to_list_leaves_out_what_was_set_here(api_client: TestClient, member: TestUser):
    """The household's state set by this route is what Mealie's whole-recipe add reads (it skips on-hand foods)."""
    foods = [
        member.repos.ingredient_foods.create(IngredientFoodSave(name=n, group_id=member.group_id))
        for n in ("Reis", "Linsen")
    ]
    ingredients = [RecipeIngredient(note=food.name, food=food, quantity=1) for food in foods]
    recipe = member.repos.recipes.create(
        RecipeDraft(
            name=utils.random_string(10),
            user_id=member.user_id,
            group_id=member.group_id,
            recipe_ingredient=ingredients,
        )
    )
    shopping_list = api_client.post(
        api_routes.households_shopping_lists, json={"name": "Rewe"}, headers=member.token
    ).json()
    api_client.post(ON_HAND, json={"foodId": str(foods[0].id), "onHand": True}, headers=member.token)
    added = api_client.post(
        api_routes.households_shopping_lists_item_id_recipe(shopping_list["id"]),
        json=[{"recipeId": str(recipe.id)}],
        headers=member.token,
    )
    assert added.status_code == 200
    items = api_client.get(
        api_routes.households_shopping_lists_item_id(shopping_list["id"]), headers=member.token
    ).json()
    assert [item["foodId"] for item in items["listItems"]] == [str(foods[1].id)]
