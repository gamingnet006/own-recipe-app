"""KH: kh_duplicate_ignored (D43): pairs of recipes the family chose to keep both of, so the report skips them."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhDuplicateIgnored(SqlAlchemyBase, BaseMixins):
    """One ignored pair; recipe_a is the smaller ID as a string, so (a, b) and (b, a) are one row."""

    __tablename__ = "kh_duplicate_ignored"
    __table_args__ = (sa.UniqueConstraint("recipe_a", "recipe_b"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes groups and recipes through the ORM, which does not know this table
    group_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    recipe_a: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    recipe_b: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("recipes.id", ondelete="CASCADE"), index=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
