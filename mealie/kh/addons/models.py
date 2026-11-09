"""KH: kh_household_addons (D46): the household's add-on switches as one JSON row. No row means the defaults, so
installs that existed before the page see no change."""

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhHouseholdAddons(SqlAlchemyBase, BaseMixins):
    """The switches of one household; the Pydantic schema AddonFlags checks the JSON."""

    __tablename__ = "kh_household_addons"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes households through the ORM, which does not know this table
    household_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("households.id", ondelete="CASCADE"), unique=True)
    flags: Mapped[dict[str, Any]] = mapped_column(sa.JSON)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
