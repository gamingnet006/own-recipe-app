"""KH: the allergen tables (D44): a recipe's corrections, a user's "Ich vertrage nicht" list and a household's
substitution hints."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID


class KhRecipeAllergen(SqlAlchemyBase, BaseMixins):
    """A correction of the rules for one recipe: present False takes a found allergen out, True adds one."""

    __tablename__ = "kh_recipe_allergen"
    __table_args__ = (sa.UniqueConstraint("recipe_id", "allergen"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    recipe_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("recipes.id", ondelete="CASCADE"))
    allergen: Mapped[str] = mapped_column(sa.String)
    present: Mapped[bool] = mapped_column(sa.Boolean)

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class KhUserAllergies(SqlAlchemyBase, BaseMixins):
    """The allergens a user cannot have, as a JSON list of keys."""

    __tablename__ = "kh_user_allergies"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    allergens: Mapped[list[str]] = mapped_column(sa.JSON)

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class KhSubstitution(SqlAlchemyBase, BaseMixins):
    """A household's own hint: an ingredient text that MATCHes an allergen can be REPLACEd by something else."""

    __tablename__ = "kh_substitution"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    household_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("households.id", ondelete="CASCADE"), index=True)
    match: Mapped[str] = mapped_column(sa.String)
    replacement: Mapped[str] = mapped_column(sa.String)
    allergen: Mapped[str] = mapped_column(sa.String)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
