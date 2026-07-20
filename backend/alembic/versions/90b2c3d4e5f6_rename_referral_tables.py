"""rename_referral_tables

Revision ID: 90b2c3d4e5f6
Revises: 89a1b2c3d4e5
Create Date: 2026-05-21 12:20:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '90b2c3d4e5f6'
down_revision: Union[str, None] = '89a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename referral_trackings to user_referral_trackings if exists
    op.execute("ALTER TABLE IF EXISTS referral_trackings RENAME TO user_referral_trackings")

    # Create user_referral_codes if not exists
    op.create_table(
        'user_referral_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('link', sa.String(500), nullable=False),
        sa.Column('total_clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_signups', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_conversions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_revenue_generated', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('total_credits_earned', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('user_referral_codes')
    op.execute("ALTER TABLE IF EXISTS user_referral_trackings RENAME TO referral_trackings")
