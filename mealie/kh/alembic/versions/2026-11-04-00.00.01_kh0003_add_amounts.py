"""KH: add kh_ingredient_extras and kh_step_amounts for the amounts (D39, D19).

Revision ID: kh0003
Revises: kh0002
Create Date: 2026-11-04 00:00:01.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0003"
down_revision: str | None = "kh0002"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime


def common() -> list[sa.Column]:
    """The ID, the recipe and Mealie's created_at and update_at, which both tables have."""
    return [
        sa.Column("id", GUID(), nullable=False),
        sa.Column("recipe_id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
    ]


def upgrade():
    """Creates both tables with the columns and indexes of mealie/kh/amounts/models.py."""
    for table, columns in (
        (
            "kh_ingredient_extras",
            [
                sa.Column("reference_id", GUID(), nullable=False),
                sa.Column("upper", sa.Float(), nullable=True),
                sa.Column("fixed", sa.Boolean(), nullable=False),
            ],
        ),
        (
            "kh_step_amounts",
            [
                sa.Column("step_id", GUID(), nullable=False),
                sa.Column("start", sa.Integer(), nullable=False),
                sa.Column("end", sa.Integer(), nullable=False),
                sa.Column("text", sa.String(), nullable=False),
                sa.Column("reference_id", GUID(), nullable=False),
                sa.Column("fraction", sa.Float(), nullable=False),
            ],
        ),
    ):
        op.create_table(
            table,
            *common(),
            *columns,
            sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.create_index(batch_op.f(f"ix_{table}_created_at"), ["created_at"], unique=False)
            batch_op.create_index(batch_op.f(f"ix_{table}_recipe_id"), ["recipe_id"], unique=False)
    with op.batch_alter_table("kh_ingredient_extras", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_kh_ingredient_extras_reference_id"), ["reference_id"], unique=True)


def downgrade():
    """Drops both tables with their indexes."""
    indexes = {
        "kh_step_amounts": ("recipe_id", "created_at"),
        "kh_ingredient_extras": ("reference_id", "recipe_id", "created_at"),
    }
    for table, columns in indexes.items():
        with op.batch_alter_table(table, schema=None) as batch_op:
            for column in columns:
                batch_op.drop_index(batch_op.f(f"ix_{table}_{column}"))
        op.drop_table(table)
