"""KH: tests for reading a line typed on the shopping page (D60): amount, unit, food and article name."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from mealie.db.models.recipe.ingredient import IngredientFoodModel
from mealie.schema.recipe.recipe_ingredient import IngredientFoodSave
from mealie.services.parser_services._base import DataMatcher
from tests.utils.fixture_schemas import TestUser

PARSE_LINE = "/api/kh/amounts/parse-line"


@pytest.fixture
def group(german: DataMatcher, unique_user: TestUser) -> DataMatcher:
    """The German group with Milch, Petersilie and Eier as foods."""
    known = DataMatcher(unique_user.repos).foods_by_alias
    for name in ("Milch", "Petersilie"):
        if IngredientFoodModel.normalize(name) not in known:
            unique_user.repos.ingredient_foods.create(IngredientFoodSave(name=name, group_id=unique_user.group_id))
    return DataMatcher(unique_user.repos)


def parse(api_client: TestClient, user: TestUser, text: str):
    return api_client.post(PARSE_LINE, json={"text": text}, headers=user.token)


CASES = [  # text, quantity, unit name, food name, name, note
    ("2 Liter Milch", 2, "Liter", "Milch", "Milch", ""),
    ("2 Milch", 2, None, "Milch", "Milch", ""),
    ("Milch 3,5%", None, None, "Milch", "Milch", "3,5 %"),
    ("2 Liter Milch 3,5 %", 2, "Liter", "Milch", "Milch", "3,5 %"),
    ("3 Eier", 3, None, "Ei", "Ei", ""),
    ("Toilettenpapier", None, None, None, "Toilettenpapier", ""),
    ("toilettenpapier 8 Rollen", None, None, None, "Toilettenpapier", "8 Rollen"),
    ("1/2 Bund Petersilie", 0.5, "Bund", "Petersilie", "Petersilie", ""),
]


@pytest.mark.parametrize(("text", "quantity", "unit", "food", "name", "note"), CASES)
def test_typed_lines(
    api_client: TestClient, unique_user: TestUser, group: DataMatcher, text, quantity, unit, food, name, note
):
    answer = parse(api_client, unique_user, text)
    assert answer.status_code == 200
    body = answer.json()
    assert (body["quantity"], body["name"], body["note"]) == (quantity, name, note)
    assert (body["unitId"] is not None, body["foodId"] is not None) == (unit is not None, food is not None)
    if unit:
        assert group.units_by_id[UUID(body["unitId"])].name == unit
    if food:
        assert group.foods_by_id[UUID(body["foodId"])].name == food


def test_an_empty_line_is_refused(api_client: TestClient, unique_user: TestUser):
    assert parse(api_client, unique_user, "").status_code == 422


def test_needs_a_signed_in_user(api_client: TestClient):
    assert api_client.post(PARSE_LINE, json={"text": "Milch"}).status_code == 401


BARE = [  # text, quantity, unit abbreviation to ensure, name, note: in a group without these units and foods
    ("2 Liter Milch 3,5%", 2, "l", "Milch", "3,5 %"),
    ("2 Becher Sahne", 2, None, "Sahne", "Becher"),
    ("Milch 1,5%", None, None, "Milch", "1,5 %"),
    ("Milch 1.5 %", None, None, "Milch", "1,5 %"),
    ("3 Packungen Nudeln", 3, None, "Nudeln", "Packungen"),
    ("500g Hack", 500, "g", "Hack", ""),
    ("1 Kilo Äpfel", 1, "kg", "Äpfel", ""),
    ("10% Rabatt Joghurt", None, None, "Rabatt Joghurt", "10 %"),
    ("Cola 0,5", None, None, "Cola", "0,5"),
]


@pytest.mark.parametrize(("text", "quantity", "abbreviation", "name", "note"), BARE)
def test_a_group_without_the_units_and_foods_gets_no_junk_name(
    api_client: TestClient, unique_user_fn_scoped: TestUser, text, quantity, abbreviation, name, note
):
    body = parse(api_client, unique_user_fn_scoped, text).json()
    assert (body["quantity"], body["unitAbbreviation"], body["name"], body["note"]) == (
        quantity,
        abbreviation,
        name,
        note,
    )
    assert body["unitId"] is None
    assert body["foodId"] is None


@pytest.mark.parametrize("text", ["3,5%", "2 Liter", "250 g 10 %"])
def test_a_line_without_an_article_is_refused(api_client: TestClient, unique_user_fn_scoped: TestUser, text):
    assert parse(api_client, unique_user_fn_scoped, text).status_code == 422
