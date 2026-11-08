"""KH: the nutrition table (D44): which BLS entry a Mealie food means, once per food for the whole group."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhFoodNutrition(SqlAlchemyBase, BaseMixins):
    """A food's BLS entry. bls_code None with confirmed means "no fitting entry"; piece_grams is the food's own weight
    of one piece and goes before the table's."""

    __tablename__ = "kh_food_nutrition"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    food_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("ingredient_foods.id", ondelete="CASCADE"), unique=True)
    bls_code: Mapped[str | None] = mapped_column(sa.String)
    confirmed: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    piece_grams: Mapped[float | None] = mapped_column(sa.Float)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
