"""KH: kh_account_links (D52): ties a person's extra accounts, one per household, to the person's primary account."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhAccountLink(SqlAlchemyBase, BaseMixins):
    """A linked account (user_id) of the person whose primary account is primary_user_id."""

    __tablename__ = "kh_account_links"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes users through the ORM, which does not know this table
    primary_user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
