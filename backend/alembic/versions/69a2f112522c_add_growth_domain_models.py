"""add_growth_domain_models

Revision ID: 69a2f112522c
Revises: db3251228ebb
Create Date: 2026-05-12 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '69a2f112522c'
down_revision: Union[str, None] = 'db3251228ebb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === growth_campaigns ===
    op.create_table(
        'growth_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('campaign_type', sa.Enum('seo_content', 'social_organic', 'lead_magnet', 'referral_viral', 'educational_nurture', 'ugc_campaign', 'community_engagement', name='growthcampaigntype'), nullable=False),
        sa.Column('status', sa.Enum('draft', 'active', 'paused', 'completed', name='growthcampaignstatus'), nullable=False, server_default='draft'),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('target_audience', sa.Text(), nullable=True),
        sa.Column('content_pillars', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('tone_of_voice', sa.String(100), nullable=False, server_default='educational'),
        sa.Column('leads_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('revenue_attributed', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('content_published', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('engagement_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('metrics_snapshot', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )
    op.create_index('ix_growth_campaigns_business_type', 'growth_campaigns', ['business_id', 'campaign_type'])
    op.create_index('ix_growth_campaigns_business_status', 'growth_campaigns', ['business_id', 'status'])

    # === lead_magnets ===
    op.create_table(
        'lead_magnets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('growth_campaigns.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('format', sa.Enum('cheat_sheet', 'template', 'calculator', 'mini_guide', 'quiz', 'audit', 'toolkit', 'checklist', 'ebook', 'video_mini', name='leadmagnetformat'), nullable=False),
        sa.Column('topic', sa.String(200), nullable=False),
        sa.Column('content', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('landing_page_copy', sa.Text(), nullable=True),
        sa.Column('delivery_message', sa.Text(), nullable=True),
        sa.Column('call_to_action', sa.String(200), nullable=True),
        sa.Column('times_delivered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_downloaded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_converted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversion_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('engagement_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('auto_deliver', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('delivery_channel', sa.String(50), nullable=False, server_default='whatsapp'),
        sa.Column('delivery_trigger', sa.String(50), nullable=False, server_default='new_lead'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )
    op.create_index('ix_lead_magnets_business_format', 'lead_magnets', ['business_id', 'format'])
    op.create_index('ix_lead_magnets_business_active', 'lead_magnets', ['business_id', 'is_active'])

    # === inbound_leads ===
    op.create_table(
        'inbound_leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('growth_campaigns.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('lead_magnet_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lead_magnets.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('source_type', sa.Enum('seo', 'social_post', 'lead_magnet', 'referral', 'comment_dm', 'story_reply', 'organic_search', 'direct', 'community', name='inboundleadsource'), nullable=False),
        sa.Column('source_detail', sa.String(200), nullable=True),
        sa.Column('source_campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('growth_campaigns.id', ondelete='SET NULL'), nullable=True),
        sa.Column('referral_code_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('referral_codes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('contact_info', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('nurturing_stage', sa.Enum('new', 'awareness', 'interest', 'consideration', 'evaluation', 'converted', 'dormant', name='nurturingstage'), nullable=False, server_default='new'),
        sa.Column('engagement_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('value_touches_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sales_touches_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('first_touch_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_touch_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_to_deal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('deals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )
    op.create_index('ix_inbound_leads_business_source', 'inbound_leads', ['business_id', 'source_type'])
    op.create_index('ix_inbound_leads_business_stage', 'inbound_leads', ['business_id', 'nurturing_stage'])
    op.create_index('ix_inbound_leads_conversation', 'inbound_leads', ['conversation_id'])

    # === social_proofs ===
    op.create_table(
        'social_proofs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('item_type', sa.Enum('testimonial', 'review', 'case_study', 'rating', 'video_testimonial', 'before_after', 'ugc_photo', 'ugc_video', name='socialprooftype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'auto_approved', name='socialproofstatus'), nullable=False, server_default='pending'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('headline', sa.String(300), nullable=True),
        sa.Column('customer_name', sa.String(255), nullable=True),
        sa.Column('customer_photo_url', sa.String(500), nullable=True),
        sa.Column('media_urls', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('sentiment_score', sa.Numeric(4, 3), nullable=False, server_default='0'),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('key_quotes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('themes_detected', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('used_in_campaigns', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )
    op.create_index('ix_social_proofs_business_type', 'social_proofs', ['business_id', 'item_type'])
    op.create_index('ix_social_proofs_business_status', 'social_proofs', ['business_id', 'status'])
    op.create_index('ix_social_proofs_business_sentiment', 'social_proofs', ['business_id', 'sentiment_score'])

    # === ugc_requests ===
    op.create_table(
        'ugc_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('growth_campaigns.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('request_message', sa.Text(), nullable=False),
        sa.Column('incentive_offered', sa.String(200), nullable=True),
        sa.Column('status', sa.Enum('pending', 'sent', 'received', 'approved', 'rejected', name='ugcrequeststatus'), nullable=False, server_default='pending'),
        sa.Column('response_media_urls', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('social_proof_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('social_proofs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_ugc_requests_business_status', 'ugc_requests', ['business_id', 'status'])
    op.create_index('ix_ugc_requests_order', 'ugc_requests', ['order_id'])

    # === value_sequences ===
    op.create_table(
        'value_sequences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('growth_campaigns.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('topic', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('messages', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('total_duration_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('target_segment', sa.String(50), nullable=False, server_default='cold'),
        sa.Column('target_source', sa.String(50), nullable=True),
        sa.Column('times_started', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversion_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('avg_engagement_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )
    op.create_index('ix_value_sequences_business_active', 'value_sequences', ['business_id', 'is_active'])

    # === value_sequence_enrollments ===
    op.create_table(
        'value_sequence_enrollments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sequence_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('value_sequences.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('inbound_lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inbound_leads.id', ondelete='SET NULL'), nullable=True),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_steps', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('messages_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('messages_read', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('messages_replied', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_engagement_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_to_deal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('deals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_value_enrollments_sequence', 'value_sequence_enrollments', ['sequence_id', 'status'])
    op.create_index('ix_value_enrollments_conversation', 'value_sequence_enrollments', ['conversation_id'])


def downgrade() -> None:
    op.drop_table('value_sequence_enrollments')
    op.drop_table('value_sequences')
    op.drop_table('ugc_requests')
    op.drop_table('social_proofs')
    op.drop_table('inbound_leads')
    op.drop_table('lead_magnets')
    op.drop_table('growth_campaigns')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS growthcampaigntype")
    op.execute("DROP TYPE IF EXISTS growthcampaignstatus")
    op.execute("DROP TYPE IF EXISTS leadmagnetformat")
    op.execute("DROP TYPE IF EXISTS inboundleadsource")
    op.execute("DROP TYPE IF EXISTS nurturingstage")
    op.execute("DROP TYPE IF EXISTS socialprooftype")
    op.execute("DROP TYPE IF EXISTS socialproofstatus")
    op.execute("DROP TYPE IF EXISTS ugcrequeststatus")
