"""KH: the duplicate report (D43): doubles inside one household, ignored pairs, the tag filter and the limit."""

from fastapi.testclient import TestClient

from tests.utils import api_routes, random_string
from tests.utils.fixture_schemas import TestUser

URL = "/api/kh/duplicates"
CAKE = ["250 g Mehl", "150 g Zucker", "3 Eier", "1 Zitrone", "1 Päckchen Backpulver"]
STEW = ["500 g Rindfleisch", "2 Zwiebeln", "3 Karotten", "1 Lorbeerblatt"]


def new_recipe(
    api_client: TestClient, user: TestUser, name: str, ingredients: list[str], tag: dict | None = None
) -> str:
    """A recipe of the user's household with these ingredient lines (and tag); returns its slug."""
    slug = api_client.post(api_routes.recipes, json={"name": name}, headers=user.token).json()
    recipe = api_client.get(api_routes.recipes_slug(slug), headers=user.token).json()
    recipe["recipeIngredient"] = [{"note": note, "referenceId": None} for note in ingredients]
    recipe["tags"] = [tag] if tag else []
    assert api_client.put(api_routes.recipes_slug(slug), json=recipe, headers=user.token).status_code == 200
    return slug


def new_tag(api_client: TestClient, user: TestUser) -> dict:
    return api_client.post(api_routes.organizers_tags, json={"name": random_string()}, headers=user.token).json()


def report(api_client: TestClient, user: TestUser, tag: str = "") -> list[dict]:
    return api_client.get(f"{URL}{tag}", headers=user.token).json()


def pair_of(slugs: list[str], pairs: list[dict]) -> list[dict]:
    """The pairs among PAIRS that are between two of SLUGS."""
    return [p for p in pairs if p["a"]["slug"] in slugs and p["b"]["slug"] in slugs]


def test_same_title_and_ingredients_make_a_pair(api_client: TestClient, unique_user: TestUser):
    name = f"Apfelkuchen {random_string()}"
    a, b = (new_recipe(api_client, unique_user, name, CAKE) for _ in range(2))
    found = pair_of([a, b], report(api_client, unique_user))
    assert len(found) == 1
    assert {found[0]["a"]["slug"], found[0]["b"]["slug"]} == {a, b}
    assert found[0]["kind"] == "similar_title" and found[0]["similarity"] > 0.9
    assert found[0]["a"].keys() == {"slug", "name", "orgUrl", "tags"}


def test_different_dishes_make_no_pair(api_client: TestClient, unique_user: TestUser):
    a = new_recipe(api_client, unique_user, f"Apfelkuchen {random_string()}", CAKE)
    b = new_recipe(api_client, unique_user, f"Gulasch {random_string()}", STEW)
    assert pair_of([a, b], report(api_client, unique_user)) == []


def test_other_households_and_groups_are_never_paired(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, g2_user: TestUser
):
    name = f"Apfelkuchen {random_string()}"
    mine = new_recipe(api_client, unique_user, name, CAKE)
    others = [new_recipe(api_client, other, name, CAKE) for other in (h2_user, g2_user)]
    assert pair_of([mine, *others], report(api_client, unique_user)) == []
    assert pair_of(others, report(api_client, h2_user)) == []


def test_ignored_pair_is_gone_in_either_order(api_client: TestClient, unique_user: TestUser):
    name = f"Apfelkuchen {random_string()}"
    a, b, c = (new_recipe(api_client, unique_user, name, CAKE) for _ in range(3))
    assert len(pair_of([a, b, c], report(api_client, unique_user))) == 3
    assert api_client.post(f"{URL}/ignore", json={"a": a, "b": b}, headers=unique_user.token).status_code == 204
    assert len(pair_of([a, b, c], report(api_client, unique_user))) == 2
    assert api_client.post(f"{URL}/ignore", json={"a": b, "b": a}, headers=unique_user.token).status_code == 204
    assert api_client.post(f"{URL}/ignore", json={"a": a, "b": c}, headers=unique_user.token).status_code == 204
    left = pair_of([a, b, c], report(api_client, unique_user))
    assert [{p["a"]["slug"], p["b"]["slug"]} for p in left] == [{b, c}]


def test_ignore_needs_two_known_recipes(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    mine = new_recipe(api_client, unique_user, random_string(), CAKE)
    theirs = new_recipe(api_client, h2_user, random_string(), CAKE)
    for body in ({"a": mine, "b": "gibt-es-nicht"}, {"a": mine, "b": theirs}, {"a": mine, "b": mine}):
        assert api_client.post(f"{URL}/ignore", json=body, headers=unique_user.token).status_code == 404


def test_tag_filter_keeps_pairs_with_the_tag_on_one_side(api_client: TestClient, unique_user: TestUser):
    tag = new_tag(api_client, unique_user)
    name = f"Apfelkuchen {random_string()}"
    tagged = new_recipe(api_client, unique_user, name, CAKE, tag)
    plain = new_recipe(api_client, unique_user, name, CAKE)
    other = new_recipe(api_client, unique_user, f"Gulasch {random_string()}", STEW)
    other_copy = new_recipe(api_client, unique_user, f"Gulasch {random_string()}", STEW)
    filtered = report(api_client, unique_user, f"?tag={tag['id']}")
    assert len(pair_of([tagged, plain], filtered)) == 1
    assert pair_of([other, other_copy], filtered) == []
    sides = {
        side["slug"]: side["tags"] for side in pair_of([tagged, plain], filtered)[0].values() if isinstance(side, dict)
    }
    assert sides == {tagged: [tag["name"]], plain: []}


def test_report_is_limited_to_200_pairs(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    name = f"Doppelt {random_string()}"
    for _ in range(205):
        new_recipe(api_client, h2_user, name, [])
    pairs = report(api_client, h2_user)
    assert len(pairs) == 200
    assert pairs == sorted(pairs, key=lambda p: p["similarity"], reverse=True)
