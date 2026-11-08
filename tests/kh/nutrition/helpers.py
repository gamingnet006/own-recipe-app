"""KH: helpers for the nutrition tests (D44): foods, units and recipes with ingredient lines, written here."""

from typing import Any

from fastapi.testclient import TestClient

from mealie.schema.recipe.recipe_ingredient import SaveIngredientFood, SaveIngredientUnit
from tests.utils import api_routes, random_string
from tests.utils.fixture_schemas import TestUser

UNITS = {"g": "Gramm", "kg": "Kilogramm", "ml": "Milliliter", "EL": "Esslöffel", "Prise": "Prise"}


def new_food(user: TestUser, name: str):
    """The group's food NAME; created on first use (a module's group lives for the whole module)."""
    repos = user.repos
    return repos.ingredient_foods.get_one(name, "name") or repos.ingredient_foods.create(
        SaveIngredientFood(name=name, group_id=user.group_id)
    )


def new_unit(user: TestUser, abbreviation: str):
    """The group's unit with this abbreviation (g, kg, ml, EL, Prise); created on first use."""
    repos = user.repos
    name = UNITS[abbreviation]
    return repos.ingredient_units.get_one(name, "name") or repos.ingredient_units.create(
        SaveIngredientUnit(name=name, abbreviation=abbreviation, group_id=user.group_id)
    )


def new_recipe(
    api_client: TestClient,
    user: TestUser,
    lines: list[tuple[float | None, str | None, str | None, str]],
    servings: float | None = None,
    **fields: Any,
) -> dict:
    """A saved recipe with LINES, each (quantity, unit abbreviation, food name, note), and SERVINGS."""
    slug = api_client.post(api_routes.recipes, json={"name": random_string()}, headers=user.token).json()
    recipe = api_client.get(api_routes.recipes_slug(slug), headers=user.token).json()
    recipe["recipeServings"] = servings or 0
    recipe.update(fields)
    recipe["recipeIngredient"] = [
        {
            "quantity": quantity,
            "unit": new_unit(user, unit).model_dump(mode="json", by_alias=True) if unit else None,
            "food": new_food(user, food).model_dump(mode="json", by_alias=True) if food else None,
            "note": note,
        }
        for quantity, unit, food, note in lines
    ]
    response = api_client.put(api_routes.recipes_slug(slug), json=recipe, headers=user.token)
    assert response.status_code == 200, response.text
    return response.json()


def set_can_organize(user: TestUser, value: bool) -> None:
    """Gives or takes the permission to organize group data (foods, tags, categories) of USER."""
    db_user = user.repos.users.get_one(user.user_id)
    assert db_user
    db_user.can_organize = value
    user.repos.users.update(db_user.id, db_user)
