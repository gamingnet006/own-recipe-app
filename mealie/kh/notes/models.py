"""KH: the table of the family notes on recipes (D82): one note per recipe per household."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhRecipeNote(SqlAlchemyBase, BaseMixins):
    """What a household wrote on a recipe ("less sugar, the kids like it so"), and who changed it last."""

    __tablename__ = "kh_recipe_notes"
    __table_args__ = (sa.UniqueConstraint("household_id", "recipe_id", name="kh_note_household_recipe"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes these rows through the ORM, which does not know this table
    group_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    household_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("households.id", ondelete="CASCADE"), index=True)
    recipe_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(sa.String(2000))
    # handed to the heir when the person deletes their account (D78); SET NULL, so deleting a user never deletes the
    # household's note
    updated_by: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="SET NULL"), index=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
