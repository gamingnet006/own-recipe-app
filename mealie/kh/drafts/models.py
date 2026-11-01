"""KH: the kh_drafts table (D18): one row per draft with its source and the recognized recipe. After the
approval the row stays as the recipe's origin."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.datetime import NaiveDateTime
from mealie.db.models._model_utils.guid import GUID

if TYPE_CHECKING:
    from mealie.db.models.users import User


# Postgres gets jsonb: unlike json it can be compared, which Mealie's generic queries do (SELECT DISTINCT)
JSON = sa.JSON().with_variant(JSONB(), "postgresql")


class KhDraft(SqlAlchemyBase, BaseMixins):
    """A recipe on its way in: where it came from, what was recognized and how far the review got."""

    __tablename__ = "kh_drafts"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    # CASCADE: Mealie deletes groups and households through the ORM, which does not know this table
    group_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    household_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("households.id", ondelete="CASCADE"), index=True)
    # SET NULL: a removed family member's drafts and origins stay
    user_id: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    user: Mapped[User | None] = orm.relationship("User", foreign_keys=[user_id])

    status: Mapped[str] = mapped_column(sa.String, index=True)
    source_type: Mapped[str] = mapped_column(sa.String)
    source_url: Mapped[str | None] = mapped_column(sa.String)
    source_url_normalized: Mapped[str | None] = mapped_column(sa.String, index=True)
    source_text: Mapped[str | None] = mapped_column(sa.Text)
    original_files: Mapped[list[str]] = mapped_column(JSON, default=list)
    recipe: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(sa.String)
    ai_model: Mapped[str | None] = mapped_column(sa.String)

    recipe_id: Mapped[GUID | None] = mapped_column(
        GUID, sa.ForeignKey("recipes.id", ondelete="CASCADE"), unique=True, index=True
    )
    approved_by: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[datetime | None] = mapped_column(NaiveDateTime)

    @property
    def user_name(self) -> str:
        """Who added the draft, as the list and the origin badge show it; empty once the account is gone."""
        if self.user is None:
            return ""
        return self.user.full_name or self.user.username or ""

    @auto_init()
    def __init__(self, **_) -> None:
        pass
