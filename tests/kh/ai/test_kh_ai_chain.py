"""KH: tests for the AI priority list (D39): providers are asked in order, a failing one is paused by its error,
and the bell gets one notice per change."""

import asyncio
from datetime import timedelta

import httpx
import openai
import pytest
import sqlalchemy as sa
from openai.types.chat import ChatCompletion

from mealie.core.exceptions import RateLimitError
from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.ai import chain
from mealie.kh.ai.chain import ask_ai, used_providers
from mealie.kh.ai.errors import AIUnavailableError
from mealie.kh.ai.state import load_states, save_state
from mealie.kh.notices.models import KhNotice
from mealie.kh.notices.service import notify
from mealie.repos.all_repositories import get_repositories
from mealie.schema.group.ai_providers import AIProviderOut
from mealie.schema.openai.general import OpenAIText
from mealie.services.openai.openai import OpenAINotEnabledException, OpenAIService
from tests.kh.ai.conftest import ANSWER, FakeAI
from tests.utils.fixture_schemas import TestUser

REQUEST = httpx.Request("POST", "https://ai.example/v1/chat/completions")
CONTENT = [{"type": "text", "text": "Wie heißt das Rezept?"}]


def status_error(cls: type[openai.APIStatusError], code: int, headers: dict | None = None):
    """An error of the openai package as a provider's answer with this status raises it."""
    return cls("provider error", response=httpx.Response(code, headers=headers, request=REQUEST), body=None)


async def ask(user: TestUser, *, images: bool = False) -> OpenAIText | None:
    """One request through the priority list, as Mealie's AI service sends it."""
    providers = user.repos.group_ai_providers.get_all()
    return await ask_ai(OpenAIService(user.repos), "prompt", CONTENT, OpenAIText, images=images, providers=providers)


def state(user: TestUser, provider: AIProviderOut):
    """The provider's stored state."""
    return load_states(user.repos.session, [provider.id])[provider.id]


def notices(user: TestUser) -> list[tuple[str, str | None, str | None]]:
    """The group's notices, oldest first, as (kind, provider, next provider)."""
    rows = user.repos.session.execute(
        sa.select(KhNotice).where(KhNotice.group_id == user.group_id).order_by(KhNotice.created_at)
    ).scalars()
    return [(row.kind, row.provider, row.next_provider) for row in rows]


