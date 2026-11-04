"""KH: the bell's tables (D39): kh_notices holds a group's notices as kind and values, so the frontend words
them in the reader's language; kh_notice_reads remembers when each user last opened the bell."""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.datetime import NaiveDateTime
from mealie.db.models._model_utils.guid import GUID


class KhNotice(SqlAlchemyBase, BaseMixins):
    """One notice, e.g. kind "ai_quota" for provider "Gemini" until 9:00 with "Groq" next; its time is created_at."""

    __tablename__ = "kh_notices"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes groups through the ORM, which does not know this table
    group_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(sa.String)
    provider: Mapped[str | None] = mapped_column(sa.String)
    next_provider: Mapped[str | None] = mapped_column(sa.String)
    until: Mapped[datetime | None] = mapped_column(NaiveDateTime)

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class KhNoticeRead(SqlAlchemyBase, BaseMixins):
    """When a user last opened the bell; notices after that count as unread."""

    __tablename__ = "kh_notice_reads"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    last_read_at: Mapped[datetime] = mapped_column(NaiveDateTime)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
