"""KH: tests for the start page's season row (D80): foods match as whole words, the recipe with more in-season
foods comes first, at most eight show, nothing without terms, and 403 while the add-on is off."""

from collections.abc import Callable, Generator

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.addons.models import KhHouseholdAddons
from mealie.kh.addons.schemas import AddonFlags
from mealie.kh.addons.service import save_flags
from tests.kh.nutrition.helpers import new_recipe
from tests.utils.fixture_schemas import TestUser

SEASON = "/api/kh/recipes/season"


@pytest.fixture
def season(unique_user: TestUser) -> Generator[Callable[[bool], None]]:
    """Switches the add-on for one test; the household's row is removed afterwards."""

    def switch(on: bool) -> None:
        save_flags(unique_user.repos.session, unique_user.household_id, AddonFlags(season=on))

    yield switch
    unique_user.repos.session.execute(
        sa.delete(KhHouseholdAddons).where(KhHouseholdAddons.household_id == unique_user.household_id)
    )
    unique_user.repos.session.commit()


def ask(api_client: TestClient, user: TestUser, *terms: str) -> list[dict]:
    response = api_client.get(SEASON, params={"food": terms}, headers=user.token)
    assert response.status_code == 200, response.text
    return response.json()["recipes"]


def test_matches_whole_words_and_ranks_by_foods(api_client: TestClient, unique_user: TestUser, season):
    season(True)
    one = new_recipe(api_client, unique_user, [(1, None, "Kürbis", "")])
    two = new_recipe(api_client, unique_user, [(1, None, "Kürbis", ""), (1, None, "Grünkohl", "")])
    new_recipe(api_client, unique_user, [(1, None, "Knoblauch", "")])
    slugs = [recipe["slug"] for recipe in ask(api_client, unique_user, "Kürbis", "Grünkohl", "Lauch")]
    assert slugs == [two["slug"], one["slug"]]
    assert ask(api_client, unique_user, "Lauch") == []


def test_at_most_eight_and_nothing_without_terms(api_client: TestClient, unique_user: TestUser, season):
    season(True)
    for _ in range(9):
        new_recipe(api_client, unique_user, [(1, None, "Spargel", "")])
    assert len(ask(api_client, unique_user, "Spargel")) == 8
    assert ask(api_client, unique_user) == []
    assert ask(api_client, unique_user, "  ") == []


def test_closed_while_off(api_client: TestClient, unique_user: TestUser, season):
    season(False)
    assert api_client.get(SEASON, params={"food": ["Kürbis"]}, headers=unique_user.token).status_code == 403
