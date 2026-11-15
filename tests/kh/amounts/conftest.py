"""KH: a group for the amounts tests (v0.2 plan 2): Mealie's German units, Kochheft's additions and a few foods,
written here and not taken from real recipes."""

import pytest

from mealie.db.models.recipe.ingredient import IngredientFoodModel
from mealie.kh.amounts.parse import ensure_german_units
from mealie.schema.recipe.recipe_ingredient import IngredientFoodSave
from mealie.services.parser_services._base import DataMatcher
from mealie.services.seeder.seeder_service import SeederService
from tests.kh.drafts.conftest import fake_ai, fake_page  # noqa: F401  the drafts' recorded AI answers and pages
from tests.utils.fixture_schemas import TestUser

FOODS = [("Mehl", None), ("Ei", "Eier"), ("Zwiebel", "Zwiebeln"), ("Zucker", None), ("Salz", None)]


@pytest.fixture
def german(unique_user: TestUser) -> DataMatcher:
    """unique_user's group with Mealie's German units, Kochheft's German additions and the foods above. The group
    lives for the whole test module, so foods are created only once; Mealie's seeder skips units that exist."""
    repos = unique_user.repos
    SeederService(repos).seed_units("de-DE")
    ensure_german_units(repos)
    known = DataMatcher(repos).foods_by_alias
    for name, plural in FOODS:
        if IngredientFoodModel.normalize(name) not in known:
            repos.ingredient_foods.create(
                IngredientFoodSave(name=name, plural_name=plural, group_id=unique_user.group_id)
            )
    return DataMatcher(repos)
