"""KH: sorts an AI provider's error into what the priority list does with it (D39): a short pause, a used-up quota,
an invalid key, a missing model, an unreachable provider, or skipping just this request."""

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from mealie.core.exceptions import OpenAIServiceError, RateLimitError
from mealie.kh.features.settings import KhSettings

FailureKind = Literal["short", "quota", "key", "model", "unreachable", "skip"]

# Gemini names its wait in the error body ("retryDelay": "33s"), others in the retry-after header
RETRY_DELAY = re.compile(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"')
# Gemini's daily quota: its QuotaFailure names a per-day quota, while its retryDelay may still be seconds
PER_DAY_QUOTA = re.compile(r'"quotaId"\s*:\s*"[^"]*PerDay')
MAX_WAIT_SECONDS = 86_400  # a provider asking for a longer wait is waited on for a day at most


def body_text(error: BaseException) -> str:
    """The provider's error body as text to search, whatever its shape (object, list, text or missing)."""
    return json.dumps(getattr(error, "body", None), default=str)


def tame(seconds: float) -> float | None:
    """A provider's wait as usable seconds: none for something that is no number of seconds, at most a day."""
    if not math.isfinite(seconds) or seconds < 0:
        return None
    return min(seconds, MAX_WAIT_SECONDS)


class AIUnavailableError(OpenAIServiceError):
    """No provider of the priority list answered; raised from the last provider's error, if one was asked. As
    Mealie's OpenAIServiceError, Mealie's own import pages say that the AI request failed."""

    def __init__(self) -> None:
        super().__init__("No AI provider answered")


class QuotaUsedUpError(RateLimitError):
    """No provider of the priority list answered and one has used up its quota. As Mealie's RateLimitError a draft
    shows quota_exceeded; its own class lets Mealie's import stop on it (compile_source), not on every rate limit."""


@dataclass(frozen=True)
class Failure:
    """What a provider's error means for the priority list, with the wait it named, if any."""

    kind: FailureKind
    wait_seconds: float | None = None


def retry_seconds(error: BaseException) -> float | None:
    """The wait a provider named for a 429: the retry-after header in seconds, else Gemini's retryDelay in the body,
    which may be an object, a list, text or missing."""
    response = getattr(error, "response", None)
    header = response.headers.get("retry-after") if response is not None else None
    if header:
        try:
            return tame(float(header))
        except ValueError:
            pass  # an HTTP date instead of seconds; the body may still name the wait
    match = RETRY_DELAY.search(body_text(error))
    return tame(float(match.group(1))) if match else None


def classify(error: BaseException, settings: KhSettings) -> Failure:
    """Sorts a provider's error. A 429 with a wait up to ai_short_pause_seconds is only a short pause (a per-minute
    limit), any other 429, and Gemini's per-day quota whatever wait it names, a used-up quota, like a 402 (no credit
    left, e.g. OpenRouter); anything that says nothing about the provider skips just this request."""
    import openai  # here: like Mealie, load the package only when an AI is asked (about a second, longer on the Pi)

    if isinstance(error, openai.RateLimitError):
        if PER_DAY_QUOTA.search(body_text(error)):
            return Failure("quota")
        wait = retry_seconds(error)
        short = wait is not None and wait <= settings.ai_short_pause_seconds
        return Failure("short" if short else "quota", wait)
    if isinstance(error, openai.APIStatusError) and error.status_code == 402:
        return Failure("quota")
    if isinstance(error, openai.AuthenticationError | openai.PermissionDeniedError):
        return Failure("key")
    if isinstance(error, openai.NotFoundError):
        return Failure("model")
    if isinstance(error, openai.APIConnectionError | openai.InternalServerError):  # timeouts are connection errors
        return Failure("unreachable")
    return Failure("skip")


def pause_until(failure: Failure, now: datetime, settings: KhSettings) -> datetime | None:
    """Until when the provider is skipped. A key or model error has no end: it waits for a save or a green test."""
    if failure.kind == "short" and failure.wait_seconds is not None:
        return now + timedelta(seconds=failure.wait_seconds)
    if failure.kind == "quota":
        if failure.wait_seconds is not None:
            return now + timedelta(seconds=failure.wait_seconds)
        return now + timedelta(minutes=settings.ai_quota_pause_minutes)
    if failure.kind == "unreachable":
        return now + timedelta(minutes=settings.ai_down_pause_minutes)
    return None
