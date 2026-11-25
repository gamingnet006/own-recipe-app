"""KH: tests for the tag proposals on recipes without tags and for the tags a draft's review keeps. No real AI."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from mealie.kh.ai.errors import QuotaUsedUpError
from mealie.kh.tags import service
from mealie.kh.tags.schemas import TagRef
from mealie.schema.recipe.recipe_organizers import TagSave
from tests.utils import api_routes, random_string
from tests.utils.fixture_schemas import TestUser

SUGGEST = "/api/kh/tags/suggest"
APPLY = "/api/kh/tags/apply"


def make_tag(user: TestUser, name: str) -> dict[str, Any]:
    tag = user.repos.tags.create(TagSave(name=f"{name}", group_id=user._group_id))
    return {"id": str(tag.id), "name": tag.name, "slug": tag.slug}


def make_recipe(api_client: TestClient, user: TestUser, *lines: str) -> dict[str, Any]:
    name = random_string()
    slug = api_client.post(api_routes.recipes, json={"name": name}, headers=user.token).json()
    body = {"recipeIngredient": [{"note": line} for line in lines]}
    return api_client.patch(api_routes.recipes_slug(slug), json=body, headers=user.token).json()


@pytest.fixture
def ai_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "ai_available", lambda _: False)


def test_proposals_use_only_existing_tags_and_nothing_is_saved(
    api_client: TestClient, unique_user: TestUser, ai_off: None
) -> None:
    for tag in unique_user.repos.tags.get_all():
        unique_user.repos.tags.delete(tag.id)
    vegan = make_tag(unique_user, "vegan")
    recipe = make_recipe(api_client, unique_user, "200 g Mehl", "Salz")
    other = make_recipe(api_client, unique_user, "200 g Hackfleisch")  # "mit Fleisch" does not exist: no proposal

    out = api_client.post(SUGGEST, json={}, headers=unique_user.token).json()
    mine = {p["slug"]: p for p in out["proposals"]}
    assert [t["id"] for t in mine[recipe["slug"]]["tags"]] == [vegan["id"]]
    assert other["slug"] not in mine
    assert out["aiAvailable"] is False
    assert out["withoutProposal"] >= 1
    got = api_client.get(api_routes.recipes_slug(recipe["slug"]), headers=unique_user.token).json()
    assert got["tags"] == []


def test_apply_adds_only_the_confirmed_tags_and_keeps_existing(
    api_client: TestClient, unique_user: TestUser, ai_off: None
) -> None:
    vegan = make_tag(unique_user, "vegetarisch")
    own = make_tag(unique_user, "Omas Rezepte")
    recipe = make_recipe(api_client, unique_user, "Mehl")
    api_client.patch(api_routes.recipes_slug(recipe["slug"]), json={"tags": [own]}, headers=unique_user.token)

    body = {"items": [{"recipeId": recipe["id"], "tagIds": [vegan["id"]]}]}
    assert api_client.post(APPLY, json=body, headers=unique_user.token).json() == {"changed": 1}
    got = api_client.get(api_routes.recipes_slug(recipe["slug"]), headers=unique_user.token).json()
    assert {t["name"] for t in got["tags"]} == {"vegetarisch", "Omas Rezepte"}

    bad = {"items": [{"recipeId": recipe["id"], "tagIds": [recipe["id"]]}]}  # not a tag of the group
    assert api_client.post(APPLY, json=bad, headers=unique_user.token).status_code == 404


def clear_tags(user: TestUser) -> None:
    for tag in user.repos.tags.get_all():
        user.repos.tags.delete(tag.id)


def fake_ai(monkeypatch: pytest.MonkeyPatch, answer: dict[str, Any]) -> list[str]:
    """An AI that answers with the TagRef of ANSWER; the list collects the slugs it was asked about."""
    asked: list[str] = []

    async def ask(repos: Any, translator: Any, found: Any) -> list[TagRef]:
        asked.append(found.slug)
        return [TagRef(**answer)]

    monkeypatch.setattr(service, "ai_available", lambda _: True)
    monkeypatch.setattr(service, "ai_tags", ask)
    return asked


def test_ai_is_asked_only_when_wanted_and_its_tags_join_the_rules(
    api_client: TestClient, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_tags(unique_user)
    soup = make_tag(unique_user, "Suppe")
    vegan = make_tag(unique_user, "vegan")
    recipe = make_recipe(api_client, unique_user, "Kürbis", "Salz")
    asked = fake_ai(monkeypatch, soup)
    api_client.post(SUGGEST, json={"useAi": False}, headers=unique_user.token)
    assert asked == []
    out = api_client.post(SUGGEST, json={"useAi": True}, headers=unique_user.token).json()
    assert recipe["slug"] in asked  # the rules gave a diet tag, and the AI is asked all the same
    mine = next(p for p in out["proposals"] if p["slug"] == recipe["slug"])
    assert {t["name"] for t in mine["tags"]} == {"Suppe", "vegan"}
    assert vegan["id"] in {t["id"] for t in mine["tags"]}
    assert recipe["id"] in out["askedIds"]


def test_recipes_already_asked_are_skipped_and_a_run_is_limited(
    api_client: TestClient, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_tags(unique_user)
    soup = make_tag(unique_user, "Suppe")
    for _ in range(service.MAX_AI_RECIPES + 3):
        make_recipe(api_client, unique_user, "Kürbis")
    asked = fake_ai(monkeypatch, soup)
    first = api_client.post(SUGGEST, json={"useAi": True}, headers=unique_user.token).json()
    assert len(first["askedIds"]) == service.MAX_AI_RECIPES
    assert first["aiLeft"] >= 3
    second = api_client.post(
        SUGGEST, json={"useAi": True, "skipIds": first["askedIds"]}, headers=unique_user.token
    ).json()
    assert not set(second["askedIds"]) & set(first["askedIds"])
    assert len(asked) == len(set(asked))  # nobody was asked twice


def failing_ai(monkeypatch: pytest.MonkeyPatch, error: Exception) -> list[str]:
    """An AI that always fails with ERROR; the list collects the slugs it was asked about."""
    asked: list[str] = []

    async def ask(repos: Any, translator: Any, found: Any) -> list[TagRef]:
        asked.append(found.slug)
        raise error

    monkeypatch.setattr(service, "ai_available", lambda _: True)
    monkeypatch.setattr(service, "ai_tags", ask)
    return asked


def test_a_used_up_quota_stops_asking_without_an_error(
    api_client: TestClient, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
) -> None:
    for _ in range(3):
        make_recipe(api_client, unique_user, "Kürbis")
    asked = failing_ai(monkeypatch, QuotaUsedUpError())
    response = api_client.post(SUGGEST, json={"useAi": True}, headers=unique_user.token)
    assert response.status_code == 200
    assert len(asked) == 1  # the quota is gone: no second request
    assert response.json()["aiAvailable"] is False


def test_an_unusable_answer_counts_as_asked_and_gives_no_error(
    api_client: TestClient, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
) -> None:
    recipe = make_recipe(api_client, unique_user, "Kürbis")
    failing_ai(monkeypatch, ValueError("answer does not fit the schema"))
    response = api_client.post(SUGGEST, json={"useAi": True}, headers=unique_user.token)
    assert response.status_code == 200
    assert recipe["id"] in response.json()["askedIds"]  # the page will not send it again


def test_apply_with_an_unknown_tag_changes_no_recipe(api_client: TestClient, unique_user: TestUser) -> None:
    clear_tags(unique_user)
    tag = make_tag(unique_user, "Suppe")
    first = make_recipe(api_client, unique_user, "Mehl")
    second = make_recipe(api_client, unique_user, "Mehl")
    body = {
        "items": [
            {"recipeId": first["id"], "tagIds": [tag["id"]]},
            {"recipeId": second["id"], "tagIds": [first["id"]]},  # not a tag
        ]
    }
    assert api_client.post(APPLY, json=body, headers=unique_user.token).status_code == 404
    got = api_client.get(api_routes.recipes_slug(first["slug"]), headers=unique_user.token).json()
    assert got["tags"] == []  # the valid first item was not saved either
