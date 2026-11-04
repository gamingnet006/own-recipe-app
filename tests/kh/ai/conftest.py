"""KH: stand-ins for the AI list's tests (D39): three providers A, B and C in unique_user's group, and recorded
answers or errors per provider instead of a real AI (D23)."""

from dataclasses import dataclass, field
from typing import Any

import pytest

from mealie.schema.group.ai_providers import AIProviderOut
from mealie.schema.openai.general import OpenAIText
from mealie.services.openai.openai import OpenAIService
from tests.utils.fixture_schemas import TestUser

ANSWER = OpenAIText(text="ok")


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
