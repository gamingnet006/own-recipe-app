"""KH: reads and writes the AI providers' place and state in kh_ai_provider_state (D39)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.group.ai_providers import AIProvider, AIProviderSettings
from mealie.kh.ai.errors import classify
from mealie.kh.ai.models import KhAiProviderState
from mealie.kh.features.settings import get_kh_settings
from mealie.schema.group.ai_providers import AIProviderOut

END_POSITION = 10_000  # the place of a provider never ordered: after every ordered one, then by name


@dataclass
class ProviderState:
    """A provider's place in the list, its state, until when it is paused, and whether it reads images."""

    position: int
    status: str
    paused_until: datetime | None
    supports_images: bool | None


def load_states(session: Session, provider_ids: list[UUID4]) -> dict[UUID4, ProviderState]:
    """The state of each provider; one without a row is last, ready and untested."""
    rows = session.execute(
        sa.select(KhAiProviderState).where(KhAiProviderState.provider_id.in_(provider_ids))
    ).scalars()
    found = {
        row.provider_id: ProviderState(row.position, row.status, row.paused_until, row.supports_images) for row in rows
    }
    return {pid: found.get(pid, ProviderState(END_POSITION, "ready", None, None)) for pid in provider_ids}


def save_state(session: Session, provider_id: UUID4, **fields: Any) -> None:
    """Creates or changes the provider's row and commits right away, so a later error in the same request does not
    roll the change back. A new row without a place goes last."""
    row = session.execute(
        sa.select(KhAiProviderState).where(KhAiProviderState.provider_id == provider_id)
    ).scalar_one_or_none()
    if row is None:
        session.add(KhAiProviderState(session=session, provider_id=provider_id, **{"position": END_POSITION, **fields}))
    else:
        for key, value in fields.items():
            setattr(row, key, value)
    session.commit()


def sync_mealie_roles(session: Session, group_id: UUID4) -> None:
    """Points Mealie's default provider at the list's first provider and its image provider at the first one whose
    test read an image, else the first untested one, so Mealie's checks before an AI request pass
    (AIRecipeService._validate_providers). The audio provider stays as chosen."""
    settings = session.execute(
        sa.select(AIProviderSettings).where(AIProviderSettings.group_id == group_id)
    ).scalar_one_or_none()
    if settings is None:
        return
    providers = session.execute(sa.select(AIProvider).where(AIProvider.settings_id == settings.id)).scalars().all()
    states = load_states(session, [p.id for p in providers])
    ordered = sorted(providers, key=lambda p: (states[p.id].position, p.name))
    readers = [p for p in ordered if states[p.id].supports_images is True]
    fitting = readers or [p for p in ordered if states[p.id].supports_images is None]
    settings.default_provider_id = ordered[0].id if ordered else None
    settings.image_provider_id = fitting[0].id if fitting else None
    session.commit()


def record_test(
    session: Session,
    provider: AIProviderOut,
    *,
    error: BaseException | None = None,
    supports_images: bool | None = None,
) -> None:
    """Keeps what a provider test found, for a saved provider tested as saved, not for unsaved edits: a green test
    makes it ready and notes whether it read an image, a rejected key or a missing model pauses it until fixed."""
    saved = session.get(AIProvider, provider.id)
    if saved is None or (saved.base_url, saved.model, saved.api_key) != (
        provider.base_url,
        provider.model,
        provider.api_key,
    ):
        return
    if error is None:
        save_state(session, provider.id, status="ready", paused_until=None, supports_images=supports_images)
    else:
        kind = classify(error, get_kh_settings()).kind
        if kind not in ("key", "model"):
            return  # a timeout or a used-up quota says nothing about the provider's setup
        save_state(session, provider.id, status=kind, paused_until=None)
    sync_mealie_roles(session, saved.group_id)
