"""KH: own recordings (P7.3): keeps an uploaded audio or video file with its draft and has an OpenAI-compatible
Whisper server (the compose service `whisper`, KH_WHISPER_URL) turn it into text. Only the server in KH_WHISPER_URL is
ever contacted; the recording never leaves the house unless that address does."""

import shutil
from pathlib import Path
from typing import BinaryIO

import httpx
from pydantic import UUID4

from mealie.kh.drafts.files import draft_dir
from mealie.kh.drafts.schemas import DraftError
from mealie.kh.features.settings import KhSettings

MEDIA_FILE = "media"  # the recording inside the draft's folder, deleted once it is transcribed
LANGUAGE = "de"
# A long recording on a small host takes minutes; only the wait for the answer is long
TIMEOUT = httpx.Timeout(connect=10, read=1800, write=600, pool=10)
MODEL_PREFIX = "Systran/faster-whisper-"  # the models speaches serves, named by size in the settings
PROFILE_MODELS = {"leicht": "tiny", "normal": "base", "stark": "small", "lokal": "base"}  # D45, PLAN.md section 8
CHUNK = 1024 * 1024
TRANSPORT: httpx.AsyncBaseTransport | None = None  # tests replace the network with a fake


class WhisperError(Exception):
    """The Whisper server could not turn the recording into text; CODE is what the intake shows."""

    def __init__(self, code: DraftError):
        super().__init__(code)
        self.code = code


def whisper_model(settings: KhSettings) -> str:
    """The model to ask for: KH_WHISPER_MODEL (a size like "small" or a full name), else the profile's size."""
    name = settings.whisper_model or PROFILE_MODELS[settings.profile]
    return name if "/" in name else f"{MODEL_PREFIX}{name}"


def media_path(draft_id: UUID4 | str) -> Path:
    """Where a draft's recording is kept."""
    return draft_dir(draft_id) / MEDIA_FILE


def store_media(draft_id: UUID4 | str, source: BinaryIO, max_mb: int) -> None:
    """Copies the upload to the draft's folder in chunks. Raises ValueError("media_too_large") over MAX_MB and
    removes what was written then."""
    path = media_path(draft_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with path.open("wb") as target:
        while chunk := source.read(CHUNK):
            size += len(chunk)
            if size > max_mb * CHUNK:
                target.close()
                shutil.rmtree(path.parent, ignore_errors=True)
                raise ValueError("media_too_large")
            target.write(chunk)


async def _ask(client: httpx.AsyncClient, draft_id: UUID4 | str, filename: str, model: str) -> httpx.Response:
    with media_path(draft_id).open("rb") as recording:
        return await client.post(
            "/v1/audio/transcriptions",
            data={"model": model, "language": LANGUAGE, "response_format": "json"},
            files={"file": (filename, recording)},
        )


async def transcribe(draft_id: UUID4 | str, filename: str, settings: KhSettings) -> str:
    """The text of the draft's recording. A server that does not know the model yet (404) is told to download it
    once and asked again. Raises WhisperError with the code to show."""
    model = whisper_model(settings)
    try:
        async with httpx.AsyncClient(
            base_url=settings.whisper_url or "", transport=TRANSPORT, timeout=TIMEOUT
        ) as client:
            response = await _ask(client, draft_id, filename, model)
            if response.status_code == 404:
                await client.post(f"/v1/models/{model}")
                response = await _ask(client, draft_id, filename, model)
    except httpx.TimeoutException as error:
        raise WhisperError(DraftError.whisper_timeout) from error
    except httpx.TransportError as error:
        raise WhisperError(DraftError.whisper_unreachable) from error
    try:
        return str(response.raise_for_status().json()["text"])
    except (httpx.HTTPStatusError, ValueError, KeyError) as error:
        raise WhisperError(DraftError.whisper_failed) from error
