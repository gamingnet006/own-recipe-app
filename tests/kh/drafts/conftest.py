"""KH: stand-ins for the drafts tests: a recorded recognition result instead of a real AI (D23) and a
stored web page instead of the internet."""

import json
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from mealie.schema.recipe.recipe import RecipeDraft
from mealie.services.recipe.ai_recipe_service import AIRecipeService
from mealie.services.scraper import recipe_scraper, scraper

DATA = Path(__file__).parent / "data"


@pytest.fixture
def fake_ai(monkeypatch: pytest.MonkeyPatch) -> Callable[[str | Exception], list[dict[str, Any]]]:
    """Replaces Mealie's AI recognition with a recorded recipe from data/ or an error; the returned
    list collects the keyword arguments of every call."""

    def use(result: str | Exception) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []

        async def build_recipe(self: AIRecipeService, **kwargs: Any) -> RecipeDraft:
            progress = kwargs.pop("on_progress", None)  # the heartbeat; it runs like the workflow's steps do
            if progress:
                await progress("step")
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
    """Replaces the internet with a stored page from data/ (None: a page without recipe data), so Mealie's
    real structured-data reader runs on it."""

    def use(html_file: str | None) -> None:
        html = (DATA / (html_file or "page-no-recipe.html")).read_text()

        async def resilient_fetch(url: str, **kwargs: Any) -> Any:
            return SimpleNamespace(text=html, url=url, via_flaresolverr=True)  # True: no second try via FlareSolverr

        monkeypatch.setattr(recipe_scraper, "resilient_fetch", resilient_fetch)

    return use