@pytest.mark.asyncio
async def test_second_answers_when_first_has_no_quota(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = status_error(openai.RateLimitError, 429)
    used_providers.set([])
    before = get_utc_now()
    assert await ask(unique_user) == ANSWER
    assert fake_ai_calls.calls == ["A", "B"]
    a = state(unique_user, providers["A"])
    assert a.status == "quota"
    assert before + timedelta(minutes=59) < a.paused_until < get_utc_now() + timedelta(minutes=61)
    assert notices(unique_user) == [("ai_quota", "A", "B")]
    assert used_providers.get() == ["B (model-b)"]


@pytest.mark.asyncio
async def test_paused_provider_is_skipped(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    save_state(
        unique_user.repos.session, providers["A"].id, status="quota", paused_until=get_utc_now() + timedelta(days=1)
    )
    assert await ask(unique_user) == ANSWER
    assert fake_ai_calls.calls == ["B"]


@pytest.mark.asyncio
async def test_key_error_waits_for_a_test(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = status_error(openai.AuthenticationError, 401)
    await ask(unique_user)
    a = state(unique_user, providers["A"])
    assert (a.status, a.paused_until) == ("key", None)
    await ask(unique_user)
    assert fake_ai_calls.calls == ["A", "B", "B"]


@pytest.mark.asyncio
async def test_short_wait_brings_no_notice(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = status_error(openai.RateLimitError, 429, {"retry-after": "30"})
    assert await ask(unique_user) == ANSWER
    a = state(unique_user, providers["A"])
    assert a.status == "ready"
    assert a.paused_until is not None and a.paused_until < get_utc_now() + timedelta(seconds=31)
    assert notices(unique_user) == []
    assert fake_ai_calls.calls == ["A", "B"]


@pytest.mark.asyncio
async def test_skip_changes_nothing(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = ValueError("broken JSON")
    assert await ask(unique_user) == ANSWER
    a = state(unique_user, providers["A"])
    assert (a.status, a.paused_until) == ("ready", None)
    assert notices(unique_user) == []
    assert fake_ai_calls.calls == ["A", "B"]


@pytest.mark.asyncio
async def test_an_error_about_the_request_is_not_sent_on(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    for error in (
        status_error(openai.BadRequestError, 400),
        openai.LengthFinishReasonError(completion=ChatCompletion.model_construct(choices=[])),
    ):
        fake_ai_calls.calls.clear()
        fake_ai_calls.behavior["A"] = error
        with pytest.raises(type(error)):
            await ask(unique_user)
        assert fake_ai_calls.calls == ["A"]


@pytest.mark.asyncio
async def test_images_only_to_capable_providers(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    session = unique_user.repos.session
    save_state(session, providers["A"].id, supports_images=False)
    save_state(session, providers["C"].id, supports_images=True)
    fake_ai_calls.behavior["C"] = openai.APIConnectionError(request=REQUEST)
    assert await ask(unique_user, images=True) == ANSWER
    assert fake_ai_calls.calls == ["C", "B"]


@pytest.mark.asyncio
async def test_no_provider_reads_images(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    for provider in providers.values():
        save_state(unique_user.repos.session, provider.id, supports_images=False)
    with pytest.raises(AIUnavailableError):
        await ask(unique_user, images=True)
    assert fake_ai_calls.calls == []
    assert notices(unique_user) == [("ai_none", None, None)]


@pytest.mark.asyncio
async def test_all_quota_raises_rate_limit(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    for name in providers:
        fake_ai_calls.behavior[name] = status_error(openai.RateLimitError, 429)
    with pytest.raises(RateLimitError):
        await ask(unique_user)
    assert notices(unique_user) == [
        ("ai_quota", "A", "B"),
        ("ai_quota", "B", "C"),
        ("ai_quota", "C", None),
        ("ai_none", None, None),
    ]


@pytest.mark.asyncio
async def test_all_down_raises_unavailable(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    last = status_error(openai.InternalServerError, 503)
    fake_ai_calls.behavior.update(
        A=openai.APIConnectionError(request=REQUEST), B=status_error(openai.InternalServerError, 500), C=last
    )
    with pytest.raises(AIUnavailableError) as raised:
        await ask(unique_user)
    assert [kind for kind, _, _ in notices(unique_user)] == ["ai_unreachable"] * 3 + ["ai_none"]
    assert raised.value.__cause__ is last  # the last provider's error shows in the log


@pytest.mark.asyncio
async def test_key_error_notice_names_the_next(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = status_error(openai.AuthenticationError, 401)
    await ask(unique_user)
    assert notices(unique_user) == [("ai_key", "A", "B")]


@pytest.mark.asyncio
async def test_missing_model_moves_on(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = status_error(openai.NotFoundError, 404)
    assert await ask(unique_user) == ANSWER
    assert state(unique_user, providers["A"]).status == "model"
    assert notices(unique_user) == [("ai_model", "A", "B")]


@pytest.mark.asyncio
async def test_pause_counts_from_the_failure(
    unique_user: TestUser, providers, fake_ai_calls: FakeAI, monkeypatch: pytest.MonkeyPatch
):
    start = get_utc_now()
    clock = {"now": start}
    monkeypatch.setattr(chain, "get_utc_now", lambda: clock["now"])

    def slow_timeout():
        clock["now"] = start + timedelta(minutes=15)  # the provider kept the request waiting this long
        return openai.APITimeoutError(request=REQUEST)

    fake_ai_calls.behavior["A"] = slow_timeout
    await ask(unique_user)
    assert state(unique_user, providers["A"]).paused_until == start + timedelta(minutes=25)


@pytest.mark.asyncio
async def test_the_list_retries_not_the_openai_package(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    # the list asks the next provider; no provider keeps the package's own retries
    fake_ai_calls.behavior.update(
        A=openai.APIConnectionError(request=REQUEST), B=openai.APIConnectionError(request=REQUEST)
    )
    assert await ask(unique_user) == ANSWER
    assert fake_ai_calls.retries == [0, 0, 0]


@pytest.mark.asyncio
async def test_two_requests_note_one_change(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior["A"] = status_error(openai.RateLimitError, 429)
    assert await asyncio.gather(ask(unique_user), ask(unique_user)) == [ANSWER, ANSWER]
    assert notices(unique_user) == [("ai_quota", "A", "B")]


@pytest.mark.asyncio
async def test_a_request_error_does_not_hide_an_outage(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    fake_ai_calls.behavior.update(
        A=ValueError("broken JSON"),
        B=status_error(openai.RateLimitError, 429),
        C=openai.APIConnectionError(request=REQUEST),
    )
    with pytest.raises(RateLimitError):
        await ask(unique_user)
    assert [kind for kind, _, _ in notices(unique_user)] == ["ai_quota", "ai_unreachable", "ai_none"]


@pytest.mark.asyncio
async def test_request_errors_are_no_outage(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    # every provider fails on just this request (e.g. an answer that is no JSON): no outage, the error goes on
    for name in providers:
        fake_ai_calls.behavior[name] = ValueError("broken JSON")
    with pytest.raises(ValueError):
        await ask(unique_user)
    assert notices(unique_user) == []
    assert fake_ai_calls.calls == ["A", "B", "C"]


@pytest.mark.asyncio
async def test_one_notice_per_outage(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    for name in providers:
        fake_ai_calls.behavior[name] = status_error(openai.RateLimitError, 429)
    for _ in range(2):
        with pytest.raises(RateLimitError):
            await ask(unique_user)
    assert [kind for kind, _, _ in notices(unique_user)] == ["ai_quota"] * 3 + ["ai_none"]
    assert fake_ai_calls.calls == ["A", "B", "C"]


@pytest.mark.asyncio
async def test_recovery_after_the_pause(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    save_state(
        unique_user.repos.session, providers["A"].id, status="quota", paused_until=get_utc_now() - timedelta(minutes=1)
    )
    assert await ask(unique_user) == ANSWER
    assert state(unique_user, providers["A"]).status == "ready"
    assert notices(unique_user) == [("ai_ready", "A", None)]
    assert fake_ai_calls.calls == ["A"]


@pytest.mark.asyncio
async def test_without_providers_ai_is_not_configured(unique_user: TestUser, clean_ai, fake_ai_calls: FakeAI):
    with pytest.raises(OpenAINotEnabledException):
        await ask(unique_user)


def test_old_notices_go(unique_user: TestUser, clean_ai):
    session = unique_user.repos.session
    old = KhNotice(session=session, group_id=unique_user.group_id, kind="ai_none")
    old.created_at = get_utc_now() - timedelta(days=31)
    session.add(old)
    session.commit()
    notify(session, unique_user.group_id, "ai_ready", provider="A")
    assert notices(unique_user) == [("ai_ready", "A", None)]


def expire_pauses(user: TestUser, providers: dict[str, AIProviderOut]) -> None:
    """Lets every provider's pause end, as if its wait were over."""
    for provider in providers.values():
        save_state(user.repos.session, provider.id, paused_until=get_utc_now() - timedelta(seconds=1))


@pytest.mark.asyncio
async def test_an_answer_ends_an_outage(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    # every provider asks for a short wait, so no answer comes although no provider changes its state
    def short():
        return status_error(openai.RateLimitError, 429, {"retry-after": "30"})

    for name in providers:
        fake_ai_calls.behavior[name] = short
    with pytest.raises(AIUnavailableError):
        await ask(unique_user)
    expire_pauses(unique_user, providers)
    fake_ai_calls.behavior.clear()
    assert await ask(unique_user) == ANSWER
    for name in providers:
        fake_ai_calls.behavior[name] = short
    expire_pauses(unique_user, providers)
    with pytest.raises(AIUnavailableError):
        await ask(unique_user)
    assert notices(unique_user) == [("ai_none", None, None), ("ai_ready", "A", None), ("ai_none", None, None)]


@pytest.mark.asyncio
async def test_a_change_during_an_outage_brings_no_second_outage(
    unique_user: TestUser, providers, fake_ai_calls: FakeAI
):
    for name in providers:
        fake_ai_calls.behavior[name] = status_error(openai.RateLimitError, 429)
    with pytest.raises(RateLimitError):
        await ask(unique_user)
    # A's pause ends and now it cannot be reached; B and C are still paused
    save_state(unique_user.repos.session, providers["A"].id, paused_until=get_utc_now() - timedelta(seconds=1))
    fake_ai_calls.behavior["A"] = openai.APIConnectionError(request=REQUEST)
    with pytest.raises(RateLimitError):
        await ask(unique_user)
    assert [kind for kind, _, _ in notices(unique_user)] == ["ai_quota"] * 3 + ["ai_none", "ai_unreachable"]


@pytest.mark.asyncio
async def test_quota_back_after_a_short_wait_is_noted(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    save_state(
        unique_user.repos.session, providers["A"].id, status="quota", paused_until=get_utc_now() - timedelta(minutes=1)
    )
    fake_ai_calls.behavior["A"] = status_error(openai.RateLimitError, 429, {"retry-after": "30"})
    assert await ask(unique_user) == ANSWER
    assert notices(unique_user) == [("ai_ready", "A", None)]


@pytest.mark.asyncio
async def test_a_quota_unfit_for_the_request_is_no_quota(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    # A cannot read photos: its used-up quota says nothing about a photo the readers could not take
    save_state(
        unique_user.repos.session,
        providers["A"].id,
        status="quota",
        paused_until=get_utc_now() + timedelta(hours=1),
        supports_images=False,
    )
    for name in ("B", "C"):
        fake_ai_calls.behavior[name] = openai.APIConnectionError(request=REQUEST)
    with pytest.raises(AIUnavailableError):
        await ask(unique_user, images=True)


@pytest.mark.asyncio
async def test_a_repository_without_group_is_refused(unique_user: TestUser, providers, fake_ai_calls: FakeAI):
    # without a group Mealie's repositories see every group's providers, with their keys
    service = OpenAIService(get_repositories(unique_user.repos.session, group_id=None))
    with pytest.raises(ValueError):
        await service.get_response("p", "m", response_schema=OpenAIText)
    assert fake_ai_calls.calls == []
