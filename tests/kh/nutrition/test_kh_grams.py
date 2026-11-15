"""KH: tests of the grams of an ingredient line (D44): units, densities, pieces, and what cannot be weighed."""

import pytest

from mealie.kh.amounts.parse import stem
from mealie.kh.nutrition.grams import food_entry, grams_of, name_stems
from mealie.schema.recipe.recipe_ingredient import CreateIngredientFood, CreateIngredientUnit, RecipeIngredient


def line(quantity: float | None, unit: str | None, food: str | None, abbreviation: str = "") -> RecipeIngredient:
    """An ingredient line like Mealie holds it: a quantity, a unit with its abbreviation, a food."""
    return RecipeIngredient(
        quantity=quantity,
        unit=CreateIngredientUnit(name=unit, abbreviation=abbreviation) if unit else None,
        food=CreateIngredientFood(name=food) if food else None,
    )


@pytest.mark.parametrize(
    ("ingredient", "expected"),
    [
        (line(250, "Gramm", "Mehl", "g"), 250),
        (line(1, "Kilogramm", "Kartoffeln", "kg"), 1000),
        (line(500, "Milliliter", "Milch", "ml"), 515),  # Milch: 1.03 g/ml
        (line(2, "Esslöffel", "Öl", "EL"), 27.6),  # 2 x 15 ml x 0.92 g/ml
        (line(1, "Liter", "Wasser", "l"), 1000),
        (line(1, "Becher", "Joghurt"), 200),  # a Becher is 200 g, whatever the density
        (line(3, None, "Eier"), 165),  # pieces: 55 g each
        (line(2, None, "Äpfel"), 300),  # the lower end of "2–3 Äpfel", which Mealie keeps as the quantity
        (line(500, "ml", "Etwas Unbekanntes"), 500),  # no density known: DEFAULT_DENSITY
        (line(1, "Prise", "Salz"), None),
        (line(1, "Msp.", "Pfeffer"), None),
        (line(1, "Dose", "Tomaten"), None),
        (line(None, None, "Salz"), None),
        (line(0, None, "Salz"), None),
        (line(1, None, "Petersilienwurzel"), None),  # a piece of a food without a known weight
        (line(2, None, None), None),  # no food, no weight
    ],
)
def test_grams_of(ingredient: RecipeIngredient, expected: float | None) -> None:
    assert grams_of(ingredient) == (pytest.approx(expected) if expected is not None else None)


def test_own_piece_weight_goes_before_the_table() -> None:
    assert grams_of(line(1, None, "Zwiebel"), piece_grams=100) == 100
    assert grams_of(line(1, None, "Zwiebel")) == 80


def test_a_unit_found_by_its_abbreviation_or_plural() -> None:
    by_abbreviation = RecipeIngredient(
        quantity=2,
        unit=CreateIngredientUnit(name="Löffel groß", abbreviation="EL"),
        food=CreateIngredientFood(name="Öl"),
    )
    by_plural = RecipeIngredient(
        quantity=2,
        unit=CreateIngredientUnit(name="Tasse", plural_name="Tassen"),
        food=CreateIngredientFood(name="Wasser"),
    )

    assert grams_of(by_abbreviation) == pytest.approx(27.6)
    assert grams_of(by_plural) == pytest.approx(480)


def test_name_stems_try_the_noun_before_the_adjective() -> None:
    assert name_stems("Grüne Bohnen")[1:] == [stem("Bohnen"), stem("Grüne")]


@pytest.mark.parametrize(
    ("food", "like"),
    [("Weizenmehl", "Mehl"), ("Dinkelmehl Type 630", "Mehl"), ("Rohrzucker", "Zucker"), ("Sonnenblumenöl", "Öl")],
)
def test_a_compound_weighs_like_its_last_part(food: str, like: str) -> None:
    assert food_entry(food) == food_entry(like) != {}


def test_a_short_word_is_no_compound() -> None:
    assert food_entry("Brei") == {}  # ends in "ei", but is no egg


@pytest.mark.parametrize(
    ("ingredient", "expected"),
    [
        (line(2, "Zehe", "Knoblauch"), 8),  # a Zehe of Knoblauch: 4 g
        (line(2, "Zehen", "Knoblauch"), 8),
        (line(2, "Stück", "Zwiebeln", "Stk."), 160),  # a Stück counts as a piece
        (line(2, "Stk.", "Zwiebeln"), 160),
        (line(3, "Stück", "Petersilienwurzel"), None),  # no piece weight known
        (line(1, "Pfund", "Hackfleisch"), 500),
    ],
)
def test_pieces_and_pfund_as_units(ingredient: RecipeIngredient, expected: float | None) -> None:
    assert grams_of(ingredient) == (pytest.approx(expected) if expected is not None else None)
