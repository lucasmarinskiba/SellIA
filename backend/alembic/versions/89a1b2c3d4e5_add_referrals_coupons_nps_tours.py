"""add_referrals_coupons_nps_tours

Revision ID: 89a1b2c3d4e5
Revises: fcbf51db9f0f
Create Date: 2026-05-20 11:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '89a1b2c3d4e5'
down_revision: Union[str, None] = 'fcbf51db9f0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === referral_trackings ===
    op.create_table(
        'referral_trackings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('referrer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('referred_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('referral_code_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('referral_codes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clicked_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('signed_up_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_purchase_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('reward_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('reward_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === coupons ===
    op.create_table(
        'coupons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('code', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_type', sa.String(20), nullable=False),
        sa.Column('discount_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_discount_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('min_purchase_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('max_uses_per_user', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('applicable_plans', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('applicable_items', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('is_flash_sale', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('flash_sale_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === coupon_usages ===
    op.create_table(
        'coupon_usages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('coupon_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('coupons.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('discount_applied', sa.Numeric(10, 2), nullable=False),
        sa.Column('original_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('final_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === nps_responses === (already exists in some installs)
    # Skipping nps_responses creation — table already exists
    pass

    # === feedback_items ===
    op.create_table(
        'feedback_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('screenshot_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='new'),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === tour_steps ===
    op.create_table(
        'tour_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('tour_id', sa.String(50), nullable=False, index=True),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('target_element', sa.String(255), nullable=True),
        sa.Column('placement', sa.String(20), nullable=False, server_default='bottom'),
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('action_target', sa.String(255), nullable=True),
        sa.Column('delay_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('video_url', sa.String(500), nullable=True),
        sa.Column('accent_color', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )

    # === user_tour_progress ===
    op.create_table(
        'user_tour_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tour_id', sa.String(50), nullable=False, index=True),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_steps', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_skipped', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_from_page', sa.String(255), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('user_tour_progress')
    op.drop_table('tour_steps')
    op.drop_table('feedback_items')
    op.drop_table('nps_responses')
    op.drop_table('coupon_usages')
    op.drop_table('coupons')
    op.drop_table('referral_trackings')
    op.drop_table('referral_codes')
