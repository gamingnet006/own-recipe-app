"""KH: reads and writes the AI providers' place and state in kh_ai_provider_state (D39)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.ai.models import KhAiProviderState

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
