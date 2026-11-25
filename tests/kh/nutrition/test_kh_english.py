"""KH: English food names and units reach the same nutrition values and piece weights as the German ones (D44, D-en)."""

import json

import pytest

from mealie.kh.nutrition.bls import load_bls
from mealie.kh.nutrition.calculate import calculate
from mealie.kh.nutrition.grams import _weights, food_entry, grams_of, name_stems
from mealie.kh.nutrition.mapping import load_aliases, suggest_code
from mealie.repos.seed._abstract_seeder import AbstractSeeder
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.schema.recipe.recipe_ingredient import IngredientFoodCreate, IngredientUnitCreate, RecipeIngredient


def line(quantity: float | None, unit: str | None, food: str, abbreviation: str = "", plural: str = ""):
    """An ingredient line as Mealie's English seed would hold it."""
    return RecipeIngredient(
        quantity=quantity,
        unit=IngredientUnitCreate(name=unit, plural_name=plural, abbreviation=abbreviation) if unit else None,
        food=IngredientFoodCreate(name=food),
    )


def _keys() -> set[str]:
    """The stems of the weight table's foods."""
    return set(_weights()[1])


def kcal_of(lines: list[RecipeIngredient]) -> float | None:
    """The recipe's kcal for the given lines, with the shipped BLS table and aliases."""
    recipe = RecipeDraft(name="Test", recipe_ingredient=lines, recipe_servings=1)
    result = calculate(recipe, {}, load_bls(), load_aliases())
    assert result.missing == []
    return result.values.kcal if result.values else None


def test_an_english_recipe_gets_the_values_of_its_german_twin() -> None:
    english = [
        line(2, None, "eggs"),
        line(250, "milliliter", "milk", "ml"),
        line(200, "gram", "flour", "g"),
        line(1, "tablespoon", "butter", "tbsp"),
    ]
    german = [
        line(2, None, "Eier"),
        line(250, "Milliliter", "Milch", "ml"),
        line(200, "Gramm", "Mehl", "g"),
        line(1, "Esslöffel", "Butter", "EL"),
    ]

    assert kcal_of(english) == kcal_of(german) != None  # noqa: E711


@pytest.mark.parametrize(
    ("name", "like"),
    [
        ("eggs", "Eier"), ("onions", "Zwiebeln"), ("tomatoes", "Tomaten"), ("potatoes", "Kartoffeln"),
        ("brown sugar", "Brauner Zucker"), ("powdered sugar", "Puderzucker"), ("icing sugar", "Puderzucker"),
        ("sour cream", "Saure Sahne"), ("heavy cream", "Sahne"), ("red onions", "Zwiebeln"),
        ("extra virgin olive oil", "Olivenöl"), ("red bell peppers", "Paprika"), ("Ice Cream", "Eis"),
        ("chicken breasts", "Hähnchenbrust"), ("ground beef", "Hackfleisch"), ("baking powder", "Backpulver"),
    ],
)  # fmt: skip
def test_english_names_suggest_the_german_code(name: str, like: str) -> None:
    foods, aliases = load_bls(), load_aliases()

    assert suggest_code(name, foods, aliases) == suggest_code(like, foods, aliases) is not None


@pytest.mark.parametrize(
    ("ingredient", "expected"),
    [
        (line(1, "pound", "flour", "lb", "pounds"), 453.6),
        (line(2, "ounce", "butter", "oz"), 56.7),
        (line(1, "cup", "water", "c", "cups"), 240),
        (line(2, "teaspoon", "salt", "tsp", "teaspoons"), 12),  # 2 x 5 ml x 1.2 g/ml
        (line(1, "tablespoon", "olive oil", "tbsp"), 13.8),  # 15 ml x 0.92 g/ml
        (line(3, None, "large eggs"), 165),
        (line(2, None, "red onions"), 160),
        (line(2, "piece", "yellow bell peppers"), 320),
        (line(3, "clove", "garlic", "", "cloves"), 12),
        (line(2, "clove", "garlic cloves", "", "cloves"), 8),
        (line(1, "can", "tomatoes"), None),  # a can's weight is not known
    ],
)  # fmt: skip
def test_english_units_and_piece_weights(ingredient: RecipeIngredient, expected: float | None) -> None:
    assert grams_of(ingredient) == (pytest.approx(expected) if expected is not None else None)


def test_an_english_compound_weighs_like_its_last_word() -> None:
    assert food_entry("buttermilk") == food_entry("milk") != {}
    assert food_entry("whole wheat flour") == food_entry("flour") != {}


@pytest.mark.parametrize(
    ("name", "code_name"),
    [
        ("peanut butter", "Erdnussbutter"), ("coconut milk", "Kokosmilch"), ("almond milk", "Mandeldrink"),
        ("soy milk", "Sojadrink"), ("oat milk", "Haferdrink"), ("vanilla ice cream", "Speiseeis"),
        ("cream cheese", "Frischkäse"), ("buttermilk", "Buttermilch"), ("butternut squash", "Kürbis"),
        ("rice vinegar", "Weinessig"), ("apple cider vinegar", "Apfelessig"), ("lemon juice", "Zitronensaft"),
        ("sweet potato", None), ("pineapple", "Ananas"), ("horseradish", "Meerrettich"),
    ],
)  # fmt: skip
def test_english_compounds_do_not_take_their_head_noun(name: str, code_name: str | None) -> None:
    foods = load_bls()
    code = suggest_code(name, foods, load_aliases())

    assert code is not None
    assert code_name is None or foods[code].name.startswith(code_name)
    assert foods[code].name not in {foods["Q611000"].name, foods["M111300"].name, foods["M173800"].name}


def test_pineapple_and_horseradish_are_no_apple_or_radish() -> None:
    assert grams_of(line(1, None, "pineapple")) == 900
    assert grams_of(line(1, None, "horseradish")) == 100


def test_english_seed_foods_reach_a_weight_only_by_their_own_name() -> None:
    """Guard for the compound rule (made for German): no English food of Mealie's seed may weigh like the end of its
    name, e.g. "pineapple" like "apple", unless it is a known true compound."""
    seed = json.loads((AbstractSeeder.resources / "foods" / "locales" / "en-US.json").read_text(encoding="utf-8"))
    names = [food["name"] for group in seed.values() for food in group["foods"].values()]
    true_compounds = {"buttermilk", "cornmeal", "cornstarch"}
    wrong = [
        name
        for name in names
        if name not in true_compounds and food_entry(name) and not any(k in _keys() for k in name_stems(name))
    ]

    assert wrong == []
