"""KH: foods and units for the shopping page (D60): found when the group has them, else made."""

from pydantic import UUID4

from mealie.db.models.recipe.ingredient import IngredientUnitModel
from mealie.kh.amounts.line import find_food
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe_ingredient import (
    IngredientFoodOut,
    IngredientFoodSave,
    IngredientUnitOut,
    IngredientUnitSave,
)
from mealie.services.parser_services._base import DataMatcher

# The units of the amount chips, by abbreviation: what a new unit is called
UNIT_NAMES = {"g": "Gramm", "kg": "Kilogramm", "ml": "Milliliter", "l": "Liter"}


def ensure_food(repos: AllRepositories, name: str, label_id: UUID4 | None) -> IngredientFoodOut:
    """The group's food called NAME (ignoring case and singular or plural), else a new one with LABEL_ID, which the
    caller has checked to belong to the group."""
    food, rest = find_food(name, DataMatcher(repos).foods_by_alias)
    if food and not rest:
        return food
    return repos.ingredient_foods.create(IngredientFoodSave(name=name, label_id=label_id, group_id=repos.group_id))


def ensure_unit(repos: AllRepositories, abbreviation: str) -> IngredientUnitOut:
    """The group's unit with this abbreviation or its usual name (ignoring case), else a new one."""
    units = DataMatcher(repos).units_by_alias
    name = UNIT_NAMES[abbreviation]
    unit = units.get(IngredientUnitModel.normalize(abbreviation)) or units.get(IngredientUnitModel.normalize(name))
    if unit:
        return unit
    return repos.ingredient_units.create(
        IngredientUnitSave(name=name, abbreviation=abbreviation, group_id=repos.group_id)
    )
