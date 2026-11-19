"""KH: remember which "Neu in Kochheft" version each person has seen (D69).

Revision ID: kh0011
Revises: kh0010
Create Date: 2026-11-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "kh0011"
down_revision: str | None = "kh0010"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    """Adds the nullable column; without a value a person sees every news card once."""
    with op.batch_alter_table("kh_user_onboarding") as batch_op:
        batch_op.add_column(sa.Column("news_seen", sa.String(length=20), nullable=True))


def downgrade():
    """Drops the column again."""
    with op.batch_alter_table("kh_user_onboarding") as batch_op:
        batch_op.drop_column("news_seen")
