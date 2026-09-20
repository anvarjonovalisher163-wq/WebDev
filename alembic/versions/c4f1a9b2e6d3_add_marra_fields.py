"""add marra (reading challenge) fields to users and settings

Revision ID: c4f1a9b2e6d3
Revises: 32ebadf164f5
Create Date: 2026-09-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4f1a9b2e6d3'
down_revision: Union[str, None] = '32ebadf164f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_marra_participant', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column('users', 'is_marra_participant', server_default=None)

    op.add_column('settings', sa.Column('marra_url', sa.String(length=500), nullable=True))
    op.add_column('settings', sa.Column('marra_reminder_text', sa.Text(), nullable=True))
    op.add_column('settings', sa.Column('marra_reminder_hour', sa.Integer(), nullable=False, server_default='20'))
    op.alter_column('settings', 'marra_reminder_hour', server_default=None)


def downgrade() -> None:
    op.drop_column('settings', 'marra_reminder_hour')
    op.drop_column('settings', 'marra_reminder_text')
    op.drop_column('settings', 'marra_url')

    op.drop_column('users', 'is_marra_participant')
