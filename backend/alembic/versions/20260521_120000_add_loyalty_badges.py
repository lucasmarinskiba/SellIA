"""add_customer_loyalty_badges

Revision ID: 20260521_120000
Revises: social_sellers_20250521
Create Date: 2026-05-21 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260521_120000'
down_revision: Union[str, None] = 'social_sellers_20250521'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === customer_loyalty_badges ===
    op.create_table(
        'customer_loyalty_badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('badge_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.Text(), nullable=True),
        sa.Column('criteria', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === customer_badge_assignments ===
    op.create_table(
        'customer_badge_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('badge_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customer_loyalty_badges.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('awarded_by_seller_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('social_sellers.id', ondelete='SET NULL'), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('customer_badge_assignments')
    op.drop_table('customer_loyalty_badges')
