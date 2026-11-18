"""KH: tests for pages read without AI, like Chefkoch (v1.3): plural markers such as "Birne(n)" are dropped, a first
step "Für 12 Muffins." becomes the yield, and steps get linked to the ingredients they name."""

from fastapi.testclient import TestClient

from mealie.kh.amounts.parse import parse_ingredient
from mealie.kh.amounts.steps import link_steps, name_stems, yield_from_steps
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.services.parser_services._base import DataMatcher
from tests.kh.amounts.helpers import build_recipe
from tests.kh.drafts.helpers import get_draft, post_draft
from tests.utils.fixture_schemas import TestUser


def test_plural_markers_are_dropped(german: DataMatcher):
    pear = parse_ingredient("200 g Birne(n) (aus dem Glas)", german.units_by_alias, german.foods_by_alias)
    assert pear.note == "Birne (aus dem Glas)"  # no such food in the test group: the name stays in the note
    egg = parse_ingredient("1 Ei(er)", german.units_by_alias, german.foods_by_alias)
    assert egg.food is not None and egg.food.name == "Ei" and egg.note == ""
    salt = parse_ingredient("1 Prise(n) Salz", german.units_by_alias, german.foods_by_alias)
    assert salt.unit is not None and salt.food is not None and salt.food.name == "Salz"


def test_steps_are_linked_to_the_ingredients_they_name(german: DataMatcher):
    lines = ["200 ml Milch", "250 g Mehl", "2 Eier"]  # Milch is no food in the test group: linked by its note
    recipe = build_recipe(german, lines, ["Die Milch kochen.", "Mehl und Eier.", "Backen."])
    link_steps(recipe, german.units_by_alias)
    index = {line.reference_id: n for n, line in enumerate(recipe.recipe_ingredient)}
    linked = [[index[ref.reference_id] for ref in step.ingredient_references] for step in recipe.recipe_instructions]
    assert linked == [[0], [1, 2], []]


def test_steps_with_links_stay_as_they_are(german: DataMatcher):
    recipe = build_recipe(german, ["200 ml Milch", "250 g Mehl"], ["Die Milch und das Mehl."])
    link_steps(recipe, german.units_by_alias)
    recipe.recipe_instructions[0].ingredient_references = recipe.recipe_instructions[0].ingredient_references[:1]
    link_steps(recipe, german.units_by_alias)  # the AI or the person linked already: nothing is added
    assert len(recipe.recipe_instructions[0].ingredient_references) == 1


def test_first_step_with_the_yield_becomes_the_yield(german: DataMatcher):
    recipe = build_recipe(german, ["250 g Mehl"], ["Für 12 Muffins.", "Backen."])
    recipe.recipe_servings = 1
    yield_from_steps(recipe)
    assert (recipe.recipe_servings, recipe.recipe_yield_quantity, recipe.recipe_yield) == (12, 12, "Muffins")
    assert [step.text for step in recipe.recipe_instructions] == ["Backen."]


def test_other_first_steps_stay(german: DataMatcher):
    recipe = build_recipe(german, ["250 g Mehl"], ["Für den Teig das Mehl sieben.", "Backen."])
    recipe.recipe_servings = 4
    yield_from_steps(recipe)
    assert recipe.recipe_servings == 4 and len(recipe.recipe_instructions) == 2


def test_chefkoch_style_page(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_page):
    fake_page("page-chefkoch-style.html")
    draft = post_draft(api_client, unique_user, data={"url": "https://example.com/testmuffins"}).json()
    recipe = get_draft(api_client, unique_user, draft["id"]).json()["recipe"]
    assert recipe["recipeServings"] == 12 and recipe["recipeYield"] == "Muffins"
    assert [step["text"] for step in recipe["recipeInstructions"]][0] == "Die Milch kurz aufkochen."
    assert len(recipe["recipeInstructions"][0]["ingredientReferences"]) == 1
    assert [(line["food"] or {}).get("name") for line in recipe["recipeIngredient"]][2:] == ["Mehl", "Ei", "Salz"]
    assert recipe["recipeIngredient"][1]["note"] == "Birne (aus dem Glas)"


def test_a_unit_left_in_the_note_is_no_name(german: DataMatcher):
    # browser check v1.3: a line read without its unit ("ml Milch", "g Zucker") must not link every step with "g"
    recipe = build_recipe(german, [], ["Die Milch kochen.", "100 g Quark verrühren."])
    recipe.recipe_ingredient = [
        RecipeIngredient(quantity=200, note="ml Milch"),
        RecipeIngredient(quantity=100, note="g Zucker"),
    ]
    link_steps(recipe, german.units_by_alias)
    milk = recipe.recipe_ingredient[0].reference_id
    assert [[ref.reference_id for ref in step.ingredient_references] for step in recipe.recipe_instructions] == [
        [milk],
        [],
    ]


def test_a_unit_word_without_known_units_is_no_name():
    # a group without Mealie's German units: "g Zucker" still names Zucker, "ml" no step
    assert name_stems(RecipeIngredient(quantity=100, note="g Zucker"), {}) == name_stems(
        RecipeIngredient(note="Zucker")
    )
    assert "ei" in name_stems(RecipeIngredient(quantity=2, note="Ei"), {})
