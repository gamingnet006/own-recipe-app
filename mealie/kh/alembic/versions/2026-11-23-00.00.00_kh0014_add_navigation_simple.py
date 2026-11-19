"""KH: the per-person "simple view" switch (D79).

Revision ID: kh0014
Revises: kh0013
Create Date: 2026-11-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "kh0014"
down_revision: str | None = "kh0013"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    """Adds the switch to the navigation table, off for everyone."""
    with op.batch_alter_table("kh_user_navigation") as batch_op:
        batch_op.add_column(sa.Column("simple", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    """Drops the column again."""
    with op.batch_alter_table("kh_user_navigation") as batch_op:
        batch_op.drop_column("simple")
