"""add seasons and referrals.season_id

Revision ID: d8c182aa06b6
Revises: 03d6c1c759e7
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8c182aa06b6'
down_revision: Union[str, None] = '03d6c1c759e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'seasons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('winner_user_id', sa.Integer(), nullable=True),
        sa.Column('winner_referral_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['winner_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_seasons_number'), 'seasons', ['number'], unique=True)
    op.create_index(op.f('ix_seasons_is_active'), 'seasons', ['is_active'], unique=False)

    # Mavjud referrallar buzilmasligi uchun avval 1-mavsumni yaratib, keyin ularni
    # shu mavsumga bog'laymiz.
    op.execute(
        "INSERT INTO seasons (number, name, is_active, started_at) "
        "VALUES (1, '1-mavsum', true, now())"
    )

    op.add_column('referrals', sa.Column('season_id', sa.Integer(), nullable=True))
    op.execute(
        "UPDATE referrals SET season_id = (SELECT id FROM seasons WHERE is_active = true LIMIT 1)"
    )
    op.alter_column('referrals', 'season_id', nullable=False)
    op.create_index(op.f('ix_referrals_season_id'), 'referrals', ['season_id'], unique=False)
    op.create_foreign_key(
        'fk_referrals_season_id', 'referrals', 'seasons', ['season_id'], ['id'], ondelete='RESTRICT'
    )


def downgrade() -> None:
    op.drop_constraint('fk_referrals_season_id', 'referrals', type_='foreignkey')
    op.drop_index(op.f('ix_referrals_season_id'), table_name='referrals')
    op.drop_column('referrals', 'season_id')

    op.drop_index(op.f('ix_seasons_is_active'), table_name='seasons')
    op.drop_index(op.f('ix_seasons_number'), table_name='seasons')
    op.drop_table('seasons')
