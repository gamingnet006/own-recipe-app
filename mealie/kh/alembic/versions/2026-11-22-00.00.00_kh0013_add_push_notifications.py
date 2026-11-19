"""KH: web push devices and each person's notification choices (D75).

Revision ID: kh0013
Revises: kh0012
Create Date: 2026-11-22 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0013"
down_revision: str | None = "kh0012"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime


def upgrade():
    """Creates both tables, empty: without rows nobody gets a notification."""
    op.create_table(
        "kh_push_subscriptions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("endpoint", sa.String(), nullable=False),
        sa.Column("p256dh", sa.String(), nullable=False),
        sa.Column("auth", sa.String(), nullable=False),
        sa.Column("user_agent", sa.String(), nullable=False),
        sa.Column("last_ok_at", NaiveDateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint"),
    )
    op.create_index("ix_kh_push_subscriptions_user_id", "kh_push_subscriptions", ["user_id"])
    op.create_table(
        "kh_notification_settings",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("toggles", sa.JSON(), nullable=False),
        sa.Column("evening_time", sa.String(length=5), nullable=False),
        sa.Column("last_evening", sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade():
    """Drops both tables."""
    op.drop_table("kh_notification_settings")
    op.drop_index("ix_kh_push_subscriptions_user_id", table_name="kh_push_subscriptions")
    op.drop_table("kh_push_subscriptions")
