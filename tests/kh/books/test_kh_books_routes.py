"""KH: the book settings and recipe flags routes (D43): defaults, round trip, who may read and who may write, and
that a photo only stays on for a recipe marked as ours."""

from uuid import uuid4

from fastapi.testclient import TestClient

from tests.utils import api_routes, random_string
from tests.utils.fixture_schemas import TestUser

KH = "/api/kh"


def print_url(cookbook_id: str) -> str:
    return f"{KH}/cookbooks/{cookbook_id}/print"


def new_cookbook(api_client: TestClient, user: TestUser) -> str:
    """A fresh cookbook of the user's household; returns its ID."""
    response = api_client.post(api_routes.households_cookbooks, json={"name": random_string()}, headers=user.token)
    return response.json()["id"]


def new_recipe(api_client: TestClient, user: TestUser) -> str:
    """A fresh recipe of the user; returns its slug."""
    return api_client.post(api_routes.recipes, json={"name": random_string()}, headers=user.token).json()


def set_flag(api_client: TestClient, user: TestUser, slug: str, own_photo: bool = True):
    return api_client.put(f"{KH}/recipes/{slug}/flags", json={"ownPhoto": own_photo}, headers=user.token)


def test_defaults_when_nothing_is_stored(api_client: TestClient, unique_user: TestUser):
    body = api_client.get(print_url(new_cookbook(api_client, unique_user)), headers=unique_user.token).json()
    assert body == {
        "title": None,
        "subtitle": None,
        "titlePage": True,
        "toc": True,
        "order": "category",
        "description": True,
        "notes": True,
        "oven": True,
        "recipes": {},
    }


def test_put_then_get_round_trip(api_client: TestClient, unique_user: TestUser):
    cookbook = new_cookbook(api_client, unique_user)
    settings = {
        "title": "Unser Buch",
        "subtitle": "Familie · 2026",
        "titlePage": False,
        "toc": False,
        "order": "alpha",
        "description": False,
        "notes": False,
        "oven": False,
        "recipes": {"kuchen": {"include": False, "photo": False, "servings": 6}},
    }
    put = api_client.put(print_url(cookbook), json=settings, headers=unique_user.token)
    assert put.status_code == 200 and put.json() == settings
    assert api_client.get(print_url(cookbook), headers=unique_user.token).json() == settings
    again = api_client.put(print_url(cookbook), json={**settings, "title": "Neu"}, headers=unique_user.token)
    assert again.json()["title"] == "Neu"  # the second save replaces the first


def test_other_household_reads_but_cannot_write(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    cookbook = new_cookbook(api_client, unique_user)
    assert api_client.get(print_url(cookbook), headers=h2_user.token).status_code == 200
    denied = api_client.put(print_url(cookbook), json={"title": "Fremd"}, headers=h2_user.token)
    assert denied.status_code == 403
    assert denied.json()["detail"] == "Nur der eigene Haushalt kann diese Sammlung ändern"
    assert api_client.get(print_url(cookbook), headers=unique_user.token).json()["title"] is None


def test_cookbook_of_another_group_is_unknown(api_client: TestClient, unique_user: TestUser, g2_user: TestUser):
    cookbook = new_cookbook(api_client, g2_user)
    assert api_client.get(print_url(cookbook), headers=unique_user.token).status_code == 404
    assert api_client.put(print_url(cookbook), json={}, headers=unique_user.token).status_code == 404
    assert api_client.get(print_url(str(uuid4())), headers=unique_user.token).status_code == 404


def test_photo_stays_on_only_for_a_recipe_marked_as_ours(api_client: TestClient, unique_user: TestUser):
    cookbook, slug = new_cookbook(api_client, unique_user), new_recipe(api_client, unique_user)
    settings = {"recipes": {slug: {"photo": True}, "gibt-es-nicht": {"photo": True}}}
    stored = api_client.put(print_url(cookbook), json=settings, headers=unique_user.token).json()
    assert stored["recipes"][slug]["photo"] is False and stored["recipes"]["gibt-es-nicht"]["photo"] is False

    assert set_flag(api_client, unique_user, slug).json() == {"ownPhoto": True}
    stored = api_client.put(print_url(cookbook), json=settings, headers=unique_user.token).json()
    assert stored["recipes"][slug]["photo"] is True and stored["recipes"]["gibt-es-nicht"]["photo"] is False


def test_photo_is_off_on_reading_when_the_flag_was_removed_later(api_client: TestClient, unique_user: TestUser):
    cookbook, slug = new_cookbook(api_client, unique_user), new_recipe(api_client, unique_user)
    set_flag(api_client, unique_user, slug)
    api_client.put(print_url(cookbook), json={"recipes": {slug: {"photo": True}}}, headers=unique_user.token)
    set_flag(api_client, unique_user, slug, own_photo=False)
    read = api_client.get(print_url(cookbook), headers=unique_user.token).json()
    assert read["recipes"][slug]["photo"] is False


def test_invalid_settings_are_refused(api_client: TestClient, unique_user: TestUser):
    cookbook = new_cookbook(api_client, unique_user)
    for body in (
        {"title": "x" * 121},
        {"subtitle": "x" * 121},
        {"order": "random"},
        {"recipes": {"a": {"servings": 0}}},
    ):
        assert api_client.put(print_url(cookbook), json=body, headers=unique_user.token).status_code == 422
    assert api_client.put(print_url(cookbook), json={"title": "x" * 120}, headers=unique_user.token).status_code == 200


def test_flags_read_and_write(api_client: TestClient, unique_user: TestUser):
    a, b = new_recipe(api_client, unique_user), new_recipe(api_client, unique_user)
    set_flag(api_client, unique_user, a)
    found = api_client.get(f"{KH}/recipes/flags?slugs={a},{b},gibt-es-nicht", headers=unique_user.token).json()
    assert found == {a: {"ownPhoto": True}, b: {"ownPhoto": False}}
    set_flag(api_client, unique_user, a, own_photo=False)
    assert api_client.get(f"{KH}/recipes/flags?slugs={a}", headers=unique_user.token).json() == {a: {"ownPhoto": False}}
    assert api_client.get(f"{KH}/recipes/flags", headers=unique_user.token).json() == {}
    assert set_flag(api_client, unique_user, "gibt-es-nicht").status_code == 404


def test_flags_need_the_right_to_edit_the_recipe(
    api_client: TestClient, unique_user: TestUser, household_member: TestUser, g2_user: TestUser
):
    slug = new_recipe(api_client, unique_user)
    recipe = api_client.get(api_routes.recipes_slug(slug), headers=unique_user.token).json()
    recipe["settings"]["locked"] = True
    locked = api_client.put(api_routes.recipes_slug(slug), json=recipe, headers=unique_user.token)
    assert locked.status_code == 200
    assert set_flag(api_client, household_member, slug).status_code == 403
    assert set_flag(api_client, unique_user, slug).status_code == 200
    assert set_flag(api_client, g2_user, slug).status_code == 404  # another group never sees the recipe
