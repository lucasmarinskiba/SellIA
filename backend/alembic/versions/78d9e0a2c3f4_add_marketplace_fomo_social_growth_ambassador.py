"""add_marketplace_fomo_social_growth_ambassador

Revision ID: 78d9e0a2c3f4
Revises: 67c2d4e8f1b0
Create Date: 2026-05-20 10:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '78d9e0a2c3f4'
down_revision: Union[str, None] = '67c2d4e8f1b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === marketplace_items ===
    op.create_table(
        'marketplace_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('short_description', sa.String(500), nullable=True),
        sa.Column('category', sa.Enum('TEMPLATE', 'APP', 'SERVICE', 'DIGITAL_PRODUCT', 'PROGRAM', 'BUNDLE', name='marketplacecategory'), nullable=False, index=True),
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('price_usd', sa.Numeric(10, 2), nullable=False),
        sa.Column('compare_price_usd', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('preview_urls', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('demo_url', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('rating_avg', sa.Numeric(2, 1), nullable=False, server_default='0'),
        sa.Column('rating_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('purchase_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_limited', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('stock_remaining', sa.Integer(), nullable=True),
        sa.Column('offer_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === marketplace_purchases ===
    op.create_table(
        'marketplace_purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('marketplace_items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('price_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='completed'),
        sa.Column('delivery_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === fomo_campaigns ===
    op.create_table(
        'fomo_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('campaign_type', sa.String(50), nullable=False),
        sa.Column('headline', sa.String(255), nullable=False),
        sa.Column('subheadline', sa.Text(), nullable=True),
        sa.Column('cta_text', sa.String(100), nullable=False, server_default='Comprar ahora'),
        sa.Column('cta_url', sa.String(500), nullable=True),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_spots', sa.Integer(), nullable=True),
        sa.Column('spots_taken', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accent_color', sa.String(20), nullable=False, server_default='#F97316'),
        sa.Column('emoji', sa.String(10), nullable=True),
        sa.Column('is_dismissible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('target_plan_ids', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('target_user_ids', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('show_on_pages', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === social_proof_events ===
    op.create_table(
        'social_proof_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('user_display_name', sa.String(100), nullable=False),
        sa.Column('user_avatar_url', sa.String(500), nullable=True),
        sa.Column('action_text', sa.String(255), nullable=False),
        sa.Column('item_name', sa.String(255), nullable=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('time_ago_text', sa.String(50), nullable=True),
        sa.Column('is_shown', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shown_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === social_profile_audits ===
    op.create_table(
        'social_profile_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('handle', sa.String(100), nullable=False),
        sa.Column('profile_url', sa.String(500), nullable=True),
        sa.Column('bio_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('engagement_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('consistency_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overall_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('findings', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('recommendations', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === content_calendar_slots ===
    op.create_table(
        'content_calendar_slots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('caption_draft', sa.Text(), nullable=True),
        sa.Column('hashtag_suggestions', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('best_time_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='suggested'),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performance_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === competitor_trackings ===
    op.create_table(
        'competitor_trackings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('competitor_handle', sa.String(100), nullable=False),
        sa.Column('competitor_name', sa.String(255), nullable=True),
        sa.Column('follower_count', sa.Integer(), nullable=True),
        sa.Column('avg_likes', sa.Integer(), nullable=True),
        sa.Column('avg_comments', sa.Integer(), nullable=True),
        sa.Column('post_frequency', sa.String(50), nullable=True),
        sa.Column('top_hashtags', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('content_themes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('user_follower_count', sa.Integer(), nullable=True),
        sa.Column('gap_analysis', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === certification_programs ===
    op.create_table(
        'certification_programs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('slug', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('level', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('requirements', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('badge_image_url', sa.String(500), nullable=True),
        sa.Column('badge_color', sa.String(20), nullable=False, server_default='#F97316'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === user_certifications ===
    op.create_table(
        'user_certifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('program_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('certification_programs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='in_progress'),
        sa.Column('progress_percent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('certificate_id', sa.String(50), nullable=True, unique=True, index=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === public_expert_profiles ===
    op.create_table(
        'public_expert_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('headline', sa.String(255), nullable=False),
        sa.Column('bio', sa.Text(), nullable=False),
        sa.Column('specialty', sa.String(100), nullable=False),
        sa.Column('total_sales_helped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_revenue_helped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('testimonials', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('featured_case_studies', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('social_links', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('displayed_badges', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('contact_clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('public_expert_profiles')
    op.drop_table('user_certifications')
    op.drop_table('certification_programs')
    op.drop_table('competitor_trackings')
    op.drop_table('content_calendar_slots')
    op.drop_table('social_profile_audits')
    op.drop_table('social_proof_events')
    op.drop_table('fomo_campaigns')
    op.drop_table('marketplace_purchases')
    op.drop_table('marketplace_items')
