"""KH: stand-ins for the drafts tests: a recorded recognition result instead of a real AI (D23) and a
stored web page instead of the internet."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException

from mealie.kh.drafts import recognize
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.services.recipe.ai_recipe_service import AIRecipeService
from mealie.services.scraper import scraper

DATA = Path(__file__).parent / "data"


@pytest.fixture
def fake_ai(monkeypatch: pytest.MonkeyPatch) -> Callable[[str | Exception], list[dict[str, Any]]]:
    """Replaces Mealie's AI recognition with a recorded recipe from data/ or an error; the returned
    list collects the keyword arguments of every call."""

    def use(result: str | Exception) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []

        async def build_recipe(self: AIRecipeService, **kwargs: Any) -> RecipeDraft:
            calls.append(kwargs)
            if isinstance(result, Exception):
                raise result
            recorded = RecipeDraft.model_validate(json.loads((DATA / result).read_text()))
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
