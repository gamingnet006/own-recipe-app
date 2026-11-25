"""KH: allergen detection and substitution hints for English ingredient lines (own test lines)."""

from types import SimpleNamespace

import pytest

from mealie.kh.allergens.rules import allergens_of_line
from mealie.kh.allergens.substitutions import _plan
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("2 eggs", {"eggs"}),
        ("1 aubergine, or eggplant", set()),
        ("200 ml whole milk", {"milk"}),
        ("200 ml coconut milk", set()),
        ("2 tbsp peanut butter", {"peanuts"}),
        ("100 g butter", {"milk"}),
        ("1 tsp cream of tartar", set()),
        ("1 pinch nutmeg", set()),
        ("200 g salmon fillet", {"fish"}),
        ("1 can tuna", {"fish"}),
        ("300 g cod", {"fish"}),
        ("200 g prawns", {"crustaceans"}),
        ("12 mussels", {"molluscs"}),
        ("1 crab apple", set()),
        ("200 g wheat flour", {"gluten"}),
        ("200 g rice flour", set()),
        ("100 g gluten-free pasta", set()),
        ("50 g almonds", {"nuts"}),
        ("1 bunch parsley", set()),
        ("1 head of kale", set()),
        ("200 g blueberries", set()),
        ("1 pint beer", {"gluten"}),
        ("2 stalks celery", {"celery"}),
        ("1 tsp mustard", {"mustard"}),
        ("2 tbsp tahini", {"sesame"}),
        ("100 ml red wine", {"sulphites"}),
        ("1 tbsp soy sauce", {"soy", "gluten"}),
        ("100 g lupin flour", {"lupin"}),
        ("200 g vegan cheese", set()),
        ("500 ml chicken broth", {"celery"}),
        ("1 tbsp toasted sesame oil", {"sesame"}),
        ("50 g toasted almonds", {"nuts"}),
        ("2 slices toast", {"gluten"}),
        ("200 g mixed veggies", set()),
        ("50 g Parmigiano-Reggiano", {"milk"}),
        ("100 g buckwheat flour", set()),
        ("2 tsp self-raising flour", {"gluten"}),
        ("200 g bean curd", {"soy"}),
        ("1 jar pasta sauce", set()),
        ("3 scrambled eggs", {"eggs"}),
    ],
)
def test_english_lines(line: str, expected: set[str]) -> None:
    found = allergens_of_line(line)
    assert expected <= found
    if not expected:
        assert not found
    if "gluten" not in expected:
        assert "gluten" not in found, line  # broth, toasted, buckwheat: no gluten words hidden in other words
    if "eggs" not in expected:
        assert "eggs" not in found, line  # veggies, Reggiano
    if "sulphites" not in expected:
        assert "sulphites" not in found, line  # "raising" is no raisin


def test_hints_follow_the_person_language() -> None:
    recipe = SimpleNamespace(recipe_ingredient=[RecipeIngredient(note="200 g pasta"), RecipeIngredient(note="Milch")])
    english = _plan(recipe, ["gluten", "milk"], [], "en-US")  # type: ignore[arg-type]
    german = _plan(recipe, ["gluten", "milk"], [], "de-DE")  # type: ignore[arg-type]
    assert english[0][1].replacement == "Gluten-free pasta"
    assert german[0][1].replacement == "Glutenfreie Pasta"
    assert english[1][1].replacement == "Reisdrink"  # a German line still finds its hint
