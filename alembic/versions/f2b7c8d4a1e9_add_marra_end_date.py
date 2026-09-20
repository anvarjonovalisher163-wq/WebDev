"""add marra_end_date to settings

Revision ID: f2b7c8d4a1e9
Revises: c4f1a9b2e6d3
Create Date: 2026-09-20 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2b7c8d4a1e9'
down_revision: Union[str, None] = 'c4f1a9b2e6d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('settings', sa.Column('marra_end_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('settings', 'marra_end_date')
