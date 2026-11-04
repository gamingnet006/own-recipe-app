"""KH: writes the bell's notices (D39) and keeps a group's notices only for KH_NOTICE_DAYS days."""

from datetime import datetime, timedelta
from typing import Literal

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.features.settings import get_kh_settings
from mealie.kh.notices.models import KhNotice

NoticeKind = Literal["ai_quota", "ai_key", "ai_model", "ai_unreachable", "ai_ready", "ai_none"]


def notify(
    session: Session,
    group_id: UUID4,
    kind: NoticeKind,
    *,
    provider: str | None = None,
    next_provider: str | None = None,
    until: datetime | None = None,
) -> None:
    """Writes a notice for the group's bell and drops the group's notices older than KH_NOTICE_DAYS. Commits right
    away, so a later error in the same request does not roll the notice back."""
    oldest = get_utc_now() - timedelta(days=get_kh_settings().notice_days)
    session.execute(sa.delete(KhNotice).where(KhNotice.group_id == group_id, KhNotice.created_at < oldest))
    notice = KhNotice(
        session=session, group_id=group_id, kind=kind, provider=provider, next_provider=next_provider, until=until
    )
    session.add(notice)
    session.commit()


def newest_kind(session: Session, group_id: UUID4) -> str | None:
    """The kind of the group's newest notice, so "no AI reachable" comes once per outage."""
    return session.execute(
        sa.select(KhNotice.kind).where(KhNotice.group_id == group_id).order_by(KhNotice.created_at.desc()).limit(1)
    ).scalar_one_or_none()
