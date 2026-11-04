"""KH: sorts an AI provider's error into what the priority list does with it (D39): a short pause, a used-up quota,
an invalid key, a missing model, an unreachable provider, or skipping just this request."""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

import openai

from mealie.kh.features.settings import KhSettings

FailureKind = Literal["short", "quota", "key", "model", "unreachable", "skip"]

# Gemini names its wait in the error body ("retryDelay": "33s"), others in the retry-after header
RETRY_DELAY = re.compile(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"')


class AIUnavailableError(Exception):
    """No provider of the priority list answered; last_error is the last one's error, if any was asked."""

    def __init__(self, last_error: Exception | None = None) -> None:
        super().__init__("No AI provider answered")
        self.last_error = last_error


@dataclass(frozen=True)
class Failure:
    """What a provider's error means for the priority list, with the wait it named, if any."""

    kind: FailureKind
    wait_seconds: float | None = None


def retry_seconds(error: Exception) -> float | None:
    """The wait a provider named for a 429: the retry-after header in seconds, else Gemini's retryDelay in the body,
    which may be an object, a list, text or missing."""
    response = getattr(error, "response", None)
    header = response.headers.get("retry-after") if response is not None else None
    if header:
        try:
            return float(header)
        except ValueError:
            pass  # an HTTP date instead of seconds; the body may still name the wait
    match = RETRY_DELAY.search(json.dumps(getattr(error, "body", None), default=str))
    return float(match.group(1)) if match else None


def classify(error: Exception, settings: KhSettings) -> Failure:
    """Sorts a provider's error. A 429 with a wait up to ai_short_pause_seconds is only a short pause (a per-minute
    limit), any other 429 a used-up quota; anything that says nothing about the provider skips just this request."""
    if isinstance(error, openai.RateLimitError):
        wait = retry_seconds(error)
        short = wait is not None and wait <= settings.ai_short_pause_seconds
        return Failure("short" if short else "quota", wait)
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
