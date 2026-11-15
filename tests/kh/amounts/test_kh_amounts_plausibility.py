"""KH: tests for the review's hints on what looks wrong (v0.2 plan 2, task 7, A6): each hint fires at its limit and
not below it, and a clean recipe gets none."""

from fastapi.testclient import TestClient

from mealie.kh.amounts.plausibility import plausibility_warnings
from mealie.kh.amounts.service import ReadAmounts
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.services.parser_services._base import DataMatcher
from tests.kh.amounts.helpers import build_recipe, recognized
from tests.utils.fixture_schemas import TestUser


def warnings(recipe: RecipeDraft, unparsed: tuple[str, ...] = (), source: str | None = None) -> list[tuple[str, str]]:
    """The hints for RECIPE, as (kind, name)."""
    read = ReadAmounts(extras=[], unparsed=list(unparsed), links=[])
    return [(warning.kind, warning.name) for warning in plausibility_warnings(recipe, read, source)]


def of_kind(found: list[tuple[str, str]], kind: str) -> list[str]:
    """The names of the hints of one kind."""
    return [name for found_kind, name in found if found_kind == kind]


def test_a_clean_recipe_has_no_warnings(german: DataMatcher):
    steps = ["Das Mehl mit den Eiern und dem Salz verrühren.", "Bei 180 °C 45 Minuten backen."]
    recipe = build_recipe(german, ["250 g Mehl", "3 Eier", "1 Prise Salz"], steps)
    recipe.perform_time_seconds = 45 * 60
    assert warnings(recipe) == []


def test_unparsed_lines(german: DataMatcher):
    recipe = build_recipe(german, ["etwas Öl"], ["Mit etwas Öl braten."])
    assert warnings(recipe, unparsed=("eine Handvoll Nüsse",)) == [("amount_unparsed", "eine Handvoll Nüsse")]


def test_unusual_amounts(german: DataMatcher):
    lines = ["6000 g Mehl", "6 kg Kartoffeln", "25 EL Öl", "4 Prisen Salz", "40 Eier", "5000 g Zucker", "20 EL Milch"]
    unusual = of_kind(warnings(build_recipe(german, lines, [])), "amount_unusual")
    assert unusual == ["6000 g Mehl", "6 kg Kartoffeln", "25 EL Öl", "4 Prisen Salz", "40 Eier"]


def test_unusual_times(german: DataMatcher):
    recipe = build_recipe(german, [], [])
    recipe.perform_time_seconds = 25 * 3600
    assert [kind for kind, _ in warnings(recipe)] == ["time_unusual"]
    recipe.perform_time_seconds = 24 * 3600
    assert warnings(recipe) == []


def test_unusual_temperatures(german: DataMatcher):
    steps = ["Bei 350 °C backen.", "Bei 20 °C gehen lassen.", "Bei 350 °F backen.", "Bei 180 °C backen."]
    assert of_kind(warnings(build_recipe(german, [], steps)), "temperature_unusual") == ["350 °C", "20 °C", "350 °F"]


def test_unused_ingredients(german: DataMatcher):
    recipe = build_recipe(german, ["3 Eier", "2 Möhren", "1 TL Zimt"], ["Das Ei schlagen.", "Möhre schälen."])
    assert of_kind(warnings(recipe), "ingredient_unused") == ["Zimt"]


def test_converted_units(german: DataMatcher):
    recipe = build_recipe(german, ["250 g Mehl"], ["Das Mehl sieben."])
    assert warnings(recipe, source="2 cups flour") == [("units_converted", "cups")]
    assert warnings(recipe) == []


def test_the_review_gets_them(api_client: TestClient, unique_user: TestUser, german: DataMatcher, fake_ai):
    draft = recognized(api_client, unique_user, fake_ai)
    assert ("amount_unparsed", "eine Handvoll Nüsse") in [(w["kind"], w["name"]) for w in draft["warnings"]]
