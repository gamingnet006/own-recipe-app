"""KH: add kh_drafts.source_note, the file name of a recording (P7.3).

Revision ID: kh0006
Revises: kh0005
Create Date: 2026-11-11 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "kh0006"
down_revision: str | None = "kh0005"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    """Adds the column; drafts that exist stay as they are."""
    with op.batch_alter_table("kh_drafts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("source_note", sa.String(), nullable=True))


def downgrade():
    """Drops the column again."""
    with op.batch_alter_table("kh_drafts", schema=None) as batch_op:
        batch_op.drop_column("source_note")
