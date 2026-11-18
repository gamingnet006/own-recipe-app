"""KH: add the onboarding tables for accounts without e-mail (D53).

Revision ID: kh0009
Revises: kh0008
Create Date: 2026-11-18 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0009"
down_revision: str | None = "kh0008"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
    ]


def upgrade():
    """Creates the three tables, empty: without rows nobody is asked for anything."""
    op.create_table(
        "kh_user_onboarding",
        *_base_columns(),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("verified_email", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "kh_account_tokens",
        *_base_columns(),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    with op.batch_alter_table("kh_account_tokens") as batch_op:
        batch_op.create_index(batch_op.f("ix_kh_account_tokens_user_id"), ["user_id"], unique=False)
    op.create_table(
        "kh_account_settings",
        *_base_columns(),
        sa.Column("email_required", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    """Drops the tables again."""
    op.drop_table("kh_account_settings")
    op.drop_table("kh_account_tokens")
    op.drop_table("kh_user_onboarding")
