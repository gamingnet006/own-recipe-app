"""KH: add kh_account_links for switching households (D52).

Revision ID: kh0008
Revises: kh0007
Create Date: 2026-11-17 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0008"
down_revision: str | None = "kh0007"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime


def upgrade():
    """Creates the table, empty: without links nobody sees the switch, so nothing changes for existing installs."""
    op.create_table(
        "kh_account_links",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
        sa.Column("primary_user_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(["primary_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    with op.batch_alter_table("kh_account_links") as batch_op:
        batch_op.create_index(batch_op.f("ix_kh_account_links_primary_user_id"), ["primary_user_id"], unique=False)


def downgrade():
    """Drops the table again."""
    op.drop_table("kh_account_links")
