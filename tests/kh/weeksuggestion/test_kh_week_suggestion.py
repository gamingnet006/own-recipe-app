"""KH: tests for the week suggestion (D70): distinct recipes, never ones made lately, planned soon or excluded, the
cooked recipes first, favorites before the rest, the same seed gives the same answer."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from tests.kh.cooked.test_kh_cooked import make_event, make_recipe, set_last_made
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

ROUTE = "/api/kh/recipes/week-suggestion"


def suggest(api_client: TestClient, user: TestUser, query: str = "") -> list[str]:
    """The slugs the route suggests."""
    response = api_client.get(f"{ROUTE}?seed=1&{query}", headers=user.token)
    assert response.status_code == 200
    return [card["slug"] for card in response.json()]


def plan(api_client: TestClient, user: TestUser, recipe: dict, in_days: int) -> None:
    """A dinner entry for the recipe IN_DAYS days from today."""
    body = {
        "date": (datetime.now(UTC).date() + timedelta(days=in_days)).isoformat(),
        "entryType": "dinner",
        "recipeId": recipe["id"],
    }
    assert api_client.post(api_routes.households_mealplans, json=body, headers=user.token).status_code == 201


def test_returns_the_requested_number_of_distinct_recipes(api_client: TestClient, unique_user_fn_scoped: TestUser):
    for _ in range(5):
        make_recipe(api_client, unique_user_fn_scoped)
    slugs = suggest(api_client, unique_user_fn_scoped, "days=4")
    assert len(slugs) == 4 == len(set(slugs))


def test_skips_recent_planned_and_excluded_recipes(api_client: TestClient, unique_user_fn_scoped: TestUser):
    recent, planned, later, excluded, fine = (make_recipe(api_client, unique_user_fn_scoped) for _ in range(5))
    make_event(api_client, unique_user_fn_scoped, recent, 3)
    plan(api_client, unique_user_fn_scoped, planned, 10)
    plan(api_client, unique_user_fn_scoped, later, 30)
    slugs = suggest(api_client, unique_user_fn_scoped, f"days=31&exclude={excluded['id']}")
    assert recent["slug"] not in slugs and planned["slug"] not in slugs and excluded["slug"] not in slugs
    assert {later["slug"], fine["slug"]} <= set(slugs)


def test_cooked_recipes_come_before_never_made_ones(api_client: TestClient, unique_user_fn_scoped: TestUser):
    often, long_ago = make_recipe(api_client, unique_user_fn_scoped), make_recipe(api_client, unique_user_fn_scoped)
    for days in (20, 40):
        make_event(api_client, unique_user_fn_scoped, often, days)
    set_last_made(api_client, unique_user_fn_scoped, long_ago, 90)
    for _ in range(3):
        make_recipe(api_client, unique_user_fn_scoped)
    slugs = suggest(api_client, unique_user_fn_scoped, "days=31")
    assert slugs[:2] == [often["slug"], long_ago["slug"]]


def test_favorites_never_made_come_before_other_recipes(api_client: TestClient, unique_user_fn_scoped: TestUser):
    for _ in range(6):
        make_recipe(api_client, unique_user_fn_scoped)
    favorite = make_recipe(api_client, unique_user_fn_scoped)
    response = api_client.post(
        api_routes.users_id_favorites_slug(unique_user_fn_scoped.user_id, favorite["slug"]),
        headers=unique_user_fn_scoped.token,
    )
    assert response.status_code == 200
    assert suggest(api_client, unique_user_fn_scoped, "days=1") == [favorite["slug"]]


def test_same_seed_gives_the_same_answer(api_client: TestClient, unique_user_fn_scoped: TestUser):
    for _ in range(8):
        make_recipe(api_client, unique_user_fn_scoped)
    assert suggest(api_client, unique_user_fn_scoped, "days=5") == suggest(api_client, unique_user_fn_scoped, "days=5")


def test_other_groups_recipes_never_show(api_client: TestClient, unique_user_fn_scoped: TestUser, g2_user: TestUser):
    theirs = make_recipe(api_client, g2_user)
    assert theirs["slug"] not in suggest(api_client, unique_user_fn_scoped, "days=31")


def test_wished_recipes_come_first_oldest_wish_first(api_client: TestClient, unique_user_fn_scoped: TestUser):
    user = unique_user_fn_scoped
    for _ in range(4):
        recipe = make_recipe(api_client, user)
        make_event(api_client, user, recipe, 20)
        make_event(api_client, user, recipe, 30)
    first, second = make_recipe(api_client, user), make_recipe(api_client, user)
    for wished in (first, second):
        assert api_client.put(f"/api/kh/wishes/{wished['id']}", headers=user.token).status_code == 204
    assert suggest(api_client, user, "days=3")[:2] == [first["slug"], second["slug"]]
