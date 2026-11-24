"""KH: language and colour per person and for the installation, and whether a person was asked about intolerances
(wave 2 of 2026-11-24: account language, own colour, intolerance question once per account).

Revision ID: kh0016
Revises: kh0015
Create Date: 2026-11-24 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "kh0016"
down_revision: str | None = "kh0015"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    """Adds the columns empty: no language or colour chosen yet means "follow the device" / "the installation's
    colour"; nobody has been asked about intolerances yet, so everyone is asked once."""
    with op.batch_alter_table("kh_user_navigation") as batch_op:
        batch_op.add_column(sa.Column("locale", sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column("accent", sa.String(length=20), nullable=True))
    with op.batch_alter_table("kh_user_onboarding") as batch_op:
        batch_op.add_column(sa.Column("intolerances_asked", sa.Boolean(), nullable=False, server_default=sa.false()))
    with op.batch_alter_table("kh_account_settings") as batch_op:
        batch_op.add_column(sa.Column("locale", sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column("accent", sa.String(length=20), nullable=True))


def downgrade():
    """Drops the columns again."""
    with op.batch_alter_table("kh_account_settings") as batch_op:
        batch_op.drop_column("accent")
        batch_op.drop_column("locale")
    with op.batch_alter_table("kh_user_onboarding") as batch_op:
        batch_op.drop_column("intolerances_asked")
    with op.batch_alter_table("kh_user_navigation") as batch_op:
        batch_op.drop_column("accent")
        batch_op.drop_column("locale")
