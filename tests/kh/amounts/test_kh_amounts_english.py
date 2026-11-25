"""KH: English lines and an English group's units: Kochheft's extra English units come once, numbers follow the
language ("1,000 g" is a thousand in English, "1,5" a one and a half in German), and German stays as it was."""

import pytest

from mealie.db.models.recipe.ingredient import IngredientFoodModel
from mealie.kh.amounts.parse import ensure_english_units, ensure_extra_units, ensure_german_units, parse_ingredient
from mealie.kh.nutrition.calculate import calculate
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.schema.recipe.recipe_ingredient import IngredientFoodSave
from mealie.schema.recipe.recipe_nutrition import Nutrition
from mealie.schema.response.pagination import PaginationQuery
from mealie.services.parser_services._base import DataMatcher
from mealie.services.seeder.seeder_service import SeederService
from tests.utils.fixture_schemas import TestUser


@pytest.fixture
def english(g2_user: TestUser) -> DataMatcher:
    """g2_user's group with Mealie's English units, Kochheft's English additions and two foods."""
    repos = g2_user.repos
    SeederService(repos).seed_units("en-US")
    ensure_english_units(repos)
    known = DataMatcher(repos).foods_by_alias
    for name in ("flour", "sugar"):
        if IngredientFoodModel.normalize(name) not in known:
            repos.ingredient_foods.create(IngredientFoodSave(name=name, group_id=g2_user.group_id))
    return DataMatcher(repos)


def parse(matcher: DataMatcher, line: str, locale: str = "en-US"):
    return parse_ingredient(line, matcher.units_by_alias, matcher.foods_by_alias, locale)


@pytest.mark.parametrize(
    ("line", "quantity", "upper", "unit", "food"),
    [
        ("1,000 g flour", 1000, None, "gram", "flour"),
        ("1,250.5 g flour", 1250.5, None, "gram", "flour"),
        ("2.5 tbsp sugar", 2.5, None, "tablespoon", "sugar"),
        ("2 to 3 tbsp sugar", 2, 3, "tablespoon", "sugar"),
        ("about 200 g flour", 200, None, "gram", "flour"),
        ("3 pieces flour", 3, None, "piece", "flour"),
        ("4 slices flour", 4, None, "slice", "flour"),
        ("2 cups of flour", 2, None, "cup", "flour"),
        ("4 slices of flour", 4, None, "slice", "flour"),
    ],
)
def test_english_lines(english: DataMatcher, line, quantity, upper, unit, food):
    parsed = parse(english, line)

    assert (parsed.quantity, parsed.upper) == (quantity, upper)
    assert (parsed.unit.name if parsed.unit else None) == unit
    assert (parsed.food.name if parsed.food else None) == food


def test_the_number_format_follows_the_language(english: DataMatcher):
    assert parse(english, "1,000 g flour", "de-DE").quantity == 1  # German: a decimal comma
    assert parse(english, "1,5 g flour", "de-DE").quantity == 1.5
    assert parse(english, "1.000 g flour", "de-DE").quantity == 1000  # German: a thousands point
    assert parse(english, "1.000 g flour", "en-US").quantity == 1  # English: a decimal point
    assert parse(english, "12,34 g flour", "en-US").quantity == 12  # no thousands group: left alone


def test_extra_english_units_come_once(g2_user: TestUser, english: DataMatcher):
    repos = g2_user.repos
    units = {unit.name: unit for unit in repos.ingredient_units.page_all(PaginationQuery(page=1, per_page=-1)).items}
    assert units["piece"].abbreviation == "pc."
    assert {"slice", "pot", "jar", "cube", "sheet"} <= units.keys()
    assert {"pkg.", "packet", "package"} <= {alias.name for alias in units["pack"].aliases}
    ensure_extra_units(repos)
    after = repos.ingredient_units.page_all(PaginationQuery(page=1, per_page=-1)).items
    assert len(after) == len(units)
    repos.ingredient_units.delete(units["jar"].id)  # a unit deleted on purpose stays deleted
    ensure_extra_units(repos)
    assert "jar" not in {
        unit.name for unit in repos.ingredient_units.page_all(PaginationQuery(page=1, per_page=-1)).items
    }


def test_an_english_group_gets_no_german_units(g2_user: TestUser, english: DataMatcher):
    before = len(g2_user.repos.ingredient_units.page_all(PaginationQuery(page=1, per_page=-1)).items)
    ensure_german_units(g2_user.repos)
    assert len(g2_user.repos.ingredient_units.page_all(PaginationQuery(page=1, per_page=-1)).items) == before


def test_hand_entered_nutrition_follows_the_language():
    recipe = RecipeDraft(name="Test", nutrition=Nutrition(calories="1,250 kcal", fat_content="12,5 g"))

    english = calculate(recipe, {}, {}, {}, "en-US").values
    german = calculate(recipe, {}, {}, {}, "de-DE").values
    assert english and german
    assert english.kcal == 1250
    assert german.kcal == 1.25
    assert german.fat == 12.5  # German decimal comma
    assert english.fat == 12  # English: "12,5" is no number with a decimal comma; the first group is read
