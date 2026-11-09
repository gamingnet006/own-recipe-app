"""KH: substitutions and variants (D44): own rules before the standard ones, a variant with replaced foods whose
original stays untouched, two variants in a row, and that a household's rules stay its own."""

import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.kh.allergens.models import KhSubstitution
from mealie.kh.allergens.rules import allergens_of_line
from mealie.kh.allergens.schemas import ALLERGEN_NAMES_DE, ALLERGENS
from mealie.kh.allergens.substitutions import standard_rules
from tests.kh.nutrition.helpers import new_recipe
from tests.utils import api_routes, random_string
from tests.utils.fixture_schemas import TestUser

KH = "/api/kh"
RULES = f"{KH}/substitutions"


def dairy_recipe(api_client: TestClient, user: TestUser) -> dict:
    """Milk, butter and salt: two lines with milk, one innocent."""
    return new_recipe(api_client, user, [(200, "ml", "Milch", ""), (50, "g", "Butter", ""), (1, "Prise", "Salz", "")])


def add_rule(api_client: TestClient, user: TestUser, match: str, replacement: str, allergen: str = "milk"):
    return api_client.post(
        RULES, json={"match": match, "replacement": replacement, "allergen": allergen}, headers=user.token
    )


def clear_rules(api_client: TestClient, user: TestUser) -> None:
    for rule in api_client.get(RULES, headers=user.token).json():
        api_client.delete(f"{RULES}/{rule['id']}", headers=user.token)


def report(api_client: TestClient, user: TestUser, slug: str) -> dict:
    return api_client.get(f"{KH}/recipes/{slug}/allergens", headers=user.token).json()


def variant(api_client: TestClient, user: TestUser, slug: str, allergens: list[str]):
    return api_client.post(f"{KH}/recipes/{slug}/variant", json={"allergens": allergens}, headers=user.token)


def test_standard_substitutions_are_listed_per_line(api_client: TestClient, unique_user: TestUser):
    clear_rules(api_client, unique_user)
    found = report(api_client, unique_user, dairy_recipe(api_client, unique_user)["slug"])["substitutions"]
    assert found == [
        {"line": "200 Milliliter Milch", "allergen": "milk", "replacement": "Reisdrink"},
        {"line": "50 Gramm Butter", "allergen": "milk", "replacement": "Margarine"},
    ]


def test_an_own_rule_wins_over_the_standard_one(api_client: TestClient, unique_user: TestUser):
    clear_rules(api_client, unique_user)
    slug = dairy_recipe(api_client, unique_user)["slug"]
    created = add_rule(api_client, unique_user, " MILCH ", "Mandeldrink")
    assert created.status_code == 201
    assert created.json() == {
        "id": created.json()["id"],
        "match": "milch",
        "replacement": "Mandeldrink",
        "allergen": "milk",
    }
    found = report(api_client, unique_user, slug)["substitutions"]
    assert [s["replacement"] for s in found] == ["Mandeldrink", "Margarine"]  # one per line, the own one first
    clear_rules(api_client, unique_user)
    assert report(api_client, unique_user, slug)["substitutions"][0]["replacement"] == "Reisdrink"


def test_rules_are_validated_and_deleted(api_client: TestClient, unique_user: TestUser):
    clear_rules(api_client, unique_user)
    assert add_rule(api_client, unique_user, "milch", "Hafer", "zimt").status_code == 422
    assert add_rule(api_client, unique_user, "  ", "Hafer").status_code == 422
    rule = add_rule(api_client, unique_user, "sahne", "Pflanzensahne").json()
    assert api_client.get(RULES, headers=unique_user.token).json() == [rule]
    assert api_client.delete(f"{RULES}/{rule['id']}", headers=unique_user.token).status_code == 200
    assert api_client.get(RULES, headers=unique_user.token).json() == []
    assert api_client.delete(f"{RULES}/{rule['id']}", headers=unique_user.token).status_code == 404


