"""KH: tables of "Mitteilungen" (D75): the devices a person gets push messages on, and each person's choices."""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.datetime import NaiveDateTime
from mealie.db.models._model_utils.guid import GUID


class KhPushSubscription(SqlAlchemyBase, BaseMixins):
    """One device of a person, as the browser's push service describes it; the endpoint is its address."""

    __tablename__ = "kh_push_subscriptions"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes users through the ORM, which does not know this table
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    endpoint: Mapped[str] = mapped_column(sa.String, unique=True)
    p256dh: Mapped[str] = mapped_column(sa.String)
    auth: Mapped[str] = mapped_column(sa.String)
    user_agent: Mapped[str] = mapped_column(
        sa.String, default=""
    )  # a short label such as "iPhone", for the device list
    last_ok_at: Mapped[datetime | None] = mapped_column(NaiveDateTime, nullable=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class KhNotificationSettings(SqlAlchemyBase, BaseMixins):
    """A person's choices; no row means all notifications are off."""

    __tablename__ = "kh_notification_settings"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    toggles: Mapped[dict] = mapped_column(sa.JSON)  # event name -> on or off
    evening_time: Mapped[str] = mapped_column(sa.String(5), default="18:00")
    last_evening: Mapped[str | None] = mapped_column(sa.String(10), nullable=True)  # ISO date of the last reminder

    @auto_init()
    def __init__(self, **_) -> None:
        pass
