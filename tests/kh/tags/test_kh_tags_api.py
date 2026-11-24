"""KH: tests for the tag proposals on recipes without tags and for the tags a draft's review keeps. No real AI."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

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


def test_ai_is_asked_only_when_wanted_and_only_for_recipes_without_a_rule_result(
    api_client: TestClient, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
) -> None:
    for tag in unique_user.repos.tags.get_all():
        unique_user.repos.tags.delete(tag.id)
    soup = make_tag(unique_user, "Suppe")  # the only tag: no rule can match it
    recipe = make_recipe(api_client, unique_user, "Kürbis")
    asked: list[str] = []

    async def fake_ai(repos: Any, translator: Any, found: Any) -> list[TagRef]:
        asked.append(found.slug)
        return [TagRef(**soup)]

    monkeypatch.setattr(service, "ai_available", lambda _: True)
    monkeypatch.setattr(service, "ai_tags", fake_ai)
    api_client.post(SUGGEST, json={"useAi": False}, headers=unique_user.token)
    assert asked == []
    out = api_client.post(SUGGEST, json={"useAi": True}, headers=unique_user.token).json()
    assert recipe["slug"] in asked
    assert any(p["slug"] == recipe["slug"] and p["tags"][0]["name"] == "Suppe" for p in out["proposals"])
