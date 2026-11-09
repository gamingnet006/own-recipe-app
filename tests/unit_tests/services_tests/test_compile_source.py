from unittest.mock import AsyncMock, MagicMock

import pytest

import mealie.services.recipe.import_workflow.steps.compile_source as compile_source_module
from mealie.core import exceptions
from mealie.services.recipe.import_workflow.context import WorkflowContext, WorkflowInput, WorkflowOptions
from mealie.services.recipe.import_workflow.steps.compile_source import CompileSourceStep

FACEBOOK_SHARE_URL = "https://www.facebook.com/share/r/1DWziuVHRi/"


def _ctx(url: str) -> WorkflowContext:
    ai = MagicMock()
    ai.provider_settings.audio_provider_enabled = True
    translator = MagicMock()
    translator.t.side_effect = lambda key: key
    return WorkflowContext(
        input=WorkflowInput(url=url),
        options=WorkflowOptions(),
        repos=MagicMock(),
        translator=translator,
        ai=ai,
        on_progress=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_share_url_of_a_video_site_is_refused_without_fetching(monkeypatch: pytest.MonkeyPatch):
    """KH: video links are never downloaded or fetched (D5); the share link is refused at once."""

    async def fail_if_fetched(url: str):
        raise AssertionError("a video link must not be fetched")

    monkeypatch.setattr(compile_source_module, "resilient_fetch", fail_if_fetched)

    with pytest.raises(exceptions.VideoDownloadError):
        await CompileSourceStep().run(_ctx(FACEBOOK_SHARE_URL))
