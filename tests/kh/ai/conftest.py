"""KH: stand-ins for the AI list's tests (D39): three providers A, B and C in unique_user's group, and recorded
answers or errors per provider instead of a real AI (D23)."""

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

import pytest
import sqlalchemy as sa

from mealie.kh.ai.models import KhAiProviderState
from mealie.kh.notices.models import KhNotice, KhNoticeRead
from mealie.schema.group.ai_providers import AIProviderOut
from mealie.schema.openai.general import OpenAIText
from mealie.services.openai.openai import OpenAIService
from tests.utils.fixture_schemas import TestUser

ANSWER = OpenAIText(text="ok")


def clear_ai(user: TestUser) -> None:
    """Removes the group's providers with their state, and the group's notices and reads."""
    repos = user.repos
    for provider in repos.group_ai_providers.get_all():
        repos.session.execute(sa.delete(KhAiProviderState).where(KhAiProviderState.provider_id == provider.id))
        repos.group_ai_providers.delete(provider.id)
    repos.session.execute(sa.delete(KhNotice).where(KhNotice.group_id == user.group_id))
    repos.session.execute(sa.delete(KhNoticeRead).where(KhNoticeRead.user_id == user.user_id))
    repos.session.commit()


@pytest.fixture
def clean_ai(unique_user: TestUser) -> Generator[None]:
    """unique_user lives for a whole module: every test starts and ends without providers or notices."""
    clear_ai(unique_user)
    yield
    clear_ai(unique_user)


@pytest.fixture
def providers(unique_user: TestUser, clean_ai) -> dict[str, AIProviderOut]:
    """Providers A, B and C with the models model-a, model-b and model-c, by name."""
    repo = unique_user.repos.group_ai_providers
    return {
        name: repo.create({"name": name, "api_key": "test-key", "model": f"model-{name.lower()}"})
        for name in ("A", "B", "C")
    }


@dataclass
class FakeAI:
    """What each provider answers or raises, by name, and which providers were asked, in order."""

    behavior: dict[str, Any] = field(default_factory=dict)
    calls: list[str] = field(default_factory=list)


@pytest.fixture
def fake_ai_calls(monkeypatch: pytest.MonkeyPatch) -> FakeAI:
    """Replaces the one request to a provider: a provider without behavior answers ANSWER."""
    fake = FakeAI()

    async def get_raw_response(self, prompt, content, response_schema, provider):
        fake.calls.append(provider.name)
        outcome = fake.behavior.get(provider.name, ANSWER)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(OpenAIService, "_get_raw_response", get_raw_response)
    return fake
