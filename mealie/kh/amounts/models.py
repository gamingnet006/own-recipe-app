"""KH: the amounts tables (D39, D19): what a recipe's ingredient lines need beyond Mealie's fields (the upper end of a
range, never scaling), and amounts in the step text linked to an ingredient. Both hang on the recipe only. Mealie
writes new step IDs on every save, also for bulk changes, so a link names its step by place; ingredients keep their
referenceId."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhIngredientExtra(SqlAlchemyBase, BaseMixins):
    """An ingredient line's range end ("2–3 EL" → 3) or its mark that it never scales (Prise, "etwas")."""

    __tablename__ = "kh_ingredient_extras"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    recipe_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    reference_id: Mapped[GUID] = mapped_column(GUID, unique=True, index=True)  # the ingredient's referenceId
    upper: Mapped[float | None] = mapped_column(sa.Float)
    fixed: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class KhStepAmount(SqlAlchemyBase, BaseMixins):
    """An amount in a step's text, start to end, that is an ingredient's amount or a fraction of it."""

    __tablename__ = "kh_step_amounts"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    recipe_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    step: Mapped[int] = mapped_column(sa.Integer)  # the step's place in the recipe, from 0
    start: Mapped[int] = mapped_column(sa.Integer)
    end: Mapped[int] = mapped_column(sa.Integer)
    text: Mapped[str] = mapped_column(sa.String)  # the text found there, to find it again after an edit
    reference_id: Mapped[GUID] = mapped_column(GUID)
    fraction: Mapped[float] = mapped_column(sa.Float, default=1)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
