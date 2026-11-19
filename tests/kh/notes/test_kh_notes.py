"""KH: tests for the family note on a recipe (D82): a household shares one note, another household never sees it,
the length limit, empty text and DELETE remove it, and a recipe of another group is a 404."""

from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.notes import service
from mealie.kh.notes.models import KhRecipeNote
from tests.kh.nutrition.helpers import new_recipe
from tests.utils import api_routes, random_string
from tests.utils.fixture_schemas import TestUser


def url(recipe: dict) -> str:
    return f"/api/kh/recipes/{recipe['id']}/note"


def test_a_household_shares_one_note(api_client: TestClient, unique_user: TestUser, household_member: TestUser):
    recipe = new_recipe(api_client, unique_user, [])
    assert api_client.get(url(recipe), headers=unique_user.token).json() is None
    answer = api_client.put(url(recipe), json={"text": "  Weniger Zucker  "}, headers=unique_user.token)
    assert answer.status_code == 200 and answer.json()["text"] == "Weniger Zucker"
    seen = api_client.get(url(recipe), headers=household_member.token).json()
    assert seen["text"] == "Weniger Zucker" and seen["updatedBy"] == str(unique_user.user_id)
    # the other person changes the same note
    api_client.put(url(recipe), json={"text": "Kinder mögen es so"}, headers=household_member.token)
    changed = api_client.get(url(recipe), headers=unique_user.token).json()
    assert changed["text"] == "Kinder mögen es so" and changed["updatedBy"] == str(household_member.user_id)


def test_another_households_note_is_invisible(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, g2_user: TestUser
):
    recipe = new_recipe(api_client, unique_user, [])
    api_client.put(url(recipe), json={"text": "unsere"}, headers=unique_user.token)
    # the other household of the group sees the recipe but not our note, and keeps its own
    assert api_client.get(url(recipe), headers=h2_user.token).json() is None
    api_client.put(url(recipe), json={"text": "eure"}, headers=h2_user.token)
    assert api_client.get(url(recipe), headers=unique_user.token).json()["text"] == "unsere"
    # a user of another group cannot even find the recipe
    assert api_client.get(url(recipe), headers=g2_user.token).status_code == 404
    assert api_client.put(url(recipe), json={"text": "x"}, headers=g2_user.token).status_code == 404


def test_length_limit_empty_text_and_delete(api_client: TestClient, unique_user: TestUser):
    recipe = new_recipe(api_client, unique_user, [])
    assert api_client.put(url(recipe), json={"text": "x" * 2001}, headers=unique_user.token).status_code == 422
    assert api_client.put(url(recipe), json={"text": "x" * 2000}, headers=unique_user.token).status_code == 200
    assert api_client.put(url(recipe), json={"text": "  "}, headers=unique_user.token).json() is None
    assert api_client.get(url(recipe), headers=unique_user.token).json() is None
    api_client.put(url(recipe), json={"text": "wieder da"}, headers=unique_user.token)
    assert api_client.delete(url(recipe), headers=unique_user.token).status_code == 204
    assert api_client.get(url(recipe), headers=unique_user.token).json() is None
    assert api_client.delete(url(recipe), headers=unique_user.token).status_code == 204  # nothing to delete is fine


def test_unknown_recipe_and_no_sign_in(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(f"/api/kh/recipes/{uuid4()}/note", headers=unique_user.token).status_code == 404
    assert api_client.get(f"/api/kh/recipes/{uuid4()}/note").status_code == 401


def note_count(user: TestUser, **where) -> int:
    session = user.repos.session
    session.expire_all()
    query = sa.select(sa.func.count()).select_from(KhRecipeNote)
    for column, value in where.items():
        query = query.where(getattr(KhRecipeNote, column) == value)
    return session.scalar(query) or 0


def test_deleting_a_recipe_deletes_its_notes(api_client: TestClient, unique_user: TestUser):
    recipe = new_recipe(api_client, unique_user, [])
    api_client.put(url(recipe), json={"text": "weg damit"}, headers=unique_user.token)
    assert note_count(unique_user, recipe_id=UUID(recipe["id"])) == 1
    assert api_client.delete(api_routes.recipes_slug(recipe["slug"]), headers=unique_user.token).status_code == 200
    assert note_count(unique_user, recipe_id=UUID(recipe["id"])) == 0


def test_deleting_a_household_deletes_its_notes(api_client: TestClient, admin_token, unique_user: TestUser):
    group = api_client.get(api_routes.groups_self, headers=unique_user.token).json()
    created = api_client.post(
        api_routes.admin_households, json={"name": random_string(12), "groupId": group["id"]}, headers=admin_token
    )
    household_id = UUID(created.json()["id"])
    recipe = new_recipe(api_client, unique_user, [])
    session = unique_user.repos.session
    session.add(
        KhRecipeNote(
            session=session,
            group_id=unique_user.group_id,
            household_id=household_id,
            recipe_id=UUID(recipe["id"]),
            text="euer Haushalt",
            updated_by=unique_user.user_id,
        )
    )
    session.commit()
    assert note_count(unique_user, household_id=household_id) == 1
    assert api_client.delete(api_routes.admin_households_item_id(household_id), headers=admin_token).status_code == 200
    assert note_count(unique_user, household_id=household_id) == 0


def test_a_note_whose_author_is_gone_still_shows(
    api_client: TestClient, admin_token, unique_user: TestUser, h2_user: TestUser
):
    recipe = new_recipe(api_client, unique_user, [])
    api_client.put(url(recipe), json={"text": "bleibt"}, headers=h2_user.token)
    session = unique_user.repos.session
    session.execute(sa.update(KhRecipeNote).where(KhRecipeNote.recipe_id == UUID(recipe["id"])).values(updated_by=None))
    session.commit()
    seen = api_client.get(url(recipe), headers=h2_user.token).json()
    assert seen["text"] == "bleibt" and seen["updatedBy"] is None and seen["updatedByName"] == ""


def test_two_first_saves_at_once_end_as_an_update(
    api_client: TestClient, unique_user: TestUser, household_member: TestUser, monkeypatch: pytest.MonkeyPatch
):
    recipe = new_recipe(api_client, unique_user, [])
    session = unique_user.repos.session
    group, household, recipe_id = unique_user.group_id, unique_user._household_id, UUID(recipe["id"])
    service.set_note(session, group, household, unique_user.user_id, recipe_id, "erste")
    # the second request looked before the first one stored: its first look finds nothing
    real = service._row
    looks: list[int] = []

    def blind_first_time(*args):
        looks.append(1)
        return None if len(looks) == 1 else real(*args)

    monkeypatch.setattr(service, "_row", blind_first_time)
    answer = service.set_note(session, group, household, household_member.user_id, recipe_id, "zweite")
    assert answer is not None and answer.text == "zweite" and answer.updated_by == household_member.user_id
    assert note_count(unique_user, recipe_id=recipe_id) == 1
