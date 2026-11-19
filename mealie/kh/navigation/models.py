"""KH: the table of each person's own side menu (D58): which entries they hid."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhUserNavigation(SqlAlchemyBase, BaseMixins):
    """The side-menu entries a user hid, as a JSON list of keys; no row means nothing is hidden."""

    __tablename__ = "kh_user_navigation"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes users through the ORM, which does not know this table
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    hidden: Mapped[list[str]] = mapped_column(sa.JSON)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
