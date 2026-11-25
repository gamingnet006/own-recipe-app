"""KH: the allergen rules (D44): 20 self-written ingredient texts and the allergens each must give, including the
German compounds that must not trigger (Buchweizenmehl, Kokosmilch, Muskatnuss) and the hidden ones that must."""

import pytest

from mealie.kh.allergens.rules import ALLERGENS, allergens_of_line, lines_allergens, recipe_allergens
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.schema.recipe.recipe_ingredient import IngredientFoodCreate, RecipeIngredient


def test_the_fourteen_keys_in_spec_order():
    assert ALLERGENS == (
        "gluten",
        "crustaceans",
        "eggs",
        "fish",
        "peanuts",
        "soy",
        "milk",
        "nuts",
        "celery",
        "mustard",
        "sesame",
        "sulphites",
        "lupin",
        "molluscs",
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Weizenmehl", {"gluten"}),
        ("Dinkelvollkornmehl", {"gluten"}),
        ("Buchweizenmehl", set()),
        ("Kokosmilch", set()),
        ("Vollmilch", {"milk"}),
        ("Parmesan", {"milk"}),
        ("Worcestersauce", {"fish"}),
        ("Gemüsebrühe", {"celery"}),
        ("Sojasauce", {"soy", "gluten"}),
        ("Mayonnaise", {"eggs", "mustard"}),
        ("Marzipan", {"nuts"}),
        ("Muskatnuss", set()),
        ("Erdnussöl", {"peanuts"}),
        ("Sesamöl", {"sesame"}),
        ("Garnelen", {"crustaceans"}),
        ("Miesmuscheln", {"molluscs"}),
        ("Senf", {"mustard"}),
        ("Weißwein", {"sulphites"}),
        ("Lupinenmehl", {"lupin"}),
        ("Pesto", {"nuts", "milk"}),
        # more compounds the rules must get right
        ("2 EL Mehl", {"gluten"}),
        ("Reis", set()),
        ("Eier", {"eggs"}),
        ("Weintrauben", set()),
        ("Erdnussbutter", {"peanuts"}),
        ("Haferdrink", {"gluten"}),
        # gaps and false alarms found in the audit (v1.1)
        ("Cheddar", {"milk"}),
        ("Halloumi", {"milk"}),
        ("Rührei", {"eggs"}),
        ("Hühnerei", {"eggs"}),
        ("Spiegelei", {"eggs"}),
        ("Eiweiss", {"eggs"}),
        ("Pizzateig", {"gluten"}),
        ("Semmelknödel", {"gluten"}),
        ("Langusten", {"crustaceans"}),
        ("Langustinen", {"crustaceans"}),
        ("Tamarinde", set()),
        ("Tamari", {"soy"}),
        ("Insekten", set()),
        ("Milcheiweiß", {"milk"}),
        ("Weinbergpfirsich", set()),
        ("Brei", set()),
    ],
)
def test_allergens_of_line(text: str, expected: set[str]):
    assert allergens_of_line(text) == expected


def test_case_and_decomposed_umlauts_do_not_matter():
    assert allergens_of_line("GEMÜSEBRÜHE") == {"celery"}
    assert allergens_of_line("Gemüsebrühe") == {"celery"}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # an exception is one compound, not the whole text
        ("Milchreis", {"milk"}),
        ("Kartoffelbrot", {"gluten"}),
        ("Kartoffelnudeln", {"gluten"}),
        ("Maisbrot", {"gluten"}),
        ("Kakaomilch", {"milk"}),
        ("Kokosmilch", set()),
        ("Reismilch", set()),
        ("Hafermilch", {"gluten"}),
        ("Mandelmilch", {"nuts"}),
        ("Buchweizenmehl", set()),
        ("Reismehl", set()),
        ("Maismehl", set()),
        ("Kartoffelmehl", set()),
        ("Kakaobutter", set()),
        ("Erdnussbutter", {"peanuts"}),
        ("Kokosjoghurt", set()),
        ("Glutenfreie Spaghetti", set()),
        ("Vegane Butter", set()),
        # pork is no wine
        ("Schweinefilet", set()),
        ("Schweinebauch", set()),
        ("Wildschwein", set()),
        ("Rotwein", {"sulphites"}),
        # gluten the rules used to miss
        *[
            (word, {"gluten"})
            for word in (
                "Brötchen",
                "Penne",
                "Fusilli",
                "Tagliatelle",
                "Lasagne",
                "Makkaroni",
                "Gnocchi",
                "Tortellini",
                "Ravioli",
                "Blätterteig",
                "Toast",
                "Baguette",
                "Zwieback",
                "Keks",
                "Graupen",
                "Bier",
                "Malz",
                "Panko",
            )  # fmt: skip
        ],
        ("Glasnudeln", set()),
        ("Schweineschmalz", set()),
        # false positives
        ("Butternutkürbis", set()),
        ("Butterbohnen", set()),
        ("Austernpilze", set()),
        ("Zimtschnecke", set()),
        ("Muschelnudeln", {"gluten"}),
        ("Tintenfisch", {"molluscs"}),
        # milk and egg words that must be found, and look-alikes that must not
        ("Crème fraiche", {"milk"}),
        ("Creme fraîche", {"milk"}),
        ("Schmand", {"milk"}),
        ("Joghurt", {"milk"}),
        ("Magerquark", {"milk"}),
        ("Frischkäse", {"milk"}),
        ("Eigelb", {"eggs"}),
        ("Eiweiß", {"eggs"}),
        ("Eis", set()),
        ("Einkorn", {"gluten"}),
    ],
)
def test_exceptions_cut_a_compound_not_the_whole_text(text: str, expected: set[str]):
    assert allergens_of_line(text) == expected


def test_lines_allergens_equals_recipe_allergens():
    lines = [
        RecipeIngredient(note="200 ml Milch"),
        RecipeIngredient(note="Salz", food=IngredientFoodCreate(name="Haselnüsse")),
        RecipeIngredient(note="1 Prise Salz"),
    ]
    corrections = {"milk": False, "sesame": True}
    recipe = RecipeDraft(name="x", recipe_ingredient=lines)
    assert lines_allergens(lines, corrections) == recipe_allergens(recipe, corrections)
    assert [hit.allergen for hit in lines_allergens(lines, corrections)] == ["milk", "nuts", "sesame"]
