"""KH: the table of each person's own view settings: the side-menu entries they hid (D58), the simple view (D79), their
language and their colour (kh0016)."""

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
    simple: Mapped[bool] = mapped_column(sa.Boolean, default=False, server_default=sa.false())
    # the language the person chose (e.g. "de-DE"); None: follow the device (kh0016)
    locale: Mapped[str | None] = mapped_column(sa.String(10), nullable=True)
    # the person's own accent colour key; None: the installation's colour (kh0016)
    accent: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
