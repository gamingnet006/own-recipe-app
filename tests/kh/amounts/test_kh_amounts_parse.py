"""KH: tests for reading German ingredient lines (v0.2 plan 2, task 1, A1): amounts, ranges, units and foods of the
group, fixed amounts, and the German units Küchenhelfer adds once."""

import pytest

from mealie.kh.amounts.parse import ensure_german_units, parse_ingredient, stem
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe_ingredient import IngredientUnit
from mealie.schema.response.pagination import PaginationQuery
from mealie.services.parser_services._base import DataMatcher
from mealie.services.seeder.seeder_service import SeederService
from tests.utils.fixture_schemas import TestUser

CASES = [  # line, quantity, upper, unit name, food name, note, fixed
    ("250 g Mehl", 250, None, "Gramm", "Mehl", "", False),
    ("250g Mehl", 250, None, "Gramm", "Mehl", "", False),
    ("1,5 kg Kartoffeln", 1.5, None, "Kilogramm", None, "Kartoffeln", False),
    ("½ TL Salz", 0.5, None, "Teelöffel", "Salz", "", False),
    ("1 1/2 TL Salz", 1.5, None, "Teelöffel", "Salz", "", False),
    ("1 ½ EL Zucker", 1.5, None, "Esslöffel", "Zucker", "", False),
    ("1½ EL Zucker", 1.5, None, "Esslöffel", "Zucker", "", False),
    ("2-3 EL Zucker", 2, 3, "Esslöffel", "Zucker", "", False),
    ("2–3 EL Zucker", 2, 3, "Esslöffel", "Zucker", "", False),
    ("2 bis 3 EL Zucker", 2, 3, "Esslöffel", "Zucker", "", False),
    ("3 Eier", 3, None, None, "Ei", "", False),
    ("2 Zwiebeln, gewürfelt", 2, None, None, "Zwiebel", "gewürfelt", False),
    ("1 Prise Salz", 1, None, "Prise", "Salz", "", True),
    ("1 Msp. Muskat", 1, None, "Messerspitze", None, "Muskat", True),
    ("1 Pck. Vanillezucker", 1, None, "Packung", None, "Vanillezucker", False),
    ("1 l Milch", 1, None, "Liter", None, "Milch", False),
    ("2 Stk. Ingwer", 2, None, "Stück", None, "Ingwer", False),
    ("4 Scheiben Toast", 4, None, "Scheibe", None, "Toast", False),
    ("1 Dose Tomaten (400 g)", 1, None, "Dose", None, "Tomaten (400 g)", False),
    ("1 EL Öl", 1, None, "Esslöffel", None, "Öl", False),
    ("etwas Öl", None, None, None, None, "etwas Öl", True),
    ("Salz und Pfeffer nach Geschmack", None, None, None, None, "Salz und Pfeffer nach Geschmack", True),
    ("eine Handvoll Nüsse", None, None, None, None, "eine Handvoll Nüsse", False),
]


def all_units(repos: AllRepositories) -> list[IngredientUnit]:
    """Every unit of the repositories' group."""
    return repos.ingredient_units.page_all(PaginationQuery(page=1, per_page=-1)).items


@pytest.mark.parametrize(("line", "quantity", "upper", "unit", "food", "note", "fixed"), CASES)
def test_german_lines(german: DataMatcher, line, quantity, upper, unit, food, note, fixed):
    parsed = parse_ingredient(line, german.units_by_alias, german.foods_by_alias)
    assert (parsed.quantity, parsed.upper) == (quantity, upper)
    assert (parsed.unit.name if parsed.unit else None) == unit
    assert (parsed.food.name if parsed.food else None) == food
    assert (parsed.note, parsed.fixed) == (note, fixed)


def test_endings_go():
    assert stem("Eier") == stem("Ei")
    assert stem("Möhren") == stem("Möhre")


def test_german_units_come_once(unique_user: TestUser, german: DataMatcher):
    repos = unique_user.repos
    units = {unit.name: unit for unit in all_units(repos)}
    assert (units["Messerspitze"].abbreviation, units["Stück"].abbreviation) == ("Msp.", "Stk.")
    assert (units["Scheibe"].plural_name, units["Glas"].plural_name, units["Blatt"].plural_name) == (
        "Scheiben",
        "Gläser",
        "Blätter",
    )
    assert {"Becher", "Würfel"} <= units.keys()
    assert {"Pck.", "Päckchen"} <= {alias.name for alias in units["Packung"].aliases}
    ensure_german_units(repos)
    assert len(all_units(repos)) == len(units)
    # a unit deleted on purpose stays deleted: Messerspitze marks the group as done
    repos.ingredient_units.delete(units["Becher"].id)
    ensure_german_units(repos)
    assert "Becher" not in {unit.name for unit in all_units(repos)}


def test_other_languages_get_no_german_units(g2_user: TestUser):
    SeederService(g2_user.repos).seed_units("en-US")
    before = len(all_units(g2_user.repos))
    ensure_german_units(g2_user.repos)
    assert len(all_units(g2_user.repos)) == before


def test_a_zero_denominator_does_not_crash(german: DataMatcher):
    # "1/0" is no fraction: the 1 counts, the rest stays text, and the draft is not lost
    parsed = parse_ingredient("1/0 Tasse Mehl", german.units_by_alias, german.foods_by_alias)
    assert parsed.quantity == 1
