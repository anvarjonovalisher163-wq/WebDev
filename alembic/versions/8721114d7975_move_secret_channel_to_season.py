"""move secret channel settings to season, add channel_id to invite_links

Revision ID: 8721114d7975
Revises: 820935712578
Create Date: 2026-09-19 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8721114d7975'
down_revision: Union[str, None] = '820935712578'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('seasons', sa.Column('secret_channel_id', sa.BigInteger(), nullable=True))
    op.add_column('seasons', sa.Column('secret_channel_title', sa.String(length=255), nullable=True))
    op.add_column('invite_links', sa.Column('channel_id', sa.BigInteger(), nullable=True))

    # Hozirgi (joriy faol) mavsum va barcha mavjud taklif havolalari eski
    # global sozlamadagi kanalga tegishli edi - shuni saqlab qolamiz.
    op.execute(
        "UPDATE seasons SET secret_channel_id = (SELECT secret_channel_id FROM settings WHERE id = 1), "
        "secret_channel_title = (SELECT secret_channel_title FROM settings WHERE id = 1) "
        "WHERE is_active = true"
    )
    op.execute(
        "UPDATE invite_links SET channel_id = (SELECT secret_channel_id FROM settings WHERE id = 1)"
    )

    op.drop_column('settings', 'secret_channel_id')
    op.drop_column('settings', 'secret_channel_title')


def downgrade() -> None:
    op.add_column('settings', sa.Column('secret_channel_title', sa.String(length=255), nullable=True))
    op.add_column('settings', sa.Column('secret_channel_id', sa.BigInteger(), nullable=True))
    op.execute(
        "UPDATE settings SET secret_channel_id = (SELECT secret_channel_id FROM seasons WHERE is_active = true LIMIT 1), "
        "secret_channel_title = (SELECT secret_channel_title FROM seasons WHERE is_active = true LIMIT 1) "
        "WHERE id = 1"
    )
    op.drop_column('invite_links', 'channel_id')
    op.drop_column('seasons', 'secret_channel_title')
    op.drop_column('seasons', 'secret_channel_id')
