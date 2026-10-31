"""KH: tests for the duplicate check (phase 2, task 4): links compare after cleaning, titles by their words,
ingredients by their names; a draft only gets hints, and approving asks again only for new ones."""

from fastapi.testclient import TestClient

from mealie.kh.drafts.duplicates import (
    Candidate,
    find_duplicates,
    ingredient_names,
    normalize_url,
    title_similarity,
)
from mealie.kh.features.settings import KhSettings
from tests.kh.drafts.helpers import DRAFTS, get_draft, post_draft
from tests.utils.fixture_schemas import TestUser

LINK = "https://example.org/testkuchen"
TEXT = "Testkuchen: 200 g Mehl, 100 g Zucker, 3 Eier, 1 Prise Salz. 30 Minuten backen."
CAKE = ["250 g Mehl", "150 g Zucker", "3 Eier", "1 Zitrone", "1 Päckchen Backpulver"]


def recipe(name: str, ingredients: list[str]) -> dict:
    """A recognized recipe as a draft stores it."""
    return {"name": name, "recipeIngredient": [{"note": note} for note in ingredients]}


def candidate(name: str, ingredients: list[str], url: str | None = None) -> Candidate:
    """An existing recipe to compare against."""
    return Candidate(
        kind="recipe",
        name=name,
        url=normalize_url(url) if url else None,
        ingredients=ingredient_names(recipe(name, ingredients)),
        recipe_slug=name.lower().replace(" ", "-"),
        draft_id=None,
    )


def test_normalize_url():
    assert (
        normalize_url("HTTP://www.Example.org/rezept/testkuchen/?utm_source=x&b=2&a=1#oben")
        == "https://example.org/rezept/testkuchen?a=1&b=2"
    )
    assert normalize_url("https://www.instagram.com/p/ABC123/?igsh=xyz") == "https://instagram.com/p/ABC123"
    assert normalize_url("https://example.org/a?fbclid=1&gclid=2&si=3&ref=4") == "https://example.org/a"


def test_title_similarity():
    assert title_similarity("Omas Apfelkuchen", "Apfelkuchen nach Oma") >= 0.85
    assert title_similarity("Apfel-Kuchen!", "apfel kuchen") >= 0.85
    assert title_similarity("Apfelkuchen", "Linsensuppe") < 0.5
    assert title_similarity("", "") == 0.0  # two untitled drafts are no hint


def test_ingredient_names():
    notes = recipe("x", ["200 g Mehl", "3 Eier", "1 Prise Salz"])
    assert ingredient_names(notes) == {"mehl", "eier", "salz"}
    parsed = {"recipeIngredient": [{"food": {"name": "Butter"}, "note": "weich"}]}
    assert ingredient_names(parsed) == {"butter"}


def test_find_duplicates_kinds():
    draft = recipe("Zitronenkuchen", CAKE)
    candidates = [
        candidate("Etwas ganz anderes", ["1 Brot"], url="https://www.example.org/zitronenkuchen/"),
        candidate("Zitronenkuchen von Oma", ["1 Brot"]),
        candidate("Zitronen-Kuchen", CAKE),  # the same recipe written apart: its ingredients give it away
    ]
    warnings = find_duplicates(draft, "https://example.org/zitronenkuchen?utm_medium=x", candidates, KhSettings())
    assert [w.kind for w in warnings] == ["duplicate_link", "similar_title", "similar_ingredients"]
    assert warnings[0].recipe_slug == "etwas-ganz-anderes"


def test_same_ingredients_other_dish_is_no_duplicate():
    batter = ["250 g Mehl", "2 Eier", "500 ml Milch", "1 Prise Salz", "50 g Butter"]
    assert find_duplicates(recipe("Pfannkuchen", batter), None, [candidate("Waffeln", batter)], KhSettings()) == []


def test_second_draft_with_same_link_warns(api_client: TestClient, unique_user: TestUser, fake_page, fake_ai):
    fake_page("page.html")
    fake_ai("recipe.json")
    first = post_draft(api_client, unique_user, data={"url": LINK}).json()["id"]
    second = post_draft(api_client, unique_user, data={"url": f"{LINK}/?utm_source=chat"}).json()["id"]
    warnings = get_draft(api_client, unique_user, second).json()["warnings"]
    assert {"kind": "duplicate_link", "draftId": first} in [
        {"kind": w["kind"], "draftId": w["draftId"]} for w in warnings
    ]


def test_approve_with_new_duplicate_needs_force(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    waiting = post_draft(api_client, unique_user, data={"text": TEXT}).json()["id"]
    other = post_draft(api_client, unique_user, data={"text": TEXT}).json()["id"]
    assert api_client.post(f"{DRAFTS}/{other}/approve", json={}, headers=unique_user.token).status_code == 200

    # The other one is a recipe now, which the waiting draft's warnings from recognizing do not know yet
    response = api_client.post(f"{DRAFTS}/{waiting}/approve", json={}, headers=unique_user.token)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "duplicates"
    assert [w["kind"] for w in response.json()["detail"]["warnings"]] == ["similar_title"]
    assert response.json()["detail"]["warnings"][0]["recipeSlug"]

    forced = api_client.post(f"{DRAFTS}/{waiting}/approve", json={"force": True}, headers=unique_user.token)
    assert forced.status_code == 200
