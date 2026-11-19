"""KH: tests for the start page's cooked rows (D67): made events are counted in the last year, the "often" row needs
two, the "long ago" row follows the household's last-made date, other groups' recipes never show."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser

COOKED = "/api/kh/recipes/cooked"


def make_recipe(api_client: TestClient, user: TestUser) -> dict:
    """A new recipe with a random name, as the API returns it."""
    slug = api_client.post(api_routes.recipes, json={"name": random_string()}, headers=user.token).json()
    return api_client.get(api_routes.recipes_slug(slug), headers=user.token).json()


def make_event(
    api_client: TestClient, user: TestUser, recipe: dict, days_ago: int, subject: str = "Anna made this", kind="comment"
) -> None:
    """A timeline event on the recipe, DAYS_AGO days old."""
    when = (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()
    body = {"recipeId": recipe["id"], "subject": subject, "eventType": kind, "timestamp": when}
    assert api_client.post(api_routes.recipes_timeline_events, json=body, headers=user.token).status_code == 201


def set_last_made(api_client: TestClient, user: TestUser, recipe: dict, days_ago: int) -> None:
    """The household's last-made date of the recipe."""
    when = (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()
    response = api_client.patch(
        api_routes.recipes_slug_last_made(recipe["slug"]), json={"timestamp": when}, headers=user.token
    )
    assert response.status_code == 200


def rows(api_client: TestClient, user: TestUser) -> dict:
    """The answer of the route."""
    response = api_client.get(COOKED, headers=user.token)
    assert response.status_code == 200
    return response.json()


def test_often_counts_made_events_of_the_last_year_and_needs_two(api_client: TestClient, unique_user: TestUser):
    three, two, one, old = (make_recipe(api_client, unique_user) for _ in range(4))
    for days in (1, 5, 9):
        make_event(api_client, unique_user, three, days)
    make_event(api_client, unique_user, two, 2)
    make_event(api_client, unique_user, two, 40, "recipe.made-this-for-dinner|Anna", "info")
    make_event(api_client, unique_user, one, 3)
    make_event(api_client, unique_user, old, 400)
    make_event(api_client, unique_user, old, 500)
    often = rows(api_client, unique_user)["often"]
    assert [
        (card["slug"], card["count"]) for card in often if card["slug"] in {r["slug"] for r in (three, two, one, old)}
    ] == [
        (three["slug"], 3),
        (two["slug"], 2),
    ]


def test_other_timeline_events_are_not_made_events(api_client: TestClient, unique_user: TestUser):
    recipe = make_recipe(api_client, unique_user)
    make_event(api_client, unique_user, recipe, 1, "Tip: more salt")
    make_event(api_client, unique_user, recipe, 2, "Recipe created", "system")
    assert all(card["slug"] != recipe["slug"] for card in rows(api_client, unique_user)["often"])


def test_long_ago_lists_the_oldest_first_and_skips_recent_and_never_made(api_client: TestClient, unique_user: TestUser):
    old, older, recent, never = (make_recipe(api_client, unique_user) for _ in range(4))
    set_last_made(api_client, unique_user, old, 60)
    set_last_made(api_client, unique_user, older, 200)
    set_last_made(api_client, unique_user, recent, 5)
    long_ago = rows(api_client, unique_user)["longAgo"]
    mine = [card["slug"] for card in long_ago if card["slug"] in {r["slug"] for r in (old, older, recent, never)}]
    assert mine == [older["slug"], old["slug"]]
    assert long_ago[-1]["lastMade"] is not None


def test_each_row_has_at_most_eight_cards(api_client: TestClient, unique_user: TestUser):
    for _ in range(9):
        recipe = make_recipe(api_client, unique_user)
        make_event(api_client, unique_user, recipe, 1)
        make_event(api_client, unique_user, recipe, 2)
        set_last_made(api_client, unique_user, recipe, 90)
    answer = rows(api_client, unique_user)
    assert (len(answer["often"]), len(answer["longAgo"])) == (8, 8)


def test_another_groups_recipes_never_show(api_client: TestClient, unique_user: TestUser, g2_user: TestUser):
    recipe = make_recipe(api_client, g2_user)
    make_event(api_client, g2_user, recipe, 1)
    make_event(api_client, g2_user, recipe, 2)
    set_last_made(api_client, g2_user, recipe, 90)
    answer = rows(api_client, unique_user)
    assert all(card["slug"] != recipe["slug"] for card in answer["often"] + answer["longAgo"])


def test_a_login_is_needed(api_client: TestClient):
    assert api_client.get(COOKED).status_code == 401
