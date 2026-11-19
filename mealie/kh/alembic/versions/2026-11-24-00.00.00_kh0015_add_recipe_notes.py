"""KH: the family note on a recipe (D82).

Revision ID: kh0015
Revises: kh0014
Create Date: 2026-11-24 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0015"
down_revision: str | None = "kh0014"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime


def upgrade():
    """Creates the table, empty: without rows no recipe has a note."""
    op.create_table(
        "kh_recipe_notes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
        sa.Column("group_id", GUID(), nullable=False),
        sa.Column("household_id", GUID(), nullable=False),
        sa.Column("recipe_id", GUID(), nullable=False),
        sa.Column("text", sa.String(length=2000), nullable=False),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id", "recipe_id", name="kh_note_household_recipe"),
    )
    with op.batch_alter_table("kh_recipe_notes") as batch_op:
        for column in ("group_id", "household_id", "recipe_id", "updated_by"):
            batch_op.create_index(batch_op.f(f"ix_kh_recipe_notes_{column}"), [column], unique=False)


def downgrade():
    """Drops the table again."""
    op.drop_table("kh_recipe_notes")
