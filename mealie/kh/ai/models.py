"""KH: the kh_ai_provider_state table (D39): one row per AI provider with its place in the priority list,
whether it is paused and why, and whether its last test read an image."""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.datetime import NaiveDateTime
from mealie.db.models._model_utils.guid import GUID


class KhAiProviderState(SqlAlchemyBase, BaseMixins):
    """A provider's place and state; a provider without a row is last, ready and untested."""

    __tablename__ = "kh_ai_provider_state"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: the row goes with its provider
    provider_id: Mapped[GUID] = mapped_column(
        GUID, sa.ForeignKey("ai_providers.id", ondelete="CASCADE"), unique=True, index=True
    )
    position: Mapped[int] = mapped_column(sa.Integer, default=0)
    status: Mapped[str] = mapped_column(sa.String, default="ready")  # ready, quota, key, model or unreachable
    paused_until: Mapped[datetime | None] = mapped_column(NaiveDateTime)
    supports_images: Mapped[bool | None] = mapped_column(sa.Boolean)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
