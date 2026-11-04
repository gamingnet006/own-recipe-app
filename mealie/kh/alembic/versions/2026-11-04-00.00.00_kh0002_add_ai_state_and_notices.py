"""KH: add kh_ai_provider_state, kh_notices and kh_notice_reads for the AI priority list and the bell (D39).

Revision ID: kh0002
Revises: kh0001
Create Date: 2026-11-04 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0002"
down_revision: str | None = "kh0001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime


def timestamps() -> list[sa.Column]:
    """created_at and update_at, which every table gets from SqlAlchemyBase."""
    return [sa.Column("created_at", NaiveDateTime(), nullable=True), sa.Column("update_at", NaiveDateTime(), nullable=True)]


def upgrade():
    """Creates the three tables with the columns and indexes of mealie/kh/ai/models.py and mealie/kh/notices/models.py."""
    op.create_table(
        "kh_ai_provider_state",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("paused_until", NaiveDateTime(), nullable=True),
        sa.Column("supports_images", sa.Boolean(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "kh_notices",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("group_id", GUID(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("next_provider", sa.String(), nullable=True),
        sa.Column("until", NaiveDateTime(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "kh_notice_reads",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("last_read_at", NaiveDateTime(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("kh_ai_provider_state", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_kh_ai_provider_state_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_kh_ai_provider_state_provider_id"), ["provider_id"], unique=True)
    with op.batch_alter_table("kh_notices", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_kh_notices_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_kh_notices_group_id"), ["group_id"], unique=False)
    with op.batch_alter_table("kh_notice_reads", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_kh_notice_reads_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_kh_notice_reads_user_id"), ["user_id"], unique=True)


def downgrade():
    """Drops the three tables with their indexes."""
    indexes = {
        "kh_notice_reads": ("user_id", "created_at"),
        "kh_notices": ("group_id", "created_at"),
        "kh_ai_provider_state": ("provider_id", "created_at"),
    }
    for table, columns in indexes.items():
        with op.batch_alter_table(table, schema=None) as batch_op:
            for column in columns:
                batch_op.drop_index(batch_op.f(f"ix_{table}_{column}"))
        op.drop_table(table)
