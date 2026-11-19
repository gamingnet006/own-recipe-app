"""KH: add each person's own side menu (D58) and the first-sign-in tour flag (D59).

Revision ID: kh0010
Revises: kh0009
Create Date: 2026-11-19 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0010"
down_revision: str | None = "kh0009"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime


def upgrade():
    """Creates the empty navigation table (without a row nothing is hidden) and adds the tour flag, off for everyone."""
    op.create_table(
        "kh_user_navigation",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("hidden", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    with op.batch_alter_table("kh_user_onboarding") as batch_op:
        batch_op.add_column(sa.Column("tour", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    """Drops the table and the column again."""
    with op.batch_alter_table("kh_user_onboarding") as batch_op:
        batch_op.drop_column("tour")
    op.drop_table("kh_user_navigation")
