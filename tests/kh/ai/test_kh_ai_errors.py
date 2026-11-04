"""KH: tests for sorting AI provider errors (D39): which failure skips a provider for how long, read from the
errors of the openai package, built here without any network (D23)."""

import subprocess
import sys
from datetime import UTC, datetime, timedelta

import httpx
import openai
import pytest

from mealie.kh.ai.errors import Failure, classify, pause_until, retry_seconds
from mealie.kh.features.settings import KhSettings

S = KhSettings()
NOW = datetime(2026, 11, 4, 8, 0, tzinfo=UTC)
REQUEST = httpx.Request("POST", "https://ai.example/v1/chat/completions")


def status_error(cls: type[openai.APIStatusError], code: int, headers: dict | None = None, body=None):
    """An error of the openai package as a provider's answer with this status raises it."""
    return cls("provider error", response=httpx.Response(code, headers=headers, request=REQUEST), body=body)


def test_long_wait_is_quota():
    assert classify(status_error(openai.RateLimitError, 429, {"retry-after": "3600"}), S) == Failure("quota", 3600)


def test_short_wait_is_no_quota():
    assert classify(status_error(openai.RateLimitError, 429, {"retry-after": "30"}), S) == Failure("short", 30)


def test_gemini_retry_delay_in_a_list_body():
    body = [
        {
            "error": {
                "code": 429,
                "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "33s"}],
            }
        }
    ]
    assert classify(status_error(openai.RateLimitError, 429, body=body), S) == Failure("short", 33)


def test_gemini_daily_quota_is_quota_despite_a_short_delay():
    # Gemini names a short retryDelay even when the day's quota is used up; its QuotaFailure says which quota
    body = [
        {
            "error": {
                "code": 429,
                "status": "RESOURCE_EXHAUSTED",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                        "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}],
                    },
                    {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "33s"},
                ],
            }
        }
    ]
    assert classify(status_error(openai.RateLimitError, 429, body=body), S) == Failure("quota", None)


def test_absurd_waits_are_tamed():
    assert retry_seconds(status_error(openai.RateLimitError, 429, {"retry-after": "inf"})) is None
    assert retry_seconds(status_error(openai.RateLimitError, 429, {"retry-after": "1e30"})) == 86400
    failure = classify(status_error(openai.RateLimitError, 429, {"retry-after": "1e30"}), S)
    assert pause_until(failure, NOW, S) == NOW + timedelta(days=1)


def test_429_without_hint_is_quota():
    assert classify(status_error(openai.RateLimitError, 429), S) == Failure("quota", None)


def test_bodies_never_crash():
    for body in (None, "rate limited", {"error": "x"}, [1, 2]):
        assert retry_seconds(status_error(openai.RateLimitError, 429, body=body)) is None


@pytest.mark.parametrize(
    ("error", "kind"),
    [
        (status_error(openai.AuthenticationError, 401), "key"),
        (status_error(openai.PermissionDeniedError, 403), "key"),
        (status_error(openai.NotFoundError, 404), "model"),
        (status_error(openai.InternalServerError, 503), "unreachable"),
        (openai.APIConnectionError(request=REQUEST), "unreachable"),
        (openai.APITimeoutError(request=REQUEST), "unreachable"),
        (status_error(openai.BadRequestError, 400), "skip"),
        (ValueError("bad json"), "skip"),
    ],
)
def test_kinds(error: Exception, kind: str):
    assert classify(error, S).kind == kind


def test_pauses():
    assert pause_until(Failure("quota"), NOW, S) == NOW + timedelta(minutes=60)
    assert pause_until(Failure("quota", 7200), NOW, S) == NOW + timedelta(hours=2)
    assert pause_until(Failure("unreachable"), NOW, S) == NOW + timedelta(minutes=10)
    assert pause_until(Failure("short", 30), NOW, S) == NOW + timedelta(seconds=30)
    assert pause_until(Failure("key"), NOW, S) is None


def test_payment_required_is_quota():
    # OpenRouter answers 402 once the credit is gone, even for its ":free" models
    assert classify(status_error(openai.APIStatusError, 402), S) == Failure("quota", None)


def test_the_ai_list_leaves_openai_unloaded():
    # Mealie loads the openai package only when it asks an AI: it takes about a second to load, longer on the Pi
    code = (
        "import sys, mealie.repos.repository_factory, mealie.services.recipe.import_workflow.steps.compile_source; "
        "print('openai' in sys.modules)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip().splitlines()[-1] == "False"
