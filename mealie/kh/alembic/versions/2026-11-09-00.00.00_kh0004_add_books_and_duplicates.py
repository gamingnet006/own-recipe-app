"""KH: add kh_cookbook_print, kh_recipe_flags and kh_duplicate_ignored for the family cookbook (D43).

Revision ID: kh0004
Revises: kh0003
Create Date: 2026-11-09 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0004"
down_revision: str | None = "kh0003"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime

# table -> its columns that need an index (the unique ones carry their own)
INDEXES = {
    "kh_cookbook_print": [],
    "kh_recipe_flags": [],
    "kh_duplicate_ignored": ["group_id", "recipe_a", "recipe_b"],
}


def common() -> list[sa.Column]:
    """The ID and Mealie's created_at and update_at, which all tables have."""
    return [
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
    ]


def upgrade():
    """Creates the three tables with the columns, constraints and indexes of the models in mealie/kh/books and
    mealie/kh/duplicates."""
    columns = {
        "kh_cookbook_print": [
            sa.Column("cookbook_id", GUID(), nullable=False),
            sa.Column("settings", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(["cookbook_id"], ["cookbooks.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("cookbook_id"),
        ],
        "kh_recipe_flags": [
            sa.Column("recipe_id", GUID(), nullable=False),
            sa.Column("own_photo", sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("recipe_id"),
        ],
        "kh_duplicate_ignored": [
            sa.Column("group_id", GUID(), nullable=False),
            sa.Column("recipe_a", GUID(), nullable=False),
            sa.Column("recipe_b", GUID(), nullable=False),
            sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["recipe_a"], ["recipes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["recipe_b"], ["recipes.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("recipe_a", "recipe_b"),
        ],
    }
    for table, table_columns in columns.items():
        op.create_table(table, *common(), *table_columns, sa.PrimaryKeyConstraint("id"))
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.create_index(batch_op.f(f"ix_{table}_created_at"), ["created_at"], unique=False)
            for column in INDEXES[table]:
                batch_op.create_index(batch_op.f(f"ix_{table}_{column}"), [column], unique=False)


def downgrade():
    """Drops the three tables with their indexes."""
    for table, indexed in INDEXES.items():
        with op.batch_alter_table(table, schema=None) as batch_op:
            for column in [*indexed, "created_at"]:
                batch_op.drop_index(batch_op.f(f"ix_{table}_{column}"))
        op.drop_table(table)
