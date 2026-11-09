"""KH: add kh_food_nutrition, kh_recipe_allergen, kh_user_allergies and kh_substitution (nutrition, allergens, D44).

Revision ID: kh0005
Revises: kh0004
Create Date: 2026-11-10 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0005"
down_revision: str | None = "kh0004"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime

# table -> its columns that need an index (the unique ones carry their own)
INDEXES = {
    "kh_food_nutrition": [],
    "kh_recipe_allergen": [],
    "kh_user_allergies": [],
    "kh_substitution": ["household_id"],
}


def common() -> list[sa.Column]:
    """The ID and Mealie's created_at and update_at, which all tables have."""
    return [
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
    ]


def upgrade():
    """Creates the four tables with the columns, constraints and indexes of the models in mealie/kh/nutrition and
    mealie/kh/allergens."""
    columns = {
        "kh_food_nutrition": [
            sa.Column("food_id", GUID(), nullable=False),
            sa.Column("bls_code", sa.String(), nullable=True),
            sa.Column("confirmed", sa.Boolean(), nullable=False),
            sa.Column("piece_grams", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(["food_id"], ["ingredient_foods.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("food_id"),
        ],
        "kh_recipe_allergen": [
            sa.Column("recipe_id", GUID(), nullable=False),
            sa.Column("allergen", sa.String(), nullable=False),
            sa.Column("present", sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("recipe_id", "allergen"),
        ],
        "kh_user_allergies": [
            sa.Column("user_id", GUID(), nullable=False),
            sa.Column("allergens", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("user_id"),
        ],
        "kh_substitution": [
            sa.Column("household_id", GUID(), nullable=False),
            sa.Column("match", sa.String(), nullable=False),
            sa.Column("replacement", sa.String(), nullable=False),
            sa.Column("allergen", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        ],
    }
    for table, table_columns in columns.items():
        op.create_table(table, *common(), *table_columns, sa.PrimaryKeyConstraint("id"))
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.create_index(batch_op.f(f"ix_{table}_created_at"), ["created_at"], unique=False)
            for column in INDEXES[table]:
                batch_op.create_index(batch_op.f(f"ix_{table}_{column}"), [column], unique=False)


def downgrade():
    """Drops the four tables with their indexes."""
    for table, indexed in INDEXES.items():
        with op.batch_alter_table(table, schema=None) as batch_op:
            for column in [*indexed, "created_at"]:
                batch_op.drop_index(batch_op.f(f"ix_{table}_{column}"))
        op.drop_table(table)
