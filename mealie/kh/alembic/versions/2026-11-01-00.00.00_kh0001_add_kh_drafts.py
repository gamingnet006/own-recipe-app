"""KH: add kh_drafts, the first migration of Küchenhelfer's own branch "kh" (D24), for drafts (D18).

Revision ID: kh0001
Revises: 1e69ea7cd45e
Create Date: 2026-11-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0001"
down_revision: str | None = "1e69ea7cd45e"
branch_labels: str | tuple[str, ...] | None = ("kh",)
depends_on: str | tuple[str, ...] | None = None


# jsonb on Postgres, like the model: json there cannot be compared, which Mealie's generic queries do
JSON = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade():
    """Creates kh_drafts with the columns and indexes of mealie/kh/drafts/models.py."""
    op.create_table(
        "kh_drafts",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("group_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("household_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("user_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("source_url_normalized", sa.String(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("original_files", JSON, nullable=False),
        sa.Column("recipe", JSON, nullable=True),
        sa.Column("warnings", JSON, nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("ai_model", sa.String(), nullable=True),
        sa.Column("recipe_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("approved_by", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("approved_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.Column("created_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.Column("update_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("kh_drafts", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_kh_drafts_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_kh_drafts_group_id"), ["group_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_kh_drafts_household_id"), ["household_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_kh_drafts_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_kh_drafts_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_kh_drafts_source_url_normalized"), ["source_url_normalized"], unique=False)
        batch_op.create_index(batch_op.f("ix_kh_drafts_recipe_id"), ["recipe_id"], unique=True)


def downgrade():
    """Drops kh_drafts with its indexes."""
    with op.batch_alter_table("kh_drafts", schema=None) as batch_op:
        indexed = ("recipe_id", "source_url_normalized", "status", "user_id", "household_id", "group_id", "created_at")
        for column in indexed:
            batch_op.drop_index(batch_op.f(f"ix_kh_drafts_{column}"))
    op.drop_table("kh_drafts")
