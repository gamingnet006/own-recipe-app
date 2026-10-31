"""KH: stand-ins for the drafts tests: a recorded recognition result instead of a real AI (D23) and a
stored web page instead of the internet."""

import json
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.kh.drafts import recognize
from mealie.repos.all_repositories import get_repositories
from mealie.schema.recipe.recipe import Recipe
from mealie.services.recipe.ai_recipe_service import AIRecipeService
from mealie.services.scraper import scraper
from tests import utils
from tests.utils import api_routes

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def household_member(
    session: Session, admin_token, api_client: TestClient, unique_user: utils.TestUser
) -> Generator[utils.TestUser]:
    """A second account in unique_user's household, like a family member invited by link."""
    group = api_client.get(api_routes.groups_self, headers=unique_user.token).json()
    household = api_client.get(api_routes.households_self, headers=unique_user.token).json()
    user_data = {
        "fullName": utils.random_string(),
        "username": utils.random_string(),
        "email": utils.random_email(),
        "password": "useruser",
        "group": group["name"],
        "household": household["name"],
        "admin": False,
        "tokens": [],
    }
    assert api_client.post(api_routes.admin_users, json=user_data, headers=admin_token).status_code == 201
    token = utils.login({"username": user_data["email"], "password": "useruser"}, api_client)
    me = api_client.get(api_routes.users_self, headers=token).json()
    yield utils.TestUser(
        user_id=UUID(me["id"]),
        _group_id=UUID(me["groupId"]),
        _household_id=UUID(me["householdId"]),
        token=token,
        email=user_data["email"],
        username=user_data["username"],
        full_name=user_data["fullName"],
        password=user_data["password"],
        repos=get_repositories(session, group_id=UUID(me["groupId"]), household_id=UUID(me["householdId"])),
    )


@pytest.fixture
def fake_ai(monkeypatch: pytest.MonkeyPatch) -> Callable[[str | Exception], list[dict[str, Any]]]:
    """Replaces Mealie's AI recognition with a recorded recipe from data/ or an error; the returned
    list collects the keyword arguments of every call."""

    def use(result: str | Exception) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []

        async def build_recipe(self: AIRecipeService, **kwargs: Any) -> Recipe:
            calls.append(kwargs)
            if isinstance(result, Exception):
                raise result
            recorded = Recipe.model_validate(json.loads((DATA / result).read_text()))
            return await scraper.finalize_scraped_recipe(recorded, self.translator)

        monkeypatch.setattr(AIRecipeService, "build_recipe", build_recipe)
        return calls

    return use


@pytest.fixture
def fake_page(monkeypatch: pytest.MonkeyPatch) -> Callable[[str | None], None]:
    """Replaces fetching a page with a stored one from data/; None stands for a page without recipe data."""

    def use(html_file: str | None) -> None:
        async def create_from_html(url: str, repos: Any, translator: Any, **kwargs: Any):
            if html_file is None:
                raise HTTPException(400, {"details": "BAD_RECIPE_DATA"})
            html = (DATA / html_file).read_text()
            return await scraper.create_from_html(url, repos, translator, html, **kwargs)

        monkeypatch.setattr(recognize, "create_from_html", create_from_html)

    return use
