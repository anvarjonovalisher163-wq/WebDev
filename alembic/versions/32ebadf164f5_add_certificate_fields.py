"""add certificate fields to users and settings

Revision ID: 32ebadf164f5
Revises: b6bb532
Create Date: 2026-09-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32ebadf164f5'
down_revision: Union[str, None] = '8721114d7975'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('cert_full_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('cert_requested_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('cert_issued_at', sa.DateTime(timezone=True), nullable=True))

    op.add_column('settings', sa.Column('acceptance_text', sa.Text(), nullable=True))
    op.add_column('settings', sa.Column('certificate_subtitle', sa.String(length=255), nullable=True))
    op.add_column('settings', sa.Column('certificate_body_text', sa.Text(), nullable=True))
    op.add_column('settings', sa.Column('certificate_signature_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('settings', 'certificate_signature_name')
    op.drop_column('settings', 'certificate_body_text')
    op.drop_column('settings', 'certificate_subtitle')
    op.drop_column('settings', 'acceptance_text')

    op.drop_column('users', 'cert_issued_at')
    op.drop_column('users', 'cert_requested_at')
    op.drop_column('users', 'cert_full_name')
