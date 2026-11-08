"""KH: the family cookbook's tables (D43): the print settings of a cookbook as JSON, and the mark that a recipe's photo
is ours and may go into a printout. Both hang on Mealie's rows and go with them."""

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhCookbookPrint(SqlAlchemyBase, BaseMixins):
    """The book editor's settings of one cookbook; the Pydantic schema BookSettings checks the JSON."""

    __tablename__ = "kh_cookbook_print"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    cookbook_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("cookbooks.id", ondelete="CASCADE"), unique=True)
    settings: Mapped[dict[str, Any]] = mapped_column(sa.JSON)

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class KhRecipeFlags(SqlAlchemyBase, BaseMixins):
    """Per-recipe marks of ours; today only own_photo ("the photo is ours"), without which no printout shows it."""

    __tablename__ = "kh_recipe_flags"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    recipe_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("recipes.id", ondelete="CASCADE"), unique=True)
    own_photo: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
