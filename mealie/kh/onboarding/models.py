"""KH: tables for accounts without e-mail (D53): first-sign-in flag and verified address, the links mailed to people,
and the admin's "e-mail required" switch."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhUserOnboarding(SqlAlchemyBase, BaseMixins):
    """Per user: must the person still choose a password, which e-mail address has been confirmed, and whether the
    first-sign-in tour is still to be shown (D59)."""

    __tablename__ = "kh_user_onboarding"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes users through the ORM, which does not know this table
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    must_change_password: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    verified_email: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    tour: Mapped[bool] = mapped_column(sa.Boolean, default=False, server_default=sa.false(), nullable=False)  # D59
    news_seen: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)  # newest "Neu in Kochheft" seen (D69)

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class KhAccountToken(SqlAlchemyBase, BaseMixins):
    """A mailed link ("welcome" or "verify"); only the hash of the token is stored."""

    __tablename__ = "kh_account_tokens"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(sa.String, nullable=False)
    token_hash: Mapped[str] = mapped_column(sa.String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(sa.String, nullable=False)

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class KhAccountSettings(SqlAlchemyBase, BaseMixins):
    """The admin's account switches; one row, no row means the defaults."""

    __tablename__ = "kh_account_settings"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    email_required: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
