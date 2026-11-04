"""KH: the AI priority list (D39): asks the group's providers in their order until one answers, pauses a failing one
as its error says, and leaves a notice in the bell whenever a provider's state changes."""

from contextvars import ContextVar
from dataclasses import replace
from datetime import datetime

from mealie.core.exceptions import RateLimitError
from mealie.core.root_logger import get_logger
from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.ai.errors import AIUnavailableError, classify, pause_until
from mealie.kh.ai.state import ProviderState, load_states, save_state
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

    queue = sorted(filter(usable, providers), key=lambda p: (states[p.id].position, p.name))
    if not images:
        return queue
    return [p for p in queue if states[p.id].supports_images is True] + [
        p for p in queue if states[p.id].supports_images is None
    ]


async def ask_ai[T: OpenAIBase](
    service: OpenAIService, prompt: str, content: list[dict], response_schema: type[T], *, images: bool
) -> T | None:
    """Sends one request to the group's providers in order until one answers. If none does, raises Mealie's
    RateLimitError when one has used up its quota, else AIUnavailableError; without providers, as Mealie did,
    OpenAINotEnabledException."""
    repos = service.repos
    providers = repos.group_ai_providers.get_all()
    if not providers:
        raise OpenAINotEnabledException("No default provider set")
    settings = get_kh_settings()
    states = load_states(repos.session, [p.id for p in providers])
    now = get_utc_now()
    queue = candidates(providers, states, images=images, now=now)
    last_error: Exception | None = None
    for index, provider in enumerate(queue):
        try:
            answer = await service._get_raw_response(prompt, content, response_schema, provider)
        except Exception as error:
            last_error = error
            next_name = queue[index + 1].name if index + 1 < len(queue) else None
            states[provider.id] = record_failure(repos, provider, states[provider.id], error, next_name, now, settings)
            continue
        record_answer(repos, provider, states[provider.id])
        used_provider.set(f"{provider.name} ({provider.model})")
        return answer
    if newest_kind(repos.session, repos.group_id) != "ai_none":
        notify(repos.session, repos.group_id, "ai_none")
    if any(state.status == "quota" for state in states.values()):
        raise RateLimitError("Every AI provider has used up its quota")
    raise AIUnavailableError(last_error)


def record_failure(
    repos: AllRepositories,
    provider: AIProviderOut,
    state: ProviderState,
    error: Exception,
    next_name: str | None,
    now: datetime,
    settings: KhSettings,
) -> ProviderState:
    """Pauses the provider as its error says and notes a change of state in the bell; returns the new state. An error
    that says nothing about the provider (skip) changes nothing. Logs the error's class and status, never its text."""
    failure = classify(error, settings)
    logger.info(f"KH: AI provider {provider.name}: {type(error).__name__} (HTTP {getattr(error, 'status_code', None)})")
    if failure.kind == "skip":
        return state
    status = "ready" if failure.kind == "short" else failure.kind
    until = pause_until(failure, now, settings)
    save_state(repos.session, provider.id, status=status, paused_until=until)
    if status != state.status and failure.kind != "short":
        kind = NOTICE_FOR[status]
        notify(repos.session, repos.group_id, kind, provider=provider.name, next_provider=next_name, until=until)
    return replace(state, status=status, paused_until=until)


def record_answer(repos: AllRepositories, provider: AIProviderOut, state: ProviderState) -> None:
    """A provider that answered is ready and no longer paused; one coming back from a failure gets a notice."""
    if state.status != "ready" or state.paused_until is not None:
        save_state(repos.session, provider.id, status="ready", paused_until=None)
    if state.status != "ready":
        notify(repos.session, repos.group_id, "ai_ready", provider=provider.name)
