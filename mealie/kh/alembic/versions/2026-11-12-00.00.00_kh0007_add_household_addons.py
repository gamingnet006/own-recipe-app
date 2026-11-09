"""KH: add kh_household_addons for the add-ons page (D46).

Revision ID: kh0007
Revises: kh0006
Create Date: 2026-11-12 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "kh0007"
down_revision: str | None = "kh0006"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

GUID = mealie.db.migration_types.GUID
NaiveDateTime = mealie.db.migration_types.NaiveDateTime


def upgrade():
    """Creates the table, empty: a household without a row has the defaults, so nothing changes for existing
    installs."""
    op.create_table(
        "kh_household_addons",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", NaiveDateTime(), nullable=True),
        sa.Column("update_at", NaiveDateTime(), nullable=True),
        sa.Column("household_id", GUID(), nullable=False),
        sa.Column("flags", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id"),
    )


def downgrade():
    """Drops the table again."""
    op.drop_table("kh_household_addons")
