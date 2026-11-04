"""KH: the AI priority list (D39): asks the group's providers in their order until one answers, pauses a failing one
as its error says, and leaves a notice in the bell whenever a provider's state changes."""

from contextvars import ContextVar
from dataclasses import replace
from datetime import datetime

from mealie.core.root_logger import get_logger
from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.ai.errors import AIUnavailableError, QuotaUsedUpError, classify, pause_until
from mealie.kh.ai.state import ProviderState, in_order, load_states, save_state
from mealie.kh.features.settings import KhSettings, get_kh_settings
from mealie.kh.notices.service import NoticeKind, newest_kind, notify
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.group.ai_providers import AIProviderOut
from mealie.schema.openai._base import OpenAIBase
from mealie.services.openai.openai import OpenAINotEnabledException, OpenAIService

logger = get_logger()

# The bell's notice for each state a failure leaves a provider in
NOTICE_FOR: dict[str, NoticeKind] = {
    "quota": "ai_quota",
    "key": "ai_key",
    "model": "ai_model",
    "unreachable": "ai_unreachable",
}

# "<name> (<model>)" of the provider that answered last in this request, e.g. for a draft's AI model
used_provider: ContextVar[str | None] = ContextVar("kh_used_provider", default=None)


def candidates(providers: list[AIProviderOut], states: dict, *, images: bool, now: datetime) -> list[AIProviderOut]:
    """The providers to ask, by place, then name; without those waiting for a fix (key, model) or still paused.
    Photos go first to providers whose test read an image, then to untested ones, never to ones that cannot."""

    def usable(provider: AIProviderOut) -> bool:
        state = states[provider.id]
        paused = state.paused_until is not None and state.paused_until > now
        return state.status not in ("key", "model") and not paused

    queue = in_order([p for p in providers if usable(p)], states)
    if not images:
        return queue
    return [p for p in queue if states[p.id].supports_images is True] + [
        p for p in queue if states[p.id].supports_images is None
    ]


async def ask_ai[T: OpenAIBase](
    service: OpenAIService, prompt: str, content: list[dict], response_schema: type[T], *, images: bool
) -> T | None:
    """Sends one request to the group's providers in order until one answers. If none does: when every provider asked
    rejected just this request (skip), the request failed, not the AI, so its error goes on as it is; otherwise raises
    QuotaUsedUpError when one has used up its quota, else AIUnavailableError. Without providers, as Mealie did,
    OpenAINotEnabledException. The list is the retry: only the last provider asked keeps the openai package's own
    retries, as Mealie's single provider had them. Commits the caller's session, so states and notices stay even if
    the request fails."""
    repos = service.repos
    providers = repos.group_ai_providers.get_all()
    if not providers:
        raise OpenAINotEnabledException("No default provider set")
    settings = get_kh_settings()
    states = load_states(repos.session, [p.id for p in providers])
    queue = candidates(providers, states, images=images, now=get_utc_now())
    last_error: Exception | None = None
    request_error: Exception | None = None
    outage = False  # a provider asked failed for its own reasons (quota, key, model, down)
    for index, provider in enumerate(queue):
        later = queue[index + 1 :]
        try:
            answer = await service._get_raw_response(
                prompt, content, response_schema, provider, max_retries=0 if later else None
            )
        except Exception as error:
            last_error = error
            if classify(error, settings).kind == "skip":
                request_error = error
            else:
                outage = True
            next_name = later[0].name if later else None
            states[provider.id] = record_failure(repos, provider, states[provider.id], error, next_name, settings)
            continue
        record_answer(repos, provider, states[provider.id])
        used_provider.set(f"{provider.name} ({provider.model})")
        return answer
    if request_error is not None and not outage:
        raise request_error
    if newest_kind(repos.session, repos.group_id) != "ai_none":
        notify(repos.session, repos.group_id, "ai_none")
    if any(state.status == "quota" for state in states.values()):
        raise QuotaUsedUpError("Every AI provider has used up its quota")
    raise AIUnavailableError(last_error)


def record_failure(
    repos: AllRepositories,
    provider: AIProviderOut,
    state: ProviderState,
    error: Exception,
    next_name: str | None,
    settings: KhSettings,
) -> ProviderState:
    """Pauses the provider as its error says, counted from the failure, since a timeout may have kept the request
    waiting for minutes, and notes a change of the stored state in the bell; returns the new state. An error that
    says nothing about the provider (skip) changes nothing. Logs the error's class and status, never its text."""
    failure = classify(error, settings)
    logger.info(f"KH: AI provider {provider.name}: {type(error).__name__} (HTTP {getattr(error, 'status_code', None)})")
    if failure.kind == "skip":
        return state
    status = "ready" if failure.kind == "short" else failure.kind
    until = pause_until(failure, get_utc_now(), settings)
    before = save_state(repos.session, provider.id, status=status, paused_until=until)
    if status != before and failure.kind != "short":
        kind = NOTICE_FOR[status]
        notify(repos.session, repos.group_id, kind, provider=provider.name, next_provider=next_name, until=until)
    return replace(state, status=status, paused_until=until)


def record_answer(repos: AllRepositories, provider: AIProviderOut, state: ProviderState) -> None:
    """A provider that answered is ready and no longer paused; one whose stored state was a failure gets a notice."""
    if state.status != "ready" or state.paused_until is not None:
        before = save_state(repos.session, provider.id, status="ready", paused_until=None)
        if before != "ready":
            notify(repos.session, repos.group_id, "ai_ready", provider=provider.name)
