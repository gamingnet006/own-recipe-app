"""KH: Mealie's own import must not download or fetch videos either (RECHT.md point 2, D5): yt-dlp is gone and the
import routes answer a link to a video site with a clear error."""

import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import mealie.services.scraper.recipe_scraper as recipe_scraper_module
from mealie.core import exceptions
from mealie.services.openai import transcription
from mealie.services.recipe.import_workflow.context import WorkflowInput
from mealie.services.recipe.import_workflow.steps import compile_source as compile_source_module
from mealie.services.recipe.import_workflow.steps.compile_source import CompileSourceStep
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_yt_dlp_is_not_installed():
    assert importlib.util.find_spec("yt_dlp") is None


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (VIDEO_URL, True),
        ("https://www.instagram.com/reel/abc/", True),
        ("https://www.facebook.com/share/r/1DWziuVHRi/", True),
        ("https://example.com/recipe", False),
        ("", False),
    ],
)
def test_is_video_url_uses_the_host_list(url: str, expected: bool):
    assert transcription.is_video_url(url) is expected


def test_download_video_refuses(tmp_path: Path):
    with pytest.raises(exceptions.VideoDownloadError):
        transcription.download_video(VIDEO_URL, tmp_path)


def test_url_import_refuses_a_video_link_without_fetching_it(
    api_client: TestClient, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
):
    async def fail_if_fetched(url: str):
        raise AssertionError("a video link must not be fetched")

    monkeypatch.setattr(recipe_scraper_module, "resilient_fetch", fail_if_fetched)
    r = api_client.post(api_routes.recipes_create_url, json={"url": VIDEO_URL}, headers=unique_user.token)
    assert r.status_code == 400
    assert "does not download videos" in r.json()["detail"]["message"]


class _Context:
    """Only what CompileSourceStep._compile_page touches."""

    def __init__(self, input: WorkflowInput) -> None:
        self.input = input
        self.resolved_url: str | None = None

    async def report_progress(self, key: str) -> None:
        pass


@pytest.mark.asyncio
async def test_ai_import_refuses_a_video_link_alone(monkeypatch: pytest.MonkeyPatch):
    async def fail_if_fetched(url: str):
        raise AssertionError("a video link must not be fetched")

    monkeypatch.setattr(compile_source_module, "resilient_fetch", fail_if_fetched)
    with pytest.raises(exceptions.VideoDownloadError):
        await CompileSourceStep()._compile_page(_Context(WorkflowInput(url=VIDEO_URL)))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_ai_import_leaves_a_video_link_to_the_text_that_comes_along(monkeypatch: pytest.MonkeyPatch):
    async def fail_if_fetched(url: str):
        raise AssertionError("a video link must not be fetched")

    monkeypatch.setattr(compile_source_module, "resilient_fetch", fail_if_fetched)
    context = _Context(WorkflowInput(url=VIDEO_URL, content="200 g Mehl"))
    assert await CompileSourceStep()._compile_page(context) is None  # type: ignore[arg-type]
