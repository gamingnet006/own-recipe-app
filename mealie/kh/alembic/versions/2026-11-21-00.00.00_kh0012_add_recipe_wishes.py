"""KH: add the recipe wishes table (D72).

Revision ID: kh0012
Revises: kh0011
Create Date: 2026-11-21 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0012"
down_revision: str | None = "kh0011"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime


def upgrade():
    """Creates the table, empty: without rows nobody has a wish."""
    op.create_table(
        "kh_recipe_wishes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
        sa.Column("group_id", GUID(), nullable=False),
        sa.Column("household_id", GUID(), nullable=False),
        sa.Column("recipe_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id", "recipe_id", "user_id", name="kh_wish_household_recipe_user"),
    )
    with op.batch_alter_table("kh_recipe_wishes") as batch_op:
        for column in ("group_id", "household_id", "recipe_id", "user_id"):
            batch_op.create_index(batch_op.f(f"ix_kh_recipe_wishes_{column}"), [column], unique=False)


def downgrade():
    """Drops the table again."""
    op.drop_table("kh_recipe_wishes")
