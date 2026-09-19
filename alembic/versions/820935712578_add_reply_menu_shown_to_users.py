"""add reply_menu_shown to users

Revision ID: 820935712578
Revises: d8c182aa06b6
Create Date: 2026-09-19 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '820935712578'
down_revision: Union[str, None] = 'd8c182aa06b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('reply_menu_shown', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('users', 'reply_menu_shown', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'reply_menu_shown')
