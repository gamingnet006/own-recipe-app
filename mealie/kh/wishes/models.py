"""KH: the table of recipe wishes (D72): who in a household wishes which recipe, since when."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhRecipeWish(SqlAlchemyBase, BaseMixins):
    """One person's wish for one recipe; it is deleted for everybody once the household plans the recipe."""

    __tablename__ = "kh_recipe_wishes"
    __table_args__ = (
        sa.UniqueConstraint("household_id", "recipe_id", "user_id", name="kh_wish_household_recipe_user"),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes these rows through the ORM, which does not know this table
    group_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    household_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("households.id", ondelete="CASCADE"), index=True)
    recipe_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), index=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
