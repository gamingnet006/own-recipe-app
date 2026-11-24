"""KH: a recognized draft gets the rule-based tags (only tags the group has), and approval saves the ones the review
kept. No real AI."""

from fastapi.testclient import TestClient

from mealie.schema.recipe.recipe_organizers import TagSave
from tests.kh.drafts.helpers import DRAFTS, get_draft, post_draft
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser


def make_tag(user: TestUser, name: str) -> dict:
    tag = user.repos.tags.create(TagSave(name=name, group_id=user._group_id))
    return {"id": str(tag.id), "name": tag.name, "slug": tag.slug}


def test_review_gets_rule_tags_and_approval_saves_the_kept_ones(
    api_client: TestClient, unique_user: TestUser, fake_ai
) -> None:
    for tag in unique_user.repos.tags.get_all():
        unique_user.repos.tags.delete(tag.id)
    vegetarian = make_tag(unique_user, "vegetarisch")
    fake_ai("recipe.json")  # flour, sugar, eggs, salt: vegetarian, not vegan
    draft_id = post_draft(api_client, unique_user, data={"text": "Testkuchen"}).json()["id"]
    draft = get_draft(api_client, unique_user, draft_id).json()
    assert [t["id"] for t in draft["recipe"]["tags"]] == [vegetarian["id"]]

    kept = api_client.post(f"{DRAFTS}/{draft_id}/approve", json={"tags": []}, headers=unique_user.token)
    slug = kept.json()["slug"]
    saved = api_client.get(api_routes.recipes_slug(slug), headers=unique_user.token).json()
    assert saved["tags"] == []  # the person removed the chip

    draft_id = post_draft(api_client, unique_user, data={"text": "Testkuchen 2"}).json()["id"]
    kept = api_client.post(f"{DRAFTS}/{draft_id}/approve", json={}, headers=unique_user.token)
    saved = api_client.get(api_routes.recipes_slug(kept.json()["slug"]), headers=unique_user.token).json()
    assert [t["name"] for t in saved["tags"]] == ["vegetarisch"]