def test_another_households_rules_are_not_visible(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    clear_rules(api_client, unique_user)
    clear_rules(api_client, h2_user)
    slug = dairy_recipe(api_client, unique_user)["slug"]
    rule = add_rule(api_client, unique_user, "milch", "Mandeldrink").json()
    assert api_client.get(RULES, headers=h2_user.token).json() == []
    assert api_client.delete(f"{RULES}/{rule['id']}", headers=h2_user.token).status_code == 404
    assert report(api_client, h2_user, slug)["substitutions"][0]["replacement"] == "Reisdrink"
    assert len(api_client.get(RULES, headers=unique_user.token).json()) == 1
    clear_rules(api_client, unique_user)


def test_variant_replaces_the_foods_and_leaves_the_original_alone(api_client: TestClient, unique_user: TestUser):
    clear_rules(api_client, unique_user)
    original = dairy_recipe(api_client, unique_user)
    slug, headers = original["slug"], unique_user.token
    api_client.put(f"{KH}/recipes/{slug}/allergens/sesame", json={"present": True}, headers=headers)
    before = (
        api_client.get(api_routes.recipes_slug(slug), headers=headers).json(),
        api_client.get(f"{KH}/amounts/{original['id']}", headers=headers).json(),
        report(api_client, unique_user, slug)["hits"],
    )

    response = variant(api_client, unique_user, slug, ["milk"])
    assert response.status_code == 201
    new = api_client.get(api_routes.recipes_slug(response.json()["slug"]), headers=headers).json()
    assert new["name"] == f"{original['name']} (ohne Milch)"
    assert new["id"] != original["id"]
    lines = [(i["quantity"], i["unit"]["abbreviation"], i["food"]["name"]) for i in new["recipeIngredient"]]
    assert lines == [(200, "ml", "Reisdrink"), (50, "g", "Margarine"), (1, "Prise", "Salz")]
    assert [i["display"] for i in new["recipeIngredient"]][0] == "200 Milliliter Reisdrink"
    assert "milk" not in {h["allergen"] for h in report(api_client, unique_user, new["slug"])["hits"]}

    after = (
        api_client.get(api_routes.recipes_slug(slug), headers=headers).json(),
        api_client.get(f"{KH}/amounts/{original['id']}", headers=headers).json(),
        report(api_client, unique_user, slug)["hits"],
    )
    assert after == before


def test_two_variants_in_a_row_get_unique_slugs(api_client: TestClient, unique_user: TestUser):
    clear_rules(api_client, unique_user)
    slug = dairy_recipe(api_client, unique_user)["slug"]
    first = variant(api_client, unique_user, slug, ["milk"]).json()["slug"]
    second = variant(api_client, unique_user, slug, ["milk"]).json()["slug"]
    assert len({slug, first, second}) == 3
    for copy in (first, second):
        assert api_client.get(api_routes.recipes_slug(copy), headers=unique_user.token).status_code == 200


def test_variant_reuses_an_existing_food_by_name(api_client: TestClient, unique_user: TestUser):
    clear_rules(api_client, unique_user)
    add_rule(api_client, unique_user, "milch", "reisdrink")  # the rule's spelling differs from the food's
    slug = new_recipe(api_client, unique_user, [(1, "ml", "Milch", ""), (1, "ml", "Reisdrink", "")])["slug"]
    new = api_client.get(
        api_routes.recipes_slug(variant(api_client, unique_user, slug, ["milk"]).json()["slug"]),
        headers=unique_user.token,
    ).json()
    foods = {i["food"]["id"] for i in new["recipeIngredient"]}
    assert len(foods) == 1  # both lines use the group's one "Reisdrink"
    clear_rules(api_client, unique_user)


def test_variant_needs_something_to_replace_and_a_known_key(api_client: TestClient, unique_user: TestUser):
    clear_rules(api_client, unique_user)
    slug = dairy_recipe(api_client, unique_user)["slug"]
    assert variant(api_client, unique_user, slug, ["peanuts"]).status_code == 422  # not in the recipe
    assert variant(api_client, unique_user, slug, ["zimt"]).status_code == 422
    assert variant(api_client, unique_user, "gibt-es-nicht", ["milk"]).status_code == 404


def test_deleting_a_household_removes_its_rules(
    api_client: TestClient, admin_token, session: Session, unique_user: TestUser
):
    household = api_client.post(
        api_routes.admin_households,
        json={"name": random_string(), "groupId": str(unique_user.group_id)},
        headers=admin_token,
    ).json()
    session.add(
        KhSubstitution(session=session, household_id=household["id"], match="milch", replacement="x", allergen="milk")
    )
    session.commit()
    assert (
        api_client.delete(api_routes.admin_households_item_id(household["id"]), headers=admin_token).status_code == 200
    )
    left = session.execute(sa.select(KhSubstitution).where(KhSubstitution.household_id == household["id"])).all()
    assert left == []


def test_no_standard_replacement_has_the_allergen_it_replaces():
    for rule in standard_rules():
        assert rule.allergen not in allergens_of_line(rule.replacement), rule


def test_variant_of_a_line_without_food_replaces_its_note(api_client: TestClient, unique_user: TestUser):
    clear_rules(api_client, unique_user)
    slug = new_recipe(api_client, unique_user, [(None, None, None, "100 g gehackte Walnüsse")])["slug"]
    new = api_client.get(
        api_routes.recipes_slug(variant(api_client, unique_user, slug, ["nuts"]).json()["slug"]),
        headers=unique_user.token,
    ).json()
    assert new["recipeIngredient"][0]["note"] == "Sonnenblumenkerne"
    assert new["name"].endswith("(ohne Schalenfrüchte)")


def test_variant_names_are_the_spec_names_from_one_dict():
    assert tuple(ALLERGEN_NAMES_DE) == ALLERGENS
    assert list(ALLERGEN_NAMES_DE.values()) == [
        "Gluten", "Krebstiere", "Ei", "Fisch", "Erdnüsse", "Soja", "Milch", "Schalenfrüchte", "Sellerie", "Senf",
        "Sesam", "Sulfite", "Lupinen", "Weichtiere",
    ]  # fmt: skip


def test_generic_rules_do_not_hit_compounds(api_client: TestClient, unique_user: TestUser):
    """Vollmilchschokolade is no milk to swap for Reisdrink, Butterkekse no butter to swap for Margarine."""
    clear_rules(api_client, unique_user)
    slug = new_recipe(api_client, unique_user, [(100, "g", "Vollmilchschokolade", ""), (100, "g", "Butterkekse", "")])[
        "slug"
    ]
    found = report(api_client, unique_user, slug)
    assert {h["allergen"] for h in found["hits"]} >= {"milk", "gluten"}
    assert found["substitutions"] == []


def test_a_variant_only_names_what_it_removed(api_client: TestClient, unique_user: TestUser):
    """Mozzarella has no rule, so the milk stays: no variant for milk, and the name of one for more says Gluten only."""
    clear_rules(api_client, unique_user)
    lines = [(200, "ml", "Milch", ""), (100, "g", "Mozzarella", ""), (100, "g", "Weizenmehl", "")]
    slug = new_recipe(api_client, unique_user, lines)["slug"]
    assert variant(api_client, unique_user, slug, ["milk"]).status_code == 422
    response = variant(api_client, unique_user, slug, ["milk", "gluten"])
    assert response.status_code == 201
    new = api_client.get(api_routes.recipes_slug(response.json()["slug"]), headers=unique_user.token).json()
    assert new["name"].endswith("(ohne Gluten)")


def test_a_variant_keeps_added_corrections_but_not_removed_ones(api_client: TestClient, unique_user: TestUser):
    clear_rules(api_client, unique_user)
    slug = dairy_recipe(api_client, unique_user)["slug"]
    headers = unique_user.token
    api_client.put(f"{KH}/recipes/{slug}/allergens/sesame", json={"present": True}, headers=headers)
    api_client.put(f"{KH}/recipes/{slug}/allergens/celery", json={"present": False}, headers=headers)
    new_slug = variant(api_client, unique_user, slug, ["milk"]).json()["slug"]
    hits = {h["allergen"]: h["corrected"] for h in report(api_client, unique_user, new_slug)["hits"]}
    assert hits == {"sesame": True}
