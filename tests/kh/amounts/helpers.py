"""KH: helpers for the amounts tests (v0.2 plan 2): a draft recognized from a recorded recipe, approved as Mealie's
recipe, and a recipe built from ingredient lines read with the group's units and foods."""

from typing import Any

from fastapi.testclient import TestClient

from mealie.kh.amounts.parse import parse_ingredient
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.schema.recipe.recipe_step import RecipeStep
from mealie.services.parser_services._base import DataMatcher
from tests.kh.drafts.helpers import DRAFTS, get_draft, post_draft
from tests.utils.fixture_schemas import TestUser

AMOUNTS = "/api/kh/amounts"


def recognized(api_client: TestClient, user: TestUser, fake_ai, recipe_file: str = "recipe-amounts.json") -> dict:
    """A text draft recognized from a recorded recipe, as the review gets it."""
    fake_ai(recipe_file)
    draft = post_draft(api_client, user, data={"text": "Ein Testkuchen."}).json()
    return get_draft(api_client, user, draft["id"]).json()


def approve(api_client: TestClient, user: TestUser, draft: dict, **body: Any):
    """POST the draft's approval with BODY, e.g. linkedSteps."""
    return api_client.post(f"{DRAFTS}/{draft['id']}/approve", json=body, headers=user.token)


def approved(api_client: TestClient, user: TestUser, fake_ai, **body: Any) -> dict[str, Any]:
    """The recipe a recognized draft became on approval, as Mealie returns it."""
    slug = approve(api_client, user, recognized(api_client, user, fake_ai), **body).json()["slug"]
    return api_client.get(f"/api/recipes/{slug}", headers=user.token).json()


def amounts_of(api_client: TestClient, user: TestUser, recipe: dict[str, Any]) -> dict[str, Any]:
    """The saved recipe's amounts, as the views get them."""
    return api_client.get(f"{AMOUNTS}/{recipe['id']}", headers=user.token).json()


def build_recipe(german: DataMatcher, lines: list[str], steps: list[str]) -> Recipe:
    """A recipe with LINES read like an import reads them and STEPS as written."""
    ingredients = []
    for line in lines:
        parsed = parse_ingredient(line, german.units_by_alias, german.foods_by_alias)
        ingredients.append(
            RecipeIngredient(quantity=parsed.quantity, unit=parsed.unit, food=parsed.food, note=parsed.note)
        )
    return Recipe(
        name="Testrezept", recipe_ingredient=ingredients, recipe_instructions=[RecipeStep(text=t) for t in steps]
    )
