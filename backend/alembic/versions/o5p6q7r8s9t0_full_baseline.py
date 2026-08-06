"""full_baseline

Revision ID: o5p6q7r8s9t0
Revises: db3251228ebb
Create Date: 2026-08-06 21:00:00.000000+00:00

Consolidated baseline for the entire schema (173 tables). The 43 delta
migrations that follow all assumed a pre-existing schema that was never
actually captured by Alembic (likely created once via
Base.metadata.create_all() in early dev and never backfilled). Rather
than splice per-table baselines into a hand-ordered position in the delta
chain — which turned out to be impossible: some early deltas need tables
only introduced by later deltas, and vice versa, so no single insertion
point works — this single migration creates the full schema in one shot,
letting Alembic's own autogenerate dependency sort order every FK
correctly. The 43 delta migrations after this one become no-ops (their
tables already exist); kept in the chain only for revision-id continuity
and any real column-level changes they still apply.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy
from sqlalchemy.dialects import postgresql
from sqlalchemy import Text
import app.core.encrypted_types


# revision identifiers, used by Alembic.
revision: str = 'o5p6q7r8s9t0'
down_revision: Union[str, None] = 'db3251228ebb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('achievements',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('slug', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('category', sa.Enum('SALES', 'GROWTH', 'CONSISTENCY', 'MASTERY', 'SOCIAL', 'ZEN', 'MILESTONE', 'MISSIONS', name='achievementcategory'), nullable=False),
    sa.Column('tier', sa.Enum('BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', name='achievementtier'), nullable=False),
    sa.Column('requirement_type', sa.String(length=50), nullable=False),
    sa.Column('requirement_value', sa.Integer(), nullable=False),
    sa.Column('requirement_context', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('xp_reward', sa.Integer(), nullable=False),
    sa.Column('garden_reward', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('icon', sa.String(length=100), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=False),
    sa.Column('animation', sa.String(length=50), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_achievements_slug'), 'achievements', ['slug'], unique=True)
    op.create_table('agent_personalities',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('slug', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('emoji', sa.String(length=10), nullable=False),
    sa.Column('tagline', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('expertise', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('color', sa.String(length=20), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_personalities_slug'), 'agent_personalities', ['slug'], unique=True)
    op.create_table('agent_reflections',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('agent_type', sa.String(length=50), nullable=False),
    sa.Column('what_went_well', sa.Text(), nullable=True),
    sa.Column('what_could_improve', sa.Text(), nullable=True),
    sa.Column('customer_insights', sa.Text(), nullable=True),
    sa.Column('future_recommendations', sa.Text(), nullable=True),
    sa.Column('score', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_reflections_conversation_id'), 'agent_reflections', ['conversation_id'], unique=False)
    op.create_table('blocked_ips',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=False),
    sa.Column('reason', sa.String(length=100), nullable=False),
    sa.Column('blocked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blocked_ips_ip_address'), 'blocked_ips', ['ip_address'], unique=True)
    op.create_table('brand_kit_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('brand_name', sa.String(length=255), nullable=False),
    sa.Column('industry', sa.String(length=100), nullable=False),
    sa.Column('colors', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('fonts', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('logo_url', sa.String(length=500), nullable=True),
    sa.Column('assets', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brand_kit_jobs_business_id'), 'brand_kit_jobs', ['business_id'], unique=False)
    op.create_table('causal_analyses',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('deal_outcome', sa.String(length=50), nullable=False),
    sa.Column('surface_reason', sa.Text(), nullable=True),
    sa.Column('root_cause', sa.Text(), nullable=True),
    sa.Column('contributing_factors', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('recommended_fix', sa.Text(), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_causal_analyses_business_id'), 'causal_analyses', ['business_id'], unique=False)
    op.create_index(op.f('ix_causal_analyses_conversation_id'), 'causal_analyses', ['conversation_id'], unique=False)
    op.create_table('chain_of_thought_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('message_id', sa.UUID(), nullable=True),
    sa.Column('thought_steps', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chain_of_thought_logs_conversation_id'), 'chain_of_thought_logs', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_chain_of_thought_logs_message_id'), 'chain_of_thought_logs', ['message_id'], unique=False)
    op.create_table('idempotency_keys',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('resource', sa.String(length=50), nullable=False),
    sa.Column('response_body', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_idempotency_keys_key'), 'idempotency_keys', ['key'], unique=True)
    op.create_index('ix_idempotency_keys_resource_created', 'idempotency_keys', ['resource', 'created_at'], unique=False)
    op.create_table('music_generation_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('genre', sa.String(length=50), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('provider_used', sa.String(length=50), nullable=True),
    sa.Column('file_url', sa.String(length=500), nullable=True),
    sa.Column('file_format', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_music_generation_jobs_business_id'), 'music_generation_jobs', ['business_id'], unique=False)
    op.create_table('objection_patterns',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('pattern_name', sa.String(length=100), nullable=False),
    sa.Column('objection_text', sa.String(length=200), nullable=False),
    sa.Column('root_cause', sa.Text(), nullable=True),
    sa.Column('frequency_count', sa.Integer(), nullable=False),
    sa.Column('frequency_percent', sa.Float(), nullable=False),
    sa.Column('overcome_count', sa.Integer(), nullable=False),
    sa.Column('overcome_rate', sa.Float(), nullable=False),
    sa.Column('affected_segments', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('recommended_response', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_objection_patterns_business_id'), 'objection_patterns', ['business_id'], unique=False)
    op.create_table('role_permissions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('resource', sa.String(length=100), nullable=False),
    sa.Column('action', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_permissions_role'), 'role_permissions', ['role'], unique=False)
    op.create_index('ix_role_permissions_role_resource', 'role_permissions', ['role', 'resource'], unique=False)
    op.create_table('security_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('blocked_countries', sa.Text(), nullable=True),
    sa.Column('require_turnstile', sa.Boolean(), nullable=False),
    sa.Column('require_2fa_for_admins', sa.Boolean(), nullable=False),
    sa.Column('alert_on_new_device', sa.Boolean(), nullable=False),
    sa.Column('alert_on_failed_login', sa.Boolean(), nullable=False),
    sa.Column('alert_on_malware', sa.Boolean(), nullable=False),
    sa.Column('max_distance_km', sa.Float(), nullable=True),
    sa.Column('alert_on_geofence', sa.Boolean(), nullable=False),
    sa.Column('hibp_api_key', sa.String(length=255), nullable=True),
    sa.Column('alert_on_breach', sa.Boolean(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('security_webhooks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('url', sa.Text(), nullable=False),
    sa.Column('platform', sa.String(length=20), nullable=False),
    sa.Column('secret', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('events', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('semantic_cache_embeddings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('query_text', sa.Text(), nullable=False),
    sa.Column('query_embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=False),
    sa.Column('response_text', sa.Text(), nullable=False),
    sa.Column('model_used', sa.String(length=100), nullable=False),
    sa.Column('hit_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('session_nonces',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_hash', sa.String(length=255), nullable=False),
    sa.Column('nonce', sa.String(length=64), nullable=False),
    sa.Column('rotated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_session_nonces_session_hash'), 'session_nonces', ['session_hash'], unique=True)
    op.create_table('subscription_plans',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('slug', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('price_monthly_ars', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('price_yearly_ars', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('price_monthly_usd', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('price_yearly_usd', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('price_monthly_latam_usd', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('price_yearly_latam_usd', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('limits', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('features', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('billing_cycle_options', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('target_regions', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('trial_days', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_plans_slug'), 'subscription_plans', ['slug'], unique=True)
    op.create_table('system_improvements',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('affected_modules', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('implementation_details', sa.Text(), nullable=True),
    sa.Column('difficulty', sa.String(length=20), nullable=True),
    sa.Column('estimated_hours', sa.Integer(), nullable=True),
    sa.Column('target_plan', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('feature_flag_name', sa.String(length=100), nullable=True),
    sa.Column('ml_model_accuracy_before', sa.Float(), nullable=True),
    sa.Column('ml_model_accuracy_after', sa.Float(), nullable=True),
    sa.Column('source_feedback_ids', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('source_health_report_id', sa.UUID(), nullable=True),
    sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reverted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_improvements_feature_flag_name'), 'system_improvements', ['feature_flag_name'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('email_verified', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_failed_login', sa.DateTime(timezone=True), nullable=True),
    sa.Column('totp_secret', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('is_2fa_enabled', sa.Boolean(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_device_fingerprint', sa.String(length=64), nullable=True),
    sa.Column('country_code', sa.String(length=2), nullable=False),
    sa.Column('detected_country', sa.String(length=2), nullable=True),
    sa.Column('preferred_currency', sa.String(length=3), nullable=False),
    sa.Column('timezone', sa.String(length=50), nullable=False),
    sa.Column('tax_id', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('billing_address', app.core.encrypted_types.EncryptedJSONB(), nullable=False),
    sa.Column('payment_methods', app.core.encrypted_types.EncryptedJSONB(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('video_generation_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('platform', sa.String(length=20), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('provider_used', sa.String(length=50), nullable=True),
    sa.Column('video_url', sa.String(length=500), nullable=True),
    sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
    sa.Column('script', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_generation_jobs_business_id'), 'video_generation_jobs', ['business_id'], unique=False)
    op.create_table('voice_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('voice_id', sa.String(length=100), nullable=False),
    sa.Column('tts_provider', sa.String(length=20), nullable=False),
    sa.Column('stt_provider', sa.String(length=20), nullable=False),
    sa.Column('language', sa.String(length=10), nullable=False),
    sa.Column('greeting_message', sa.Text(), nullable=False),
    sa.Column('max_call_duration', sa.Integer(), nullable=False),
    sa.Column('allowed_hours_start', sa.Time(), nullable=False),
    sa.Column('allowed_hours_end', sa.Time(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voice_configs_business_id'), 'voice_configs', ['business_id'], unique=True)
    op.create_table('webhook_event_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('provider', sa.String(length=20), nullable=False),
    sa.Column('event_id', sa.String(length=100), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_event_logs_event_id'), 'webhook_event_logs', ['event_id'], unique=False)
    op.create_index('ix_webhook_event_logs_provider_event', 'webhook_event_logs', ['provider', 'event_id'], unique=True)
    op.create_table('brand_assets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('job_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('asset_type', sa.String(length=50), nullable=False),
    sa.Column('file_url', sa.String(length=500), nullable=False),
    sa.Column('config', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['brand_kit_jobs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brand_assets_business_id'), 'brand_assets', ['business_id'], unique=False)
    op.create_index(op.f('ix_brand_assets_job_id'), 'brand_assets', ['job_id'], unique=False)
    op.create_table('breach_check_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('breaches_found', sa.Integer(), nullable=False),
    sa.Column('breach_names', sa.Text(), nullable=True),
    sa.Column('checked_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_breach_check_logs_user_id'), 'breach_check_logs', ['user_id'], unique=False)
    op.create_table('businesses',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('type', sa.Enum('SERVICES', 'GOODS', 'DIGITAL', 'MIXED', name='businesstype'), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_businesses_user_id'), 'businesses', ['user_id'], unique=False)
    op.create_table('chargeback_alerts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('payment_provider', sa.String(length=50), nullable=False),
    sa.Column('transaction_id', sa.String(length=255), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('evidence_json', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chargeback_alerts_user_id'), 'chargeback_alerts', ['user_id'], unique=False)
    op.create_table('computer_use_proxy_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('proxy_type', sa.Enum('http', 'https', 'socks5', name='proxy_type'), nullable=True),
    sa.Column('host', sa.String(length=255), nullable=False),
    sa.Column('port', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=True),
    sa.Column('password_encrypted', sa.Text(), nullable=True),
    sa.Column('rotation_url', sa.String(length=2048), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('use_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_proxy_configs_user_id'), 'computer_use_proxy_configs', ['user_id'], unique=False)
    op.create_table('daily_mood_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('mood', sa.String(length=20), nullable=False),
    sa.Column('energy_level', sa.Integer(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('ai_response', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_mood_logs_user_id'), 'daily_mood_logs', ['user_id'], unique=False)
    op.create_index('ix_mood_logs_user_date', 'daily_mood_logs', ['user_id', 'created_at'], unique=False)
    op.create_table('email_otps',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('code_hash', sa.String(length=255), nullable=False),
    sa.Column('purpose', sa.String(length=50), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_used', sa.Boolean(), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_otps_user_id'), 'email_otps', ['user_id'], unique=False)
    op.create_table('feature_flags',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('enabled_plans', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('rollout_percentage', sa.Integer(), nullable=False),
    sa.Column('user_id_allowlist', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_by_improvement_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by_improvement_id'], ['system_improvements.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_flags_name'), 'feature_flags', ['name'], unique=True)
    op.create_table('ip_allowlists',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=False),
    sa.Column('label', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ip_allowlists_user_id'), 'ip_allowlists', ['user_id'], unique=False)
    op.create_table('login_anomalies',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('anomaly_type', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('score', sa.Float(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('device_fingerprint', sa.String(length=64), nullable=True),
    sa.Column('country', sa.String(length=10), nullable=True),
    sa.Column('is_resolved', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_login_anomalies_user_id'), 'login_anomalies', ['user_id'], unique=False)
    op.create_table('music_tracks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('job_id', sa.UUID(), nullable=True),
    sa.Column('track_name', sa.String(length=255), nullable=False),
    sa.Column('genre', sa.String(length=50), nullable=False),
    sa.Column('mood', sa.String(length=50), nullable=True),
    sa.Column('tempo', sa.Integer(), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=False),
    sa.Column('file_url', sa.String(length=500), nullable=False),
    sa.Column('usage_rights', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['music_generation_jobs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_music_tracks_business_id'), 'music_tracks', ['business_id'], unique=False)
    op.create_table('push_subscriptions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('endpoint', sa.Text(), nullable=False),
    sa.Column('p256dh', sa.String(length=255), nullable=False),
    sa.Column('auth', sa.String(length=255), nullable=False),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_push_subscriptions_user_id'), 'push_subscriptions', ['user_id'], unique=False)
    op.create_table('resource_requests',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('resource_type', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('parameters', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('provider_reference', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resource_requests_resource_type'), 'resource_requests', ['resource_type'], unique=False)
    op.create_index(op.f('ix_resource_requests_status'), 'resource_requests', ['status'], unique=False)
    op.create_table('security_keys',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('credential_id', sa.Text(), nullable=False),
    sa.Column('attestation', sa.Text(), nullable=True),
    sa.Column('nickname', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('credential_id')
    )
    op.create_index(op.f('ix_security_keys_user_id'), 'security_keys', ['user_id'], unique=False)
    op.create_table('sellia_conversations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=True),
    sa.Column('messages', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sellia_conversations_user_id'), 'sellia_conversations', ['user_id'], unique=False)
    op.create_table('subscription_access_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('feature_name', sa.String(length=100), nullable=False),
    sa.Column('endpoint', sa.String(length=255), nullable=True),
    sa.Column('response_status', sa.Integer(), nullable=True),
    sa.Column('response_size', sa.Integer(), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_access_logs_feature_name'), 'subscription_access_logs', ['feature_name'], unique=False)
    op.create_index(op.f('ix_subscription_access_logs_user_id'), 'subscription_access_logs', ['user_id'], unique=False)
    op.create_table('subscriptions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('plan_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('ACTIVE', 'CANCELLED', 'PAST_DUE', 'TRIALING', 'INACTIVE', name='subscriptionstatus'), nullable=False),
    sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False),
    sa.Column('stripe_customer_id', sa.String(length=100), nullable=True),
    sa.Column('stripe_subscription_id', sa.String(length=100), nullable=True),
    sa.Column('mercadopago_preference_id', sa.String(length=100), nullable=True),
    sa.Column('mercadopago_payment_id', sa.String(length=100), nullable=True),
    sa.Column('mercadopago_preapproval_id', sa.String(length=100), nullable=True),
    sa.Column('billing_cycle', sa.String(length=10), nullable=False),
    sa.Column('payment_provider', sa.String(length=20), nullable=True),
    sa.Column('payment_method_id', sa.String(length=100), nullable=True),
    sa.Column('crypto_network', sa.String(length=20), nullable=True),
    sa.Column('crypto_wallet_address', sa.String(length=100), nullable=True),
    sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('grace_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('auto_renew', sa.Boolean(), nullable=False),
    sa.Column('invoice_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('downgrade_to_plan_id', sa.UUID(), nullable=True),
    sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['downgrade_to_plan_id'], ['subscription_plans.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=True)
    op.create_table('trusted_devices',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('device_fingerprint', sa.String(length=64), nullable=False),
    sa.Column('device_name', sa.String(length=255), nullable=True),
    sa.Column('os', sa.String(length=100), nullable=True),
    sa.Column('browser', sa.String(length=100), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('country', sa.String(length=10), nullable=True),
    sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_trusted', sa.Boolean(), nullable=False),
    sa.Column('is_blocked', sa.Boolean(), nullable=False),
    sa.Column('remember_days', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trusted_devices_user_id'), 'trusted_devices', ['user_id'], unique=False)
    op.create_table('two_fa_backup_codes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('code_hash', sa.String(length=255), nullable=False),
    sa.Column('is_used', sa.Boolean(), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_two_fa_backup_codes_user_id'), 'two_fa_backup_codes', ['user_id'], unique=False)
    op.create_table('usage_alerts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('metric_type', sa.String(length=50), nullable=False),
    sa.Column('threshold_percent', sa.Integer(), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('acknowledged', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_alerts_user_id'), 'usage_alerts', ['user_id'], unique=False)
    op.create_table('user_achievements',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('achievement_id', sa.UUID(), nullable=False),
    sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('was_celebrated', sa.Boolean(), nullable=False),
    sa.Column('shared_to_social', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_achievements_achievement_id'), 'user_achievements', ['achievement_id'], unique=False)
    op.create_index('ix_user_achievements_user_achievement', 'user_achievements', ['user_id', 'achievement_id'], unique=True)
    op.create_index(op.f('ix_user_achievements_user_id'), 'user_achievements', ['user_id'], unique=False)
    op.create_table('user_api_keys',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('encrypted_key', sa.Text(), nullable=False),
    sa.Column('api_key_fernet', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_api_keys_user_id'), 'user_api_keys', ['user_id'], unique=False)
    op.create_table('user_login_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=False),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('device_fingerprint', sa.String(length=64), nullable=True),
    sa.Column('country', sa.String(length=10), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_login_logs_user_id'), 'user_login_logs', ['user_id'], unique=False)
    op.create_table('user_sessions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('session_token', sa.String(length=255), nullable=False),
    sa.Column('device_name', sa.String(length=255), nullable=True),
    sa.Column('device_fingerprint', sa.String(length=64), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=False),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('country', sa.String(length=10), nullable=True),
    sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_revoked', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_session_token'), 'user_sessions', ['session_token'], unique=True)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
    op.create_table('video_scripts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('job_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('hook', sa.Text(), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('cta', sa.Text(), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=False),
    sa.Column('visual_direction', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['video_generation_jobs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_scripts_business_id'), 'video_scripts', ['business_id'], unique=False)
    op.create_index(op.f('ix_video_scripts_job_id'), 'video_scripts', ['job_id'], unique=False)
    op.create_table('webauthn_credentials',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('credential_id', sa.Text(), nullable=False),
    sa.Column('public_key', sa.Text(), nullable=False),
    sa.Column('sign_count', sa.Integer(), nullable=False),
    sa.Column('device_name', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('credential_id')
    )
    op.create_index(op.f('ix_webauthn_credentials_user_id'), 'webauthn_credentials', ['user_id'], unique=False)
    op.create_table('accounts_receivable_snapshots',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('total_outstanding', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('total_overdue', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('invoice_count', sa.Integer(), nullable=False),
    sa.Column('overdue_count', sa.Integer(), nullable=False),
    sa.Column('customer_breakdown', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_receivable_snapshots_business_id'), 'accounts_receivable_snapshots', ['business_id'], unique=False)
    op.create_index('ix_ar_snapshots_business_date', 'accounts_receivable_snapshots', ['business_id', 'snapshot_date'], unique=False)
    op.create_table('agent_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('personality_id', sa.UUID(), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=True),
    sa.Column('custom_instructions', sa.Text(), nullable=True),
    sa.Column('tone_override', sa.String(length=50), nullable=True),
    sa.Column('voice_personality_id', sa.UUID(), nullable=True),
    sa.Column('ai_auto_reply_enabled', sa.Boolean(), nullable=False),
    sa.Column('ai_auto_reply_personality_id', sa.UUID(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['ai_auto_reply_personality_id'], ['agent_personalities.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['personality_id'], ['agent_personalities.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['voice_personality_id'], ['agent_personalities.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_configs_business_id'), 'agent_configs', ['business_id'], unique=False)
    op.create_table('agent_conversations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('personality_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=True),
    sa.Column('context_summary', sa.Text(), nullable=True),
    sa.Column('message_count', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['personality_id'], ['agent_personalities.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_conversations_business_id'), 'agent_conversations', ['business_id'], unique=False)
    op.create_index(op.f('ix_agent_conversations_user_id'), 'agent_conversations', ['user_id'], unique=False)
    op.create_table('alert_rules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('rule_type', sa.Enum('LEAD_SCORE_THRESHOLD', 'DEAL_STALLED', 'NO_REPLY', 'REVENUE_TARGET', 'HOT_LEAD_NO_DEAL', 'CART_ABANDONED', 'WORKFLOW_FAILED', 'COMPETITOR_MENTIONED', name='alertruletype'), nullable=False),
    sa.Column('config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('severity', sa.Enum('INFO', 'WARNING', 'CRITICAL', name='alertseverity'), nullable=False),
    sa.Column('channels', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('cooldown_minutes', sa.Integer(), nullable=False),
    sa.Column('max_alerts_per_day', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_rules_business_id'), 'alert_rules', ['business_id'], unique=False)
    op.create_index(op.f('ix_alert_rules_rule_type'), 'alert_rules', ['rule_type'], unique=False)
    op.create_table('app_build_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('app_name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('features', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('tech_stack', sa.String(length=100), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'ANALYZING', 'GENERATING', 'COMPLETED', 'FAILED', name='appbuildstatus'), nullable=False),
    sa.Column('code_zip_url', sa.String(length=1000), nullable=True),
    sa.Column('preview_url', sa.String(length=1000), nullable=True),
    sa.Column('deploy_instructions', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_app_build_jobs_business_id'), 'app_build_jobs', ['business_id'], unique=False)
    op.create_index(op.f('ix_app_build_jobs_status'), 'app_build_jobs', ['status'], unique=False)
    op.create_table('automation_workflows',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('trigger_type', sa.Enum('NEW_LEAD', 'NEW_MESSAGE', 'NO_REPLY', 'CART_ABANDONED', 'APPOINTMENT_MISSED', 'TAG_ADDED', 'STAGE_CHANGED', 'TIME_DELAY', 'LEAD_SCORE_CHANGED', 'DEAL_STALLED', 'PRICE_INQUIRY', 'REPEAT_CUSTOMER', 'REVENUE_EVENT', 'SERVICE_PAID', 'APPOINTMENT_SCHEDULED', 'APPOINTMENT_CONFIRMED', 'APPOINTMENT_NO_SHOW', 'SERVICE_COMPLETED', 'FEEDBACK_RECEIVED', name='workflowtriggertype'), nullable=False),
    sa.Column('trigger_config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('actions', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('visual_data', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'DRAFT', name='workflowstatus'), nullable=False),
    sa.Column('execution_count', sa.Integer(), nullable=True),
    sa.Column('conversion_count', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_workflows_business_id'), 'automation_workflows', ['business_id'], unique=False)
    op.create_table('autopilot_action_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('action_type', sa.Enum('QUALIFY_LEAD', 'MOVE_DEAL', 'SEND_FOLLOWUP', 'CLOSE_DEAL', 'CREATE_ORDER', 'REQUEST_REVIEW', 'ACTIVATE_RECOVERY_WORKFLOW', 'ESCALATE_TO_HUMAN', 'SEND_PROPOSAL', 'ASSIGN_AGENT', 'START_SEQUENCE', 'CREATE_DEAL', 'UPDATE_LEAD_SCORE', 'APPLY_RECOMMENDATION', name='autopilotactiontype'), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.UUID(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('ai_explanation', sa.Text(), nullable=True),
    sa.Column('confidence_score', sa.Integer(), nullable=False),
    sa.Column('context_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('status', sa.Enum('EXECUTED', 'PENDING_APPROVAL', 'ESCALATED', 'REJECTED', 'FAILED', name='autopilotactionstatus'), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('requires_approval', sa.Boolean(), nullable=False),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('approved_by_user_id', sa.UUID(), nullable=True),
    sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('rejected_reason', sa.Text(), nullable=True),
    sa.Column('revenue_impact', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_autopilot_action_logs_action_type'), 'autopilot_action_logs', ['action_type'], unique=False)
    op.create_index(op.f('ix_autopilot_action_logs_business_id'), 'autopilot_action_logs', ['business_id'], unique=False)
    op.create_index(op.f('ix_autopilot_action_logs_entity_id'), 'autopilot_action_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_autopilot_action_logs_status'), 'autopilot_action_logs', ['status'], unique=False)
    op.create_index('ix_autopilot_logs_business_created', 'autopilot_action_logs', ['business_id', 'created_at'], unique=False)
    op.create_index('ix_autopilot_logs_business_status', 'autopilot_action_logs', ['business_id', 'status'], unique=False)
    op.create_index('ix_autopilot_logs_entity', 'autopilot_action_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_table('autopilot_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('auto_qualify_leads', sa.Boolean(), nullable=False),
    sa.Column('auto_move_deals', sa.Boolean(), nullable=False),
    sa.Column('auto_send_followups', sa.Boolean(), nullable=False),
    sa.Column('auto_close_deals', sa.Boolean(), nullable=False),
    sa.Column('auto_create_orders', sa.Boolean(), nullable=False),
    sa.Column('auto_request_reviews', sa.Boolean(), nullable=False),
    sa.Column('auto_activate_recovery_workflows', sa.Boolean(), nullable=False),
    sa.Column('auto_escalate_to_human', sa.Boolean(), nullable=False),
    sa.Column('approval_threshold_amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('max_daily_auto_messages', sa.Integer(), nullable=False),
    sa.Column('max_daily_auto_closes', sa.Integer(), nullable=False),
    sa.Column('max_daily_auto_orders', sa.Integer(), nullable=False),
    sa.Column('human_escalation_channels', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('escalation_email', sa.String(length=255), nullable=True),
    sa.Column('escalation_whatsapp', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_paused', sa.Boolean(), nullable=False),
    sa.Column('paused_reason', sa.Text(), nullable=True),
    sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('require_ai_explanation', sa.Boolean(), nullable=False),
    sa.Column('explanation_language', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_autopilot_configs_business_active', 'autopilot_configs', ['business_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_autopilot_configs_business_id'), 'autopilot_configs', ['business_id'], unique=True)
    op.create_table('autopilot_daily_reports',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('report_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('leads_contacted', sa.Integer(), nullable=False),
    sa.Column('deals_moved', sa.Integer(), nullable=False),
    sa.Column('deals_closed', sa.Integer(), nullable=False),
    sa.Column('orders_created', sa.Integer(), nullable=False),
    sa.Column('messages_sent', sa.Integer(), nullable=False),
    sa.Column('sequences_started', sa.Integer(), nullable=False),
    sa.Column('workflows_activated', sa.Integer(), nullable=False),
    sa.Column('revenue_generated', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('deals_value_closed', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('actions_escalated', sa.Integer(), nullable=False),
    sa.Column('actions_pending_approval', sa.Integer(), nullable=False),
    sa.Column('actions_rejected', sa.Integer(), nullable=False),
    sa.Column('ai_summary', sa.Text(), nullable=True),
    sa.Column('highlights', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_autopilot_daily_reports_business_id'), 'autopilot_daily_reports', ['business_id'], unique=False)
    op.create_index(op.f('ix_autopilot_daily_reports_report_date'), 'autopilot_daily_reports', ['report_date'], unique=False)
    op.create_index('ix_autopilot_reports_business_date', 'autopilot_daily_reports', ['business_id', 'report_date'], unique=True)
    op.create_table('bank_transfer_payments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('subscription_id', sa.UUID(), nullable=True),
    sa.Column('plan_id', sa.UUID(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('order_number', sa.String(length=50), nullable=False),
    sa.Column('alias', sa.String(length=100), nullable=True),
    sa.Column('cbu', sa.String(length=50), nullable=True),
    sa.Column('account_holder', sa.String(length=255), nullable=True),
    sa.Column('instructions', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('proof_image_url', sa.Text(), nullable=True),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('confirmed_by_admin_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('confirmed_by_admin_id', sa.UUID(), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['confirmed_by_admin_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_transfer_payments_order_number'), 'bank_transfer_payments', ['order_number'], unique=True)
    op.create_index(op.f('ix_bank_transfer_payments_subscription_id'), 'bank_transfer_payments', ['subscription_id'], unique=False)
    op.create_index(op.f('ix_bank_transfer_payments_user_id'), 'bank_transfer_payments', ['user_id'], unique=False)
    op.create_table('business_contexts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('business_type', sa.Enum('PHYSICAL_PRODUCTS', 'DIGITAL_PRODUCTS', 'SERVICES', 'CONSULTING', 'SOFTWARE', 'FOOD_BEVERAGE', 'FASHION_BEAUTY', 'HEALTH_WELLNESS', 'HOME_DECOR', 'HANDCRAFT', 'OTHER', name='businesstype'), nullable=False),
    sa.Column('sales_model', sa.Enum('B2C', 'B2B', 'B2B2C', 'D2C', 'MARKETPLACE', name='salesmodel'), nullable=False),
    sa.Column('geographic_reach', sa.Enum('LOCAL', 'REGIONAL', 'NATIONAL', 'CROSS_BORDER', 'GLOBAL', name='geographicreach'), nullable=False),
    sa.Column('presence_type', sa.Enum('LOCAL_PHYSICAL', 'HOME_OFFICE', 'SHOWROOM', 'ONLINE_ONLY', 'HYBRID', name='presencetype'), nullable=False),
    sa.Column('industry', sa.String(length=100), nullable=True),
    sa.Column('target_audience', sa.Text(), nullable=True),
    sa.Column('value_proposition', sa.Text(), nullable=True),
    sa.Column('price_range', sa.String(length=50), nullable=True),
    sa.Column('average_ticket', sa.Integer(), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('state_province', sa.String(length=100), nullable=True),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('has_physical_location', sa.Boolean(), nullable=True),
    sa.Column('serves_home_office', sa.Boolean(), nullable=True),
    sa.Column('does_delivery', sa.Boolean(), nullable=True),
    sa.Column('does_pickup', sa.Boolean(), nullable=True),
    sa.Column('shipping_radius_km', sa.Integer(), nullable=True),
    sa.Column('channels_configured', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('ads_configured', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('shipping_configured', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('website_configured', sa.Boolean(), nullable=True),
    sa.Column('seo_configured', sa.Boolean(), nullable=True),
    sa.Column('email_marketing_configured', sa.Boolean(), nullable=True),
    sa.Column('primary_goal', sa.String(length=50), nullable=True),
    sa.Column('monthly_revenue_goal', sa.Integer(), nullable=True),
    sa.Column('monthly_leads_goal', sa.Integer(), nullable=True),
    sa.Column('target_countries', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('ai_recommended_playbooks', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('ai_priority_actions', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('ai_brand_voice', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_contexts_business_id'), 'business_contexts', ['business_id'], unique=False)
    op.create_index(op.f('ix_business_contexts_user_id'), 'business_contexts', ['user_id'], unique=False)
    op.create_table('business_documents',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=False),
    sa.Column('file_type', sa.String(length=50), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('chunk_count', sa.Integer(), nullable=False),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_documents_business_id'), 'business_documents', ['business_id'], unique=False)
    op.create_table('business_user_roles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('invited_by', sa.UUID(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_user_roles_business_id'), 'business_user_roles', ['business_id'], unique=False)
    op.create_index('ix_business_user_roles_user_business', 'business_user_roles', ['user_id', 'business_id'], unique=True)
    op.create_index(op.f('ix_business_user_roles_user_id'), 'business_user_roles', ['user_id'], unique=False)
    op.create_table('cancellation_feedbacks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('subscription_id', sa.UUID(), nullable=True),
    sa.Column('reason_category', sa.String(length=50), nullable=False),
    sa.Column('reason_text', sa.Text(), nullable=True),
    sa.Column('competitor_name', sa.Text(), nullable=True),
    sa.Column('improvement_suggestion', sa.Text(), nullable=True),
    sa.Column('rating_nps', sa.Integer(), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cancellation_feedbacks_user_id'), 'cancellation_feedbacks', ['user_id'], unique=False)
    op.create_table('catalog_items',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('type', sa.Enum('SERVICE', 'GOOD', 'DIGITAL', name='catalogitemtype'), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('stock', sa.Integer(), nullable=True),
    sa.Column('is_available', sa.Boolean(), nullable=False),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('images', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('tags', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_catalog_items_business_id'), 'catalog_items', ['business_id'], unique=False)
    op.create_table('celebration_events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('event_title', sa.String(length=200), nullable=False),
    sa.Column('event_description', sa.Text(), nullable=True),
    sa.Column('event_value', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('event_metadata', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('intensity', sa.String(length=20), nullable=False),
    sa.Column('was_shown', sa.Boolean(), nullable=False),
    sa.Column('shown_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('companion_message', sa.Text(), nullable=True),
    sa.Column('companion_emotion', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_celebration_events_business_id'), 'celebration_events', ['business_id'], unique=False)
    op.create_index(op.f('ix_celebration_events_event_type'), 'celebration_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_celebration_events_user_id'), 'celebration_events', ['user_id'], unique=False)
    op.create_index('ix_celebration_events_user_unshown', 'celebration_events', ['user_id', 'was_shown'], unique=False)
    op.create_table('channel_connections',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('platform', sa.Enum('WHATSAPP', 'EMAIL', 'INSTAGRAM', 'MERCADOLIBRE', 'AMAZON', 'BEACONS', 'LINKEDIN', 'TELEGRAM', 'WEBCHAT', 'MESSENGER', 'FACEBOOK_ADS', 'META_ADS', 'GOOGLE_ADS', 'SHOPIFY', 'TIKTOK', 'TIKTOK_ADS', 'TWITTER', 'THREADS', name='channelplatform'), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('credentials', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('settings', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'CONNECTED', 'ERROR', 'DISABLED', name='channelstatus'), nullable=False),
    sa.Column('status_message', sa.Text(), nullable=True),
    sa.Column('webhook_url', sa.String(length=512), nullable=True),
    sa.Column('webhook_token', sa.String(length=64), nullable=False),
    sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('webhook_token')
    )
    op.create_index(op.f('ix_channel_connections_business_id'), 'channel_connections', ['business_id'], unique=False)
    op.create_table('chatbot_rules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('intent', sa.String(length=100), nullable=False),
    sa.Column('keywords', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('response_template', sa.Text(), nullable=False),
    sa.Column('response_type', sa.String(length=50), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('channel_filter', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('requires_human', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('usage_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatbot_rules_business_id'), 'chatbot_rules', ['business_id'], unique=False)
    op.create_index(op.f('ix_chatbot_rules_intent'), 'chatbot_rules', ['intent'], unique=False)
    op.create_table('cohort_metrics',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('cohort_month', sa.String(length=7), nullable=False),
    sa.Column('cohort_size', sa.Integer(), nullable=False),
    sa.Column('period_months', sa.Integer(), nullable=False),
    sa.Column('active_customers', sa.Integer(), nullable=False),
    sa.Column('revenue', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('retention_rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cohort_metrics_business_cohort', 'cohort_metrics', ['business_id', 'cohort_month', 'period_months'], unique=False)
    op.create_index(op.f('ix_cohort_metrics_business_id'), 'cohort_metrics', ['business_id'], unique=False)
    op.create_table('computer_use_batch_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('task_description', sa.Text(), nullable=False),
    sa.Column('urls', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('provider', sa.String(length=50), nullable=True),
    sa.Column('max_steps_per_url', sa.Integer(), nullable=True),
    sa.Column('concurrency', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='batch_status'), nullable=True),
    sa.Column('completed_count', sa.Integer(), nullable=True),
    sa.Column('failed_count', sa.Integer(), nullable=True),
    sa.Column('total_count', sa.Integer(), nullable=True),
    sa.Column('results_summary', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_batch_jobs_user_id'), 'computer_use_batch_jobs', ['user_id'], unique=False)
    op.create_table('computer_use_browser_profiles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('viewport_width', sa.Integer(), nullable=True),
    sa.Column('viewport_height', sa.Integer(), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('locale', sa.String(length=10), nullable=True),
    sa.Column('timezone_id', sa.String(length=50), nullable=True),
    sa.Column('cookies', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('local_storage', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('geolocation', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_browser_profiles_user_id'), 'computer_use_browser_profiles', ['user_id'], unique=False)
    op.create_table('computer_use_templates',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('task_description', sa.Text(), nullable=False),
    sa.Column('start_url', sa.String(length=2048), nullable=True),
    sa.Column('tags', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('usage_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_templates_user_id'), 'computer_use_templates', ['user_id'], unique=False)
    op.create_table('computer_use_webhooks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('url', sa.String(length=2048), nullable=False),
    sa.Column('events', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('secret', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_status_code', sa.Integer(), nullable=True),
    sa.Column('failure_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_webhooks_user_id'), 'computer_use_webhooks', ['user_id'], unique=False)
    op.create_table('crm_build_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('crm_name', sa.String(length=255), nullable=False),
    sa.Column('modules', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'GENERATING', 'COMPLETED', 'FAILED', name='crmbuildstatus'), nullable=False),
    sa.Column('code_url', sa.String(length=1000), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crm_build_jobs_business_id'), 'crm_build_jobs', ['business_id'], unique=False)
    op.create_index(op.f('ix_crm_build_jobs_status'), 'crm_build_jobs', ['status'], unique=False)
    op.create_table('customer_loyalty_badges',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('badge_type', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('icon_url', sa.Text(), nullable=True),
    sa.Column('criteria', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_loyalty_badges_business_id'), 'customer_loyalty_badges', ['business_id'], unique=False)
    op.create_table('data_access_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('action', sa.String(length=20), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('record_id', sa.String(length=36), nullable=True),
    sa.Column('field_name', sa.String(length=100), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('request_path', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_access_logs_business_id'), 'data_access_logs', ['business_id'], unique=False)
    op.create_index('ix_data_access_logs_table_action', 'data_access_logs', ['table_name', 'action'], unique=False)
    op.create_index('ix_data_access_logs_user_business', 'data_access_logs', ['user_id', 'business_id'], unique=False)
    op.create_index(op.f('ix_data_access_logs_user_id'), 'data_access_logs', ['user_id'], unique=False)
    op.create_table('data_retention_policies',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('retention_days', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_retention_policies_business_id'), 'data_retention_policies', ['business_id'], unique=False)
    op.create_index('ix_data_retention_policies_business_table', 'data_retention_policies', ['business_id', 'table_name'], unique=False)
    op.create_table('departments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('slug', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('head_agent_personality_id', sa.UUID(), nullable=True),
    sa.Column('color', sa.String(length=20), nullable=True),
    sa.Column('icon', sa.String(length=50), nullable=True),
    sa.Column('config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['head_agent_personality_id'], ['agent_personalities.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_departments_business_id'), 'departments', ['business_id'], unique=False)
    op.create_table('email_sequences',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'DRAFT', name='workflowstatus'), nullable=False),
    sa.Column('trigger_type', sa.String(length=100), nullable=True),
    sa.Column('sent_count', sa.Integer(), nullable=True),
    sa.Column('opens_count', sa.Integer(), nullable=True),
    sa.Column('clicks_count', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_sequences_business_id'), 'email_sequences', ['business_id'], unique=False)
    op.create_table('email_templates',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('subject', sa.String(length=500), nullable=False),
    sa.Column('body_html', sa.Text(), nullable=True),
    sa.Column('body_text', sa.Text(), nullable=False),
    sa.Column('variables', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_templates_business_id'), 'email_templates', ['business_id'], unique=False)
    op.create_table('finance_autopilot_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_paused', sa.Boolean(), nullable=False),
    sa.Column('paused_reason', sa.Text(), nullable=True),
    sa.Column('auto_deliver_invoices', sa.Boolean(), nullable=False),
    sa.Column('auto_run_dunning', sa.Boolean(), nullable=False),
    sa.Column('auto_reconcile_payments', sa.Boolean(), nullable=False),
    sa.Column('auto_generate_tax_reports', sa.Boolean(), nullable=False),
    sa.Column('dunning_channel', sa.String(length=50), nullable=False),
    sa.Column('max_dunning_level', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_finance_autopilot_configs_business_id'), 'finance_autopilot_configs', ['business_id'], unique=True)
    op.create_table('funnel_metrics',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('period', sa.String(length=20), nullable=False),
    sa.Column('period_type', sa.String(length=10), nullable=False),
    sa.Column('leads_count', sa.Integer(), nullable=False),
    sa.Column('qualified_count', sa.Integer(), nullable=False),
    sa.Column('deals_count', sa.Integer(), nullable=False),
    sa.Column('orders_count', sa.Integer(), nullable=False),
    sa.Column('repeat_orders_count', sa.Integer(), nullable=False),
    sa.Column('conversion_lead_to_qualified', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('conversion_qualified_to_deal', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('conversion_deal_to_order', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('conversion_order_to_repeat', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('revenue_total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('avg_order_value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_funnel_metrics_business_id'), 'funnel_metrics', ['business_id'], unique=False)
    op.create_index('ix_funnel_metrics_business_period', 'funnel_metrics', ['business_id', 'period'], unique=False)
    op.create_table('growth_campaigns',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('campaign_type', sa.Enum('SEO_CONTENT', 'SOCIAL_ORGANIC', 'LEAD_MAGNET', 'REFERRAL_VIRAL', 'EDUCATIONAL_NURTURE', 'UGC_CAMPAIGN', 'COMMUNITY_ENGAGEMENT', name='growthcampaigntype'), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', name='growthcampaignstatus'), nullable=False),
    sa.Column('config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('target_audience', sa.Text(), nullable=True),
    sa.Column('content_pillars', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('tone_of_voice', sa.String(length=100), nullable=False),
    sa.Column('leads_generated', sa.Integer(), nullable=False),
    sa.Column('conversions', sa.Integer(), nullable=False),
    sa.Column('revenue_attributed', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('content_published', sa.Integer(), nullable=False),
    sa.Column('engagement_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('metrics_snapshot', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_growth_campaigns_business_id'), 'growth_campaigns', ['business_id'], unique=False)
    op.create_index('ix_growth_campaigns_business_status', 'growth_campaigns', ['business_id', 'status'], unique=False)
    op.create_index('ix_growth_campaigns_business_type', 'growth_campaigns', ['business_id', 'campaign_type'], unique=False)
    op.create_index(op.f('ix_growth_campaigns_campaign_type'), 'growth_campaigns', ['campaign_type'], unique=False)
    op.create_table('insight_alerts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('insight_type', sa.String(length=50), nullable=False),
    sa.Column('severity', sa.String(length=20), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('metric_name', sa.String(length=100), nullable=True),
    sa.Column('metric_change_percent', sa.Numeric(precision=7, scale=2), nullable=True),
    sa.Column('recommended_action', sa.Text(), nullable=True),
    sa.Column('action_taken', sa.Boolean(), nullable=False),
    sa.Column('action_result', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_insight_alerts_business_id'), 'insight_alerts', ['business_id'], unique=False)
    op.create_index('ix_insight_alerts_business_type', 'insight_alerts', ['business_id', 'insight_type'], unique=False)
    op.create_index(op.f('ix_insight_alerts_insight_type'), 'insight_alerts', ['insight_type'], unique=False)
    op.create_table('loyalty_programs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('points_per_currency', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('min_redeem_points', sa.Integer(), nullable=False),
    sa.Column('welcome_bonus', sa.Integer(), nullable=False),
    sa.Column('referral_bonus', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_loyalty_programs_business_id'), 'loyalty_programs', ['business_id'], unique=False)
    op.create_table('ml_training_data',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('data_type', sa.String(length=50), nullable=False),
    sa.Column('features', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('label', sa.String(length=50), nullable=True),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('model_version', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_training_data_data_type'), 'ml_training_data', ['data_type'], unique=False)
    op.create_index(op.f('ix_ml_training_data_user_id'), 'ml_training_data', ['user_id'], unique=False)
    op.create_table('notification_deliveries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('channel', sa.String(length=20), nullable=False),
    sa.Column('priority', sa.String(length=20), nullable=False),
    sa.Column('notification_type', sa.String(length=50), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=True),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('message_short', sa.String(length=500), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('context_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_deliveries_business_id'), 'notification_deliveries', ['business_id'], unique=False)
    op.create_index(op.f('ix_notification_deliveries_channel'), 'notification_deliveries', ['channel'], unique=False)
    op.create_index(op.f('ix_notification_deliveries_priority'), 'notification_deliveries', ['priority'], unique=False)
    op.create_index(op.f('ix_notification_deliveries_status'), 'notification_deliveries', ['status'], unique=False)
    op.create_index(op.f('ix_notification_deliveries_user_id'), 'notification_deliveries', ['user_id'], unique=False)
    op.create_index('ix_notifications_business_type', 'notification_deliveries', ['business_id', 'notification_type'], unique=False)
    op.create_index('ix_notifications_user_status', 'notification_deliveries', ['user_id', 'status'], unique=False)
    op.create_table('nps_campaigns',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('trigger_type', sa.String(length=50), nullable=False),
    sa.Column('trigger_days', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', name='npscampaignstatus'), nullable=False),
    sa.Column('question_text', sa.String(length=500), nullable=False),
    sa.Column('thank_you_message', sa.String(length=500), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nps_campaigns_business_id'), 'nps_campaigns', ['business_id'], unique=False)
    op.create_table('optimization_experiments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('hypothesis', sa.Text(), nullable=False),
    sa.Column('target_metric', sa.String(length=50), nullable=False),
    sa.Column('variant_a_name', sa.String(length=100), nullable=False),
    sa.Column('variant_a_config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('variant_b_name', sa.String(length=100), nullable=False),
    sa.Column('variant_b_config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('sample_size_target', sa.Integer(), nullable=False),
    sa.Column('confidence_threshold', sa.Numeric(precision=4, scale=3), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('winner_variant', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_optimization_experiments_business_id'), 'optimization_experiments', ['business_id'], unique=False)
    op.create_table('outreach_cadence_rules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('max_messages_per_week', sa.Integer(), nullable=False),
    sa.Column('max_messages_per_channel_per_week', sa.Integer(), nullable=False),
    sa.Column('min_hours_between_contacts', sa.Integer(), nullable=False),
    sa.Column('cooldown_after_no_reply_days', sa.Integer(), nullable=False),
    sa.Column('cooldown_after_no_reply_count', sa.Integer(), nullable=False),
    sa.Column('long_cooldown_days', sa.Integer(), nullable=False),
    sa.Column('channel_priority', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('respect_local_hours', sa.Boolean(), nullable=False),
    sa.Column('allowed_hours_start', sa.Integer(), nullable=False),
    sa.Column('allowed_hours_end', sa.Integer(), nullable=False),
    sa.Column('avoid_weekends', sa.Boolean(), nullable=False),
    sa.Column('hot_lead_override', sa.Boolean(), nullable=False),
    sa.Column('hot_lead_max_per_week', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outreach_cadence_rules_business_id'), 'outreach_cadence_rules', ['business_id'], unique=True)
    op.create_table('payment_integrations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_default', sa.Boolean(), nullable=False),
    sa.Column('credentials_encrypted', sa.Text(), nullable=True),
    sa.Column('settings', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_integrations_business_id'), 'payment_integrations', ['business_id'], unique=False)
    op.create_table('payment_transactions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('subscription_id', sa.UUID(), nullable=True),
    sa.Column('plan_id', sa.UUID(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('provider', sa.String(length=20), nullable=False),
    sa.Column('provider_transaction_id', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('crypto_network', sa.String(length=20), nullable=True),
    sa.Column('crypto_from_address', sa.String(length=100), nullable=True),
    sa.Column('crypto_tx_hash', sa.String(length=100), nullable=True),
    sa.Column('crypto_confirmations', sa.Integer(), nullable=True),
    sa.Column('billing_cycle', sa.String(length=10), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_transactions_crypto_tx_hash'), 'payment_transactions', ['crypto_tx_hash'], unique=False)
    op.create_index(op.f('ix_payment_transactions_provider_transaction_id'), 'payment_transactions', ['provider_transaction_id'], unique=False)
    op.create_index(op.f('ix_payment_transactions_subscription_id'), 'payment_transactions', ['subscription_id'], unique=False)
    op.create_index(op.f('ix_payment_transactions_user_id'), 'payment_transactions', ['user_id'], unique=False)
    op.create_table('pipelines',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('stages', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_default', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pipelines_business_id'), 'pipelines', ['business_id'], unique=False)
    op.create_table('recommendations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('type', sa.Enum('SCORE_INCREASE', 'DEAL_MOVE', 'FOLLOW_UP', 'ASSIGN_AGENT', 'CREATE_ORDER', 'CUSTOM', name='recommendationtype'), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('context_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('action_type', sa.Enum('SEND_MESSAGE', 'MOVE_STAGE', 'ASSIGN_AGENT', 'CREATE_DEAL', 'WAIT', 'DISMISS', name='recommendationactiontype'), nullable=False),
    sa.Column('action_payload', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'APPLIED', 'DISMISSED', name='recommendationstatus'), nullable=False),
    sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('applied_by_user_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendations_business_id'), 'recommendations', ['business_id'], unique=False)
    op.create_index(op.f('ix_recommendations_status'), 'recommendations', ['status'], unique=False)
    op.create_table('referral_programs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('reward_type', sa.String(length=50), nullable=False),
    sa.Column('reward_value', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('max_referrals_per_user', sa.Integer(), nullable=False),
    sa.Column('expiry_days', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referral_programs_business_id'), 'referral_programs', ['business_id'], unique=False)
    op.create_table('resource_events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('request_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['request_id'], ['resource_requests.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resource_events_request_id'), 'resource_events', ['request_id'], unique=False)
    op.create_table('resource_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('request_id', sa.UUID(), nullable=False),
    sa.Column('job_type', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('result', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.ForeignKeyConstraint(['request_id'], ['resource_requests.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resource_jobs_request_id'), 'resource_jobs', ['request_id'], unique=False)
    op.create_table('secret_rotation_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('secret_type', sa.String(length=50), nullable=False),
    sa.Column('target_id', sa.String(length=36), nullable=True),
    sa.Column('old_value_hash', sa.String(length=255), nullable=True),
    sa.Column('new_value_hash', sa.String(length=255), nullable=True),
    sa.Column('rotated_by', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['rotated_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_secret_rotation_logs_business_id'), 'secret_rotation_logs', ['business_id'], unique=False)
    op.create_table('shipment_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('carrier', sa.Enum('ANDREANI', 'CORREO_ARGENTINO', 'OCA', 'MERCADO_ENVIOS', 'DHL', 'FEDEX', 'UPS', 'STARKEN', 'SERVIENTREGA', 'LOCAL', 'OTHER', name='carriertype'), nullable=False),
    sa.Column('label', sa.String(length=100), nullable=True),
    sa.Column('credentials', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_test_mode', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('default_service_type', sa.Enum('STANDARD', 'EXPRESS', 'SAME_DAY', 'OVERNIGHT', 'INTERNATIONAL', 'ECONOMY', name='servicetype'), nullable=True),
    sa.Column('default_from_address', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shipment_configs_business_id'), 'shipment_configs', ['business_id'], unique=False)
    op.create_table('social_sellers',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('platform', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('avatar_url', sa.Text(), nullable=True),
    sa.Column('personality_slug', sa.String(length=100), nullable=True),
    sa.Column('voice_config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('stats', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('ai_auto_reply', sa.Boolean(), nullable=False),
    sa.Column('greeting_message', sa.Text(), nullable=True),
    sa.Column('closing_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_social_sellers_business_id'), 'social_sellers', ['business_id'], unique=False)
    op.create_table('support_faqs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('question', sa.String(length=500), nullable=False),
    sa.Column('answer', sa.Text(), nullable=False),
    sa.Column('tags', sa.Text(), nullable=True),
    sa.Column('usage_count', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_support_faqs_business_id'), 'support_faqs', ['business_id'], unique=False)
    op.create_table('support_kb_articles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('tags', sa.Text(), nullable=True),
    sa.Column('embedding_vector', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_support_kb_articles_business_id'), 'support_kb_articles', ['business_id'], unique=False)
    op.create_table('support_tickets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('category', sa.Enum('ACCOUNT', 'BILLING', 'TECHNICAL', 'SALES', 'SECURITY', 'FEATURE_REQUEST', 'OTHER', name='ticketcategory'), nullable=False),
    sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='ticketpriority'), nullable=False),
    sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'WAITING_USER', 'RESOLVED', 'CLOSED', 'ESCALATED', name='ticketstatus'), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('ai_suggested_answer', sa.Text(), nullable=True),
    sa.Column('ai_confidence', sa.Float(), nullable=True),
    sa.Column('ai_response_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigned_to', sa.UUID(), nullable=True),
    sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolution_notes', sa.Text(), nullable=True),
    sa.Column('last_customer_reply', sa.Text(), nullable=True),
    sa.Column('last_customer_reply_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('csat_rating', sa.Integer(), nullable=True),
    sa.Column('csat_comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_support_tickets_assigned_to'), 'support_tickets', ['assigned_to'], unique=False)
    op.create_index(op.f('ix_support_tickets_business_id'), 'support_tickets', ['business_id'], unique=False)
    op.create_index(op.f('ix_support_tickets_user_id'), 'support_tickets', ['user_id'], unique=False)
    op.create_table('tax_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('country_code', sa.String(length=2), nullable=False),
    sa.Column('tax_name', sa.String(length=100), nullable=False),
    sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('tax_id_number', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('is_tax_exempt', sa.Boolean(), nullable=False),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_configs_business_id'), 'tax_configs', ['business_id'], unique=False)
    op.create_table('unified_customers',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('display_name', sa.String(length=200), nullable=True),
    sa.Column('master_email', sa.String(length=255), nullable=True),
    sa.Column('master_phone', sa.String(length=50), nullable=True),
    sa.Column('identity_map', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('total_lifetime_value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('buying_frequency_days', sa.Integer(), nullable=True),
    sa.Column('preferred_platforms', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('rfm_segment', sa.String(length=30), nullable=True),
    sa.Column('last_purchase_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('total_purchases', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_unified_customers_business_id'), 'unified_customers', ['business_id'], unique=False)
    op.create_index(op.f('ix_unified_customers_master_email'), 'unified_customers', ['master_email'], unique=False)
    op.create_index(op.f('ix_unified_customers_master_phone'), 'unified_customers', ['master_phone'], unique=False)
    op.create_table('usage_tracking',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('metric_type', sa.String(length=50), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('period_month', sa.String(length=7), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_tracking_metric_type'), 'usage_tracking', ['metric_type'], unique=False)
    op.create_index(op.f('ix_usage_tracking_period_month'), 'usage_tracking', ['period_month'], unique=False)
    op.create_index(op.f('ix_usage_tracking_user_id'), 'usage_tracking', ['user_id'], unique=False)
    op.create_table('user_feedback',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('type', sa.Enum('BUG', 'IDEA', 'COMPLAINT', 'PRAISE', 'OTHER', name='feedbacktype'), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='feedbackseverity'), nullable=False),
    sa.Column('status', sa.Enum('NEW', 'UNDER_REVIEW', 'PLANNED', 'IN_PROGRESS', 'SHIPPED', 'DECLINED', name='feedbackstatus'), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('screenshots', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('ai_analysis', sa.Text(), nullable=True),
    sa.Column('ai_solution_proposal', sa.Text(), nullable=True),
    sa.Column('ai_confidence', sa.Float(), nullable=True),
    sa.Column('ai_duplicate_of_id', sa.UUID(), nullable=True),
    sa.Column('votes_count', sa.Integer(), nullable=False),
    sa.Column('comments_count', sa.Integer(), nullable=False),
    sa.Column('target_plan', sa.String(length=50), nullable=True),
    sa.Column('estimated_effort_hours', sa.Integer(), nullable=True),
    sa.Column('system_improvement_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['ai_duplicate_of_id'], ['user_feedback.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['system_improvement_id'], ['system_improvements.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_feedback_business_id'), 'user_feedback', ['business_id'], unique=False)
    op.create_index(op.f('ix_user_feedback_user_id'), 'user_feedback', ['user_id'], unique=False)
    op.create_table('user_gamification_profiles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('level', sa.Integer(), nullable=False),
    sa.Column('level_title', sa.String(length=100), nullable=False),
    sa.Column('total_xp', sa.Integer(), nullable=False),
    sa.Column('xp_to_next_level', sa.Integer(), nullable=False),
    sa.Column('progress_pct', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('current_login_streak', sa.Integer(), nullable=False),
    sa.Column('max_login_streak', sa.Integer(), nullable=False),
    sa.Column('last_login_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('autopilot_trust_streak', sa.Integer(), nullable=False),
    sa.Column('total_achievements', sa.Integer(), nullable=False),
    sa.Column('total_sales_closed', sa.Integer(), nullable=False),
    sa.Column('total_revenue_generated', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('total_leads_acquired', sa.Integer(), nullable=False),
    sa.Column('total_content_published', sa.Integer(), nullable=False),
    sa.Column('total_reviews_collected', sa.Integer(), nullable=False),
    sa.Column('total_referrals_generated', sa.Integer(), nullable=False),
    sa.Column('total_missions_created', sa.Integer(), nullable=False),
    sa.Column('total_missions_completed', sa.Integer(), nullable=False),
    sa.Column('total_missions_started', sa.Integer(), nullable=False),
    sa.Column('total_computer_use_sessions', sa.Integer(), nullable=False),
    sa.Column('total_platforms_automated', sa.Integer(), nullable=False),
    sa.Column('garden_state', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('companion_name', sa.String(length=50), nullable=False),
    sa.Column('companion_mood', sa.String(length=20), nullable=False),
    sa.Column('companion_last_message', sa.Text(), nullable=True),
    sa.Column('user_mood_today', sa.String(length=20), nullable=True),
    sa.Column('mood_history', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_gamification_profiles_business_id'), 'user_gamification_profiles', ['business_id'], unique=False)
    op.create_index(op.f('ix_user_gamification_profiles_user_id'), 'user_gamification_profiles', ['user_id'], unique=True)
    op.create_table('agent_messages',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('model_used', sa.String(length=50), nullable=True),
    sa.Column('tokens_used', sa.Integer(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['agent_conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_messages_conversation_id'), 'agent_messages', ['conversation_id'], unique=False)
    op.create_table('app_features',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('job_id', sa.UUID(), nullable=False),
    sa.Column('feature_name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('estimated_hours', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['app_build_jobs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_app_features_job_id'), 'app_features', ['job_id'], unique=False)
    op.create_table('business_objectives',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('department_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('period', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY', 'CUSTOM', name='objectiveperiod'), nullable=False),
    sa.Column('status', sa.Enum('ACTIVE', 'ACHIEVED', 'AT_RISK', 'MISSED', 'PAUSED', name='objectivestatus'), nullable=False),
    sa.Column('target_value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('current_value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('linked_workflow_id', sa.UUID(), nullable=True),
    sa.Column('linked_channel_platform', sa.String(length=50), nullable=True),
    sa.Column('alert_threshold_percent', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('alert_channels', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['linked_workflow_id'], ['automation_workflows.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_objectives_business_id'), 'business_objectives', ['business_id'], unique=False)
    op.create_index(op.f('ix_business_objectives_department_id'), 'business_objectives', ['department_id'], unique=False)
    op.create_index(op.f('ix_business_objectives_status'), 'business_objectives', ['status'], unique=False)
    op.create_index('ix_objectives_business_status', 'business_objectives', ['business_id', 'status'], unique=False)
    op.create_table('computer_use_sessions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('task_description', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'running', 'paused', 'completed', 'failed', 'stopped', name='computer_use_status'), nullable=False),
    sa.Column('current_url', sa.String(length=2048), nullable=True),
    sa.Column('result_data', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('total_steps', sa.Integer(), nullable=True),
    sa.Column('browser_type', sa.String(length=20), nullable=True),
    sa.Column('profile_id', sa.UUID(), nullable=True),
    sa.Column('proxy_config_id', sa.UUID(), nullable=True),
    sa.Column('provider_used', sa.String(length=50), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['profile_id'], ['computer_use_browser_profiles.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['proxy_config_id'], ['computer_use_proxy_configs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_sessions_business_id'), 'computer_use_sessions', ['business_id'], unique=False)
    op.create_index(op.f('ix_computer_use_sessions_user_id'), 'computer_use_sessions', ['user_id'], unique=False)
    op.create_table('conversations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('channel_connection_id', sa.UUID(), nullable=True),
    sa.Column('external_id', sa.String(length=255), nullable=True),
    sa.Column('lead_name', sa.String(length=255), nullable=True),
    sa.Column('lead_email', sa.String(length=255), nullable=True),
    sa.Column('lead_phone', sa.String(length=50), nullable=True),
    sa.Column('lead_source', sa.String(length=100), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', 'SPAM', name='conversationstatus'), nullable=False),
    sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['channel_connection_id'], ['channel_connections.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_business_id'), 'conversations', ['business_id'], unique=False)
    op.create_index(op.f('ix_conversations_external_id'), 'conversations', ['external_id'], unique=False)
    op.create_table('crm_modules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('job_id', sa.UUID(), nullable=False),
    sa.Column('module_name', sa.String(length=100), nullable=False),
    sa.Column('config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['crm_build_jobs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crm_modules_job_id'), 'crm_modules', ['job_id'], unique=False)
    op.create_table('data_retention_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('policy_id', sa.UUID(), nullable=True),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('records_deleted', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['policy_id'], ['data_retention_policies.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_chunks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('document_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', app.domains.documents.models.Vector(768), nullable=True),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('page_number', sa.Integer(), nullable=True),
    sa.Column('chunk_metadata', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['business_documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_business_id'), 'document_chunks', ['business_id'], unique=False)
    op.create_index('ix_document_chunks_business_id_embedding', 'document_chunks', ['business_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
    op.create_table('feedback_comments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('feedback_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['feedback_id'], ['user_feedback.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_comments_feedback_id'), 'feedback_comments', ['feedback_id'], unique=False)
    op.create_index(op.f('ix_feedback_comments_user_id'), 'feedback_comments', ['user_id'], unique=False)
    op.create_table('feedback_votes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('feedback_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['feedback_id'], ['user_feedback.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_votes_feedback_id'), 'feedback_votes', ['feedback_id'], unique=False)
    op.create_index(op.f('ix_feedback_votes_user_id'), 'feedback_votes', ['user_id'], unique=False)
    op.create_table('invoices',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('transaction_id', sa.UUID(), nullable=True),
    sa.Column('invoice_number', sa.String(length=50), nullable=False),
    sa.Column('invoice_type', sa.String(length=10), nullable=False),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('total_amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('plan_name', sa.String(length=100), nullable=True),
    sa.Column('billing_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('billing_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('afip_cae', sa.String(length=20), nullable=True),
    sa.Column('afip_barcode', sa.Text(), nullable=True),
    sa.Column('pdf_url', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('emitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['transaction_id'], ['payment_transactions.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoices_invoice_number'), 'invoices', ['invoice_number'], unique=True)
    op.create_index(op.f('ix_invoices_transaction_id'), 'invoices', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_invoices_user_id'), 'invoices', ['user_id'], unique=False)
    op.create_table('lead_magnets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('campaign_id', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=300), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('format', sa.Enum('CHEAT_SHEET', 'TEMPLATE', 'CALCULATOR', 'MINI_GUIDE', 'QUIZ', 'AUDIT', 'TOOLKIT', 'CHECKLIST', 'EBOOK', 'VIDEO_MINI', name='leadmagnetformat'), nullable=False),
    sa.Column('topic', sa.String(length=200), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('landing_page_copy', sa.Text(), nullable=True),
    sa.Column('delivery_message', sa.Text(), nullable=True),
    sa.Column('call_to_action', sa.String(length=200), nullable=True),
    sa.Column('times_delivered', sa.Integer(), nullable=False),
    sa.Column('times_downloaded', sa.Integer(), nullable=False),
    sa.Column('times_converted', sa.Integer(), nullable=False),
    sa.Column('conversion_rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('engagement_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('auto_deliver', sa.Boolean(), nullable=False),
    sa.Column('delivery_channel', sa.String(length=50), nullable=False),
    sa.Column('delivery_trigger', sa.String(length=50), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['campaign_id'], ['growth_campaigns.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lead_magnets_business_active', 'lead_magnets', ['business_id', 'is_active'], unique=False)
    op.create_index('ix_lead_magnets_business_format', 'lead_magnets', ['business_id', 'format'], unique=False)
    op.create_index(op.f('ix_lead_magnets_business_id'), 'lead_magnets', ['business_id'], unique=False)
    op.create_index(op.f('ix_lead_magnets_campaign_id'), 'lead_magnets', ['campaign_id'], unique=False)
    op.create_table('optimization_results',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('experiment_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('variant_a_conversions', sa.Integer(), nullable=False),
    sa.Column('variant_a_total', sa.Integer(), nullable=False),
    sa.Column('variant_a_rate', sa.Numeric(precision=5, scale=4), nullable=False),
    sa.Column('variant_b_conversions', sa.Integer(), nullable=False),
    sa.Column('variant_b_total', sa.Integer(), nullable=False),
    sa.Column('variant_b_rate', sa.Numeric(precision=5, scale=4), nullable=False),
    sa.Column('improvement_percent', sa.Numeric(precision=7, scale=2), nullable=False),
    sa.Column('is_statistically_significant', sa.Boolean(), nullable=False),
    sa.Column('p_value', sa.Numeric(precision=6, scale=5), nullable=True),
    sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['experiment_id'], ['optimization_experiments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_optimization_results_business_id'), 'optimization_results', ['business_id'], unique=False)
    op.create_index(op.f('ix_optimization_results_experiment_id'), 'optimization_results', ['experiment_id'], unique=False)
    op.create_table('seller_performances',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('seller_id', sa.UUID(), nullable=False),
    sa.Column('period', sa.String(length=20), nullable=False),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('leads_acquired', sa.Integer(), nullable=False),
    sa.Column('messages_sent', sa.Integer(), nullable=False),
    sa.Column('conversations_active', sa.Integer(), nullable=False),
    sa.Column('deals_won', sa.Integer(), nullable=False),
    sa.Column('revenue', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('conversion_rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('best_performing_hour', sa.Integer(), nullable=True),
    sa.Column('best_performing_content_type', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['seller_id'], ['social_sellers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seller_performances_seller_id'), 'seller_performances', ['seller_id'], unique=False)
    op.create_table('sequence_steps',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('sequence_id', sa.UUID(), nullable=False),
    sa.Column('step_order', sa.Integer(), nullable=False),
    sa.Column('delay_hours', sa.Integer(), nullable=False),
    sa.Column('delay_minutes', sa.Integer(), nullable=False),
    sa.Column('template_id', sa.UUID(), nullable=True),
    sa.Column('subject_override', sa.String(length=500), nullable=True),
    sa.Column('body_override', sa.Text(), nullable=True),
    sa.Column('condition', sa.String(length=200), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['sequence_id'], ['email_sequences.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sequence_steps_sequence_id'), 'sequence_steps', ['sequence_id'], unique=False)
    op.create_table('ticket_messages',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('ticket_id', sa.UUID(), nullable=False),
    sa.Column('sender_type', sa.Enum('USER', 'AGENT', 'SYSTEM', 'AI', name='messagesendertype'), nullable=False),
    sa.Column('sender_id', sa.UUID(), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('is_internal', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ticket_messages_ticket_id'), 'ticket_messages', ['ticket_id'], unique=False)
    op.create_table('value_sequences',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('campaign_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('topic', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('messages', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('message_count', sa.Integer(), nullable=False),
    sa.Column('total_duration_days', sa.Integer(), nullable=False),
    sa.Column('target_segment', sa.String(length=50), nullable=False),
    sa.Column('target_source', sa.String(length=50), nullable=True),
    sa.Column('times_started', sa.Integer(), nullable=False),
    sa.Column('times_completed', sa.Integer(), nullable=False),
    sa.Column('conversion_rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('avg_engagement_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['campaign_id'], ['growth_campaigns.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_value_sequences_business_active', 'value_sequences', ['business_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_value_sequences_business_id'), 'value_sequences', ['business_id'], unique=False)
    op.create_index(op.f('ix_value_sequences_campaign_id'), 'value_sequences', ['campaign_id'], unique=False)
    op.create_table('workflow_variants',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('workflow_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('variant_name', sa.String(length=100), nullable=False),
    sa.Column('traffic_split', sa.Integer(), nullable=False),
    sa.Column('actions', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('execution_count', sa.Integer(), nullable=True),
    sa.Column('conversion_count', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workflow_id'], ['automation_workflows.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_variants_business_id'), 'workflow_variants', ['business_id'], unique=False)
    op.create_index(op.f('ix_workflow_variants_workflow_id'), 'workflow_variants', ['workflow_id'], unique=False)
    op.create_table('automation_workflow_executions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('workflow_id', sa.UUID(), nullable=False),
    sa.Column('variant_id', sa.UUID(), nullable=True),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('trigger_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('actions_executed', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['variant_id'], ['workflow_variants.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['workflow_id'], ['automation_workflows.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_workflow_executions_variant_id'), 'automation_workflow_executions', ['variant_id'], unique=False)
    op.create_index(op.f('ix_automation_workflow_executions_workflow_id'), 'automation_workflow_executions', ['workflow_id'], unique=False)
    op.create_table('churn_predictions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='churnrisklevel'), nullable=False),
    sa.Column('churn_probability', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('predicted_churn_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('factors', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('recommended_action', sa.String(length=255), nullable=True),
    sa.Column('model_version', sa.String(length=20), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_churn_predictions_business_id'), 'churn_predictions', ['business_id'], unique=False)
    op.create_index('ix_churn_predictions_business_risk', 'churn_predictions', ['business_id', 'risk_level'], unique=False)
    op.create_index(op.f('ix_churn_predictions_conversation_id'), 'churn_predictions', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_churn_predictions_risk_level'), 'churn_predictions', ['risk_level'], unique=False)
    op.create_table('computer_use_annotations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('step_number', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('x_coordinate', sa.Integer(), nullable=True),
    sa.Column('y_coordinate', sa.Integer(), nullable=True),
    sa.Column('color', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['computer_use_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_annotations_session_id'), 'computer_use_annotations', ['session_id'], unique=False)
    op.create_table('computer_use_messages',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('role', sa.Enum('user', 'agent', 'system', name='computer_use_message_role'), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['computer_use_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_messages_session_id'), 'computer_use_messages', ['session_id'], unique=False)
    op.create_table('computer_use_scheduled_tasks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('task_description', sa.Text(), nullable=False),
    sa.Column('start_url', sa.String(length=2048), nullable=True),
    sa.Column('cron_expression', sa.String(length=100), nullable=False),
    sa.Column('timezone', sa.String(length=50), nullable=True),
    sa.Column('provider', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('max_steps', sa.Integer(), nullable=True),
    sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_session_id', sa.UUID(), nullable=True),
    sa.Column('total_runs', sa.Integer(), nullable=True),
    sa.Column('success_count', sa.Integer(), nullable=True),
    sa.Column('fail_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['last_session_id'], ['computer_use_sessions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_scheduled_tasks_user_id'), 'computer_use_scheduled_tasks', ['user_id'], unique=False)
    op.create_table('computer_use_session_bookmarks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('step_number', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('label', sa.String(length=200), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['computer_use_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_session_bookmarks_session_id'), 'computer_use_session_bookmarks', ['session_id'], unique=False)
    op.create_table('computer_use_session_notes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('is_pinned', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['computer_use_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_session_notes_session_id'), 'computer_use_session_notes', ['session_id'], unique=False)
    op.create_table('computer_use_session_shares',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('shared_by_user_id', sa.UUID(), nullable=False),
    sa.Column('shared_with_user_id', sa.UUID(), nullable=True),
    sa.Column('shared_with_email', sa.String(length=255), nullable=True),
    sa.Column('permission', sa.Enum('view', 'comment', 'control', name='share_permission'), nullable=True),
    sa.Column('token', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['computer_use_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shared_by_user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shared_with_user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id', 'shared_with_user_id', name='uq_session_share_user')
    )
    op.create_index(op.f('ix_computer_use_session_shares_session_id'), 'computer_use_session_shares', ['session_id'], unique=False)
    op.create_index(op.f('ix_computer_use_session_shares_token'), 'computer_use_session_shares', ['token'], unique=True)
    op.create_table('computer_use_session_tags',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('tag', sa.String(length=50), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['computer_use_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id', 'tag', name='uq_session_tag')
    )
    op.create_index(op.f('ix_computer_use_session_tags_session_id'), 'computer_use_session_tags', ['session_id'], unique=False)
    op.create_index(op.f('ix_computer_use_session_tags_tag'), 'computer_use_session_tags', ['tag'], unique=False)
    op.create_table('computer_use_steps',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('step_number', sa.Integer(), nullable=False),
    sa.Column('screenshot_path', sa.String(length=512), nullable=True),
    sa.Column('llm_prompt', sa.Text(), nullable=True),
    sa.Column('llm_response', sa.Text(), nullable=True),
    sa.Column('action_type', sa.Enum('click', 'double_click', 'right_click', 'type', 'scroll', 'navigate', 'wait', 'screenshot', 'done', 'error', 'pause_requested', name='computer_use_action_type'), nullable=False),
    sa.Column('action_params', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('execution_result', sa.Text(), nullable=True),
    sa.Column('execution_ms', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['computer_use_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_computer_use_steps_session_id'), 'computer_use_steps', ['session_id'], unique=False)
    op.create_table('contact_fatigue_scores',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('total_contacts_last_7d', sa.Integer(), nullable=False),
    sa.Column('total_contacts_last_30d', sa.Integer(), nullable=False),
    sa.Column('contacts_by_channel', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('last_contact_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_response_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('consecutive_no_replies', sa.Integer(), nullable=False),
    sa.Column('fatigue_level', sa.Enum('RELAXED', 'NORMAL', 'TIRED', 'EXHAUSTED', name='fatiguelevel'), nullable=False),
    sa.Column('recommended_cooldown_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ai_recommendation', sa.Text(), nullable=True),
    sa.Column('recommended_channel', sa.String(length=50), nullable=True),
    sa.Column('recommended_message_type', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contact_fatigue_scores_business_id'), 'contact_fatigue_scores', ['business_id'], unique=False)
    op.create_index(op.f('ix_contact_fatigue_scores_conversation_id'), 'contact_fatigue_scores', ['conversation_id'], unique=True)
    op.create_index(op.f('ix_contact_fatigue_scores_fatigue_level'), 'contact_fatigue_scores', ['fatigue_level'], unique=False)
    op.create_index('ix_fatigue_business_level', 'contact_fatigue_scores', ['business_id', 'fatigue_level'], unique=False)
    op.create_index('ix_fatigue_cooldown', 'contact_fatigue_scores', ['recommended_cooldown_until'], unique=False)
    op.create_table('conversation_intelligences',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('overall_sentiment_trend', sa.String(length=20), nullable=False),
    sa.Column('average_sentiment_score', sa.Numeric(precision=4, scale=3), nullable=False),
    sa.Column('dominant_intent', sa.String(length=50), nullable=False),
    sa.Column('buying_readiness_score', sa.Integer(), nullable=False),
    sa.Column('objection_history', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('churn_risk_signals_count', sa.Integer(), nullable=False),
    sa.Column('next_best_action', sa.String(length=50), nullable=True),
    sa.Column('next_best_action_reason', sa.Text(), nullable=True),
    sa.Column('total_messages_analyzed', sa.Integer(), nullable=False),
    sa.Column('positive_messages_count', sa.Integer(), nullable=False),
    sa.Column('negative_messages_count', sa.Integer(), nullable=False),
    sa.Column('buying_signals_count', sa.Integer(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conv_intel_business_intent', 'conversation_intelligences', ['business_id', 'dominant_intent'], unique=False)
    op.create_index('ix_conv_intel_business_readiness', 'conversation_intelligences', ['business_id', 'buying_readiness_score'], unique=False)
    op.create_index(op.f('ix_conversation_intelligences_business_id'), 'conversation_intelligences', ['business_id'], unique=False)
    op.create_index(op.f('ix_conversation_intelligences_conversation_id'), 'conversation_intelligences', ['conversation_id'], unique=True)
    op.create_table('conversation_memory_chunks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('agent_id', sa.UUID(), nullable=True),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', app.domains.memory.models.Vector(768), nullable=True),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_memory_chunks_agent_id'), 'conversation_memory_chunks', ['agent_id'], unique=False)
    op.create_index(op.f('ix_conversation_memory_chunks_business_id'), 'conversation_memory_chunks', ['business_id'], unique=False)
    op.create_index(op.f('ix_conversation_memory_chunks_conversation_id'), 'conversation_memory_chunks', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_memory_chunks_user_id'), 'conversation_memory_chunks', ['user_id'], unique=False)
    op.create_index('ix_memory_chunks_embedding_hnsw', 'conversation_memory_chunks', ['embedding'], unique=False, postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.create_table('conversation_outcomes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('agent_type', sa.String(length=50), nullable=False),
    sa.Column('outcome', sa.String(length=50), nullable=False),
    sa.Column('revenue', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('feedback', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('customer_badge_assignments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('badge_id', sa.UUID(), nullable=False),
    sa.Column('customer_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('earned_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('awarded_by_seller_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['awarded_by_seller_id'], ['social_sellers.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['badge_id'], ['customer_loyalty_badges.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['customer_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('customer_memories',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('customer_id', sa.UUID(), nullable=False),
    sa.Column('memory_type', sa.String(length=50), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', app.domains.memory.models.Vector(768), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('source_conversation_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['source_conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_memories_business_id'), 'customer_memories', ['business_id'], unique=False)
    op.create_index(op.f('ix_customer_memories_customer_id'), 'customer_memories', ['customer_id'], unique=False)
    op.create_index('ix_customer_memories_embedding_hnsw', 'customer_memories', ['embedding'], unique=False, postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.create_index(op.f('ix_customer_memories_memory_type'), 'customer_memories', ['memory_type'], unique=False)
    op.create_table('customer_segments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('segment', sa.Enum('CHAMPIONS', 'LOYAL', 'POTENTIAL', 'NEW', 'AT_RISK', 'LOST', name='customersegmenttype'), nullable=False),
    sa.Column('r_score', sa.Integer(), nullable=False),
    sa.Column('f_score', sa.Integer(), nullable=False),
    sa.Column('m_score', sa.Integer(), nullable=False),
    sa.Column('rfm_score', sa.Integer(), nullable=False),
    sa.Column('last_order_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('total_orders', sa.Integer(), nullable=False),
    sa.Column('total_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('avg_order_value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_segments_business_id'), 'customer_segments', ['business_id'], unique=False)
    op.create_index('ix_customer_segments_business_segment', 'customer_segments', ['business_id', 'segment'], unique=False)
    op.create_index(op.f('ix_customer_segments_conversation_id'), 'customer_segments', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_customer_segments_segment'), 'customer_segments', ['segment'], unique=False)
    op.create_table('deals',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('pipeline_id', sa.UUID(), nullable=True),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=300), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('contact_name', sa.String(length=255), nullable=True),
    sa.Column('contact_email', sa.String(length=255), nullable=True),
    sa.Column('contact_phone', sa.String(length=100), nullable=True),
    sa.Column('value', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('stage', sa.Enum('NEW_LEAD', 'CONTACTED', 'QUALIFIED', 'PROPOSAL_SENT', 'NEGOTIATING', 'CLOSED_WON', 'CLOSED_LOST', 'NURTURE', name='leadstage'), nullable=False),
    sa.Column('stage_order', sa.Integer(), nullable=False),
    sa.Column('probability', sa.Integer(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('expected_close_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_close_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('close_reason', sa.Text(), nullable=True),
    sa.Column('source_channel', sa.String(length=50), nullable=True),
    sa.Column('source_campaign', sa.String(length=200), nullable=True),
    sa.Column('source_agent_id', sa.UUID(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deals_business_id'), 'deals', ['business_id'], unique=False)
    op.create_index(op.f('ix_deals_conversation_id'), 'deals', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_deals_pipeline_id'), 'deals', ['pipeline_id'], unique=False)
    op.create_index(op.f('ix_deals_stage'), 'deals', ['stage'], unique=False)
    op.create_table('health_score_histories',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('health_score', sa.Integer(), nullable=False),
    sa.Column('trend', sa.String(length=20), nullable=False),
    sa.Column('churn_risk_level', sa.String(length=20), nullable=False),
    sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_health_histories_conv_date', 'health_score_histories', ['conversation_id', 'calculated_at'], unique=False)
    op.create_index(op.f('ix_health_score_histories_business_id'), 'health_score_histories', ['business_id'], unique=False)
    op.create_index(op.f('ix_health_score_histories_conversation_id'), 'health_score_histories', ['conversation_id'], unique=False)
    op.create_table('health_score_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('health_score', sa.Integer(), nullable=False),
    sa.Column('trend', sa.String(length=20), nullable=False),
    sa.Column('churn_risk_level', sa.String(length=20), nullable=False),
    sa.Column('recommended_action', sa.Text(), nullable=True),
    sa.Column('last_order_days', sa.Integer(), nullable=False),
    sa.Column('engagement_score', sa.Integer(), nullable=False),
    sa.Column('nps_score', sa.Integer(), nullable=True),
    sa.Column('support_ticket_count', sa.Integer(), nullable=False),
    sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_health_score_records_business_id'), 'health_score_records', ['business_id'], unique=False)
    op.create_index(op.f('ix_health_score_records_churn_risk_level'), 'health_score_records', ['churn_risk_level'], unique=False)
    op.create_index(op.f('ix_health_score_records_conversation_id'), 'health_score_records', ['conversation_id'], unique=True)
    op.create_index('ix_health_scores_business_risk', 'health_score_records', ['business_id', 'churn_risk_level'], unique=False)
    op.create_table('key_results',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('objective_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('target_value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('current_value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('weight', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'ACHIEVED', 'AT_RISK', 'MISSED', 'PAUSED', name='objectivestatus'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['objective_id'], ['business_objectives.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_key_results_objective_id'), 'key_results', ['objective_id'], unique=False)
    op.create_table('kpis',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('department_id', sa.UUID(), nullable=True),
    sa.Column('objective_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('slug', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('metric_type', sa.String(length=50), nullable=False),
    sa.Column('aggregation', sa.String(length=20), nullable=False),
    sa.Column('target_value', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('current_value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('period', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY', 'CUSTOM', name='objectiveperiod'), nullable=False),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('data_source', sa.String(length=100), nullable=False),
    sa.Column('data_source_filter', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['objective_id'], ['business_objectives.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kpis_business_id'), 'kpis', ['business_id'], unique=False)
    op.create_index('ix_kpis_business_slug_period', 'kpis', ['business_id', 'slug', 'period'], unique=False)
    op.create_index(op.f('ix_kpis_department_id'), 'kpis', ['department_id'], unique=False)
    op.create_index(op.f('ix_kpis_objective_id'), 'kpis', ['objective_id'], unique=False)
    op.create_index(op.f('ix_kpis_slug'), 'kpis', ['slug'], unique=False)
    op.create_table('lead_activities',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('activity_type', sa.String(length=50), nullable=False),
    sa.Column('points', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_activities_activity_type'), 'lead_activities', ['activity_type'], unique=False)
    op.create_index(op.f('ix_lead_activities_business_id'), 'lead_activities', ['business_id'], unique=False)
    op.create_index(op.f('ix_lead_activities_conversation_id'), 'lead_activities', ['conversation_id'], unique=False)
    op.create_table('lead_scores',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('total_score', sa.Integer(), nullable=False),
    sa.Column('engagement_score', sa.Integer(), nullable=False),
    sa.Column('intent_score', sa.Integer(), nullable=False),
    sa.Column('demographic_score', sa.Integer(), nullable=False),
    sa.Column('behavioral_score', sa.Integer(), nullable=False),
    sa.Column('recency_score', sa.Integer(), nullable=False),
    sa.Column('score_history', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('classification', sa.String(length=20), nullable=False),
    sa.Column('commentary', sa.Text(), nullable=True),
    sa.Column('last_calculated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_scores_business_id'), 'lead_scores', ['business_id'], unique=False)
    op.create_index(op.f('ix_lead_scores_conversation_id'), 'lead_scores', ['conversation_id'], unique=True)
    op.create_index(op.f('ix_lead_scores_total_score'), 'lead_scores', ['total_score'], unique=False)
    op.create_table('ltv_predictions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('predicted_ltv', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('predicted_orders', sa.Integer(), nullable=False),
    sa.Column('prediction_horizon_months', sa.Integer(), nullable=False),
    sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('factors', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('model_version', sa.String(length=20), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ltv_predictions_business_id'), 'ltv_predictions', ['business_id'], unique=False)
    op.create_index('ix_ltv_predictions_business_ltv', 'ltv_predictions', ['business_id', 'predicted_ltv'], unique=False)
    op.create_index(op.f('ix_ltv_predictions_conversation_id'), 'ltv_predictions', ['conversation_id'], unique=False)
    op.create_table('messages',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('direction', sa.Enum('INBOUND', 'OUTBOUND', name='messagedirection'), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('content_type', sa.String(length=50), nullable=False),
    sa.Column('status', sa.Enum('SENT', 'DELIVERED', 'READ', 'FAILED', 'PENDING', name='messagestatus'), nullable=False),
    sa.Column('external_message_id', sa.String(length=255), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_conversation_created', 'messages', ['conversation_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_table('outreach_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('channel', sa.String(length=50), nullable=False),
    sa.Column('message_type', sa.String(length=50), nullable=False),
    sa.Column('cadence_step', sa.Integer(), nullable=False),
    sa.Column('message_content', sa.Text(), nullable=True),
    sa.Column('workflow_execution_id', sa.UUID(), nullable=True),
    sa.Column('sequence_step_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.Enum('SENT', 'DELIVERED', 'READ', 'RESPONDED', 'FAILED', name='outreachlogstatus'), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('response_type', sa.String(length=50), nullable=True),
    sa.Column('response_content', sa.Text(), nullable=True),
    sa.Column('ai_generated', sa.Boolean(), nullable=False),
    sa.Column('ai_prompt_summary', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_outreach_logs_business_channel', 'outreach_logs', ['business_id', 'channel'], unique=False)
    op.create_index(op.f('ix_outreach_logs_business_id'), 'outreach_logs', ['business_id'], unique=False)
    op.create_index(op.f('ix_outreach_logs_channel'), 'outreach_logs', ['channel'], unique=False)
    op.create_index('ix_outreach_logs_conv_sent', 'outreach_logs', ['conversation_id', 'sent_at'], unique=False)
    op.create_index(op.f('ix_outreach_logs_conversation_id'), 'outreach_logs', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_outreach_logs_status'), 'outreach_logs', ['status'], unique=False)
    op.create_table('referral_codes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('referrer_name', sa.String(length=255), nullable=True),
    sa.Column('referrer_email', sa.String(length=255), nullable=True),
    sa.Column('total_uses', sa.Integer(), nullable=False),
    sa.Column('total_conversions', sa.Integer(), nullable=False),
    sa.Column('total_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['program_id'], ['referral_programs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_referral_codes_business', 'referral_codes', ['business_id', 'code'], unique=False)
    op.create_index(op.f('ix_referral_codes_business_id'), 'referral_codes', ['business_id'], unique=False)
    op.create_index(op.f('ix_referral_codes_code'), 'referral_codes', ['code'], unique=True)
    op.create_index(op.f('ix_referral_codes_conversation_id'), 'referral_codes', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_referral_codes_program_id'), 'referral_codes', ['program_id'], unique=False)
    op.create_table('seller_customer_relationships',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('seller_id', sa.UUID(), nullable=False),
    sa.Column('customer_id', sa.UUID(), nullable=False),
    sa.Column('first_contact_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_contact_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('total_interactions', sa.Integer(), nullable=False),
    sa.Column('deals_closed', sa.Integer(), nullable=False),
    sa.Column('total_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('relationship_stage', sa.String(length=30), nullable=False),
    sa.Column('loyalty_score', sa.Integer(), nullable=False),
    sa.Column('next_best_action', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['seller_id'], ['social_sellers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seller_customer_relationships_customer_id'), 'seller_customer_relationships', ['customer_id'], unique=False)
    op.create_index(op.f('ix_seller_customer_relationships_seller_id'), 'seller_customer_relationships', ['seller_id'], unique=False)
    op.create_table('sequence_subscriptions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('sequence_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('current_step_index', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sequence_id'], ['email_sequences.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sequence_subscriptions_business_id'), 'sequence_subscriptions', ['business_id'], unique=False)
    op.create_index(op.f('ix_sequence_subscriptions_conversation_id'), 'sequence_subscriptions', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_sequence_subscriptions_sequence_id'), 'sequence_subscriptions', ['sequence_id'], unique=False)
    op.create_table('voice_calls',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('customer_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('phone_number', sa.String(length=50), nullable=False),
    sa.Column('direction', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('recording_url', sa.String(length=500), nullable=True),
    sa.Column('recording_duration', sa.Integer(), nullable=True),
    sa.Column('transcript', sa.Text(), nullable=True),
    sa.Column('transcript_segments', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('ai_summary', sa.Text(), nullable=True),
    sa.Column('outcome', sa.String(length=50), nullable=True),
    sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voice_calls_business_id'), 'voice_calls', ['business_id'], unique=False)
    op.create_index(op.f('ix_voice_calls_customer_id'), 'voice_calls', ['customer_id'], unique=False)
    op.create_table('generated_contents',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('catalog_item_id', sa.UUID(), nullable=True),
    sa.Column('workflow_execution_id', sa.UUID(), nullable=True),
    sa.Column('content_type', sa.String(length=50), nullable=False),
    sa.Column('agent_slug', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=True),
    sa.Column('negative_prompt', sa.Text(), nullable=True),
    sa.Column('generation_config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('source_url', sa.String(length=1000), nullable=True),
    sa.Column('thumbnail_url', sa.String(length=1000), nullable=True),
    sa.Column('text_content', sa.Text(), nullable=True),
    sa.Column('variations', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('platform', sa.String(length=50), nullable=True),
    sa.Column('purpose', sa.String(length=100), nullable=True),
    sa.Column('usage_count', sa.Integer(), nullable=True),
    sa.Column('performance_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('reviewed_by', sa.UUID(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('approval_status', sa.String(length=50), nullable=False),
    sa.Column('feedback_notes', sa.Text(), nullable=True),
    sa.Column('generation_cost', sa.Integer(), nullable=False),
    sa.Column('ai_model_used', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['catalog_item_id'], ['catalog_items.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['workflow_execution_id'], ['automation_workflow_executions.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_gencontent_business_agent', 'generated_contents', ['business_id', 'agent_slug'], unique=False)
    op.create_index('idx_gencontent_business_approval', 'generated_contents', ['business_id', 'approval_status'], unique=False)
    op.create_index('idx_gencontent_business_type_status', 'generated_contents', ['business_id', 'content_type', 'status'], unique=False)
    op.create_index('idx_gencontent_catalog_status', 'generated_contents', ['catalog_item_id', 'status'], unique=False)
    op.create_index('idx_gencontent_config_gin', 'generated_contents', ['generation_config'], unique=False, postgresql_using='gin')
    op.create_index('idx_gencontent_perf_gin', 'generated_contents', ['performance_data'], unique=False, postgresql_using='gin')
    op.create_index('idx_gencontent_status_created', 'generated_contents', ['status', 'created_at'], unique=False)
    op.create_index('idx_gencontent_variations_gin', 'generated_contents', ['variations'], unique=False, postgresql_using='gin')
    op.create_index(op.f('ix_generated_contents_business_id'), 'generated_contents', ['business_id'], unique=False)
    op.create_index(op.f('ix_generated_contents_catalog_item_id'), 'generated_contents', ['catalog_item_id'], unique=False)
    op.create_index(op.f('ix_generated_contents_workflow_execution_id'), 'generated_contents', ['workflow_execution_id'], unique=False)
    op.create_table('inbound_leads',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('campaign_id', sa.UUID(), nullable=True),
    sa.Column('lead_magnet_id', sa.UUID(), nullable=True),
    sa.Column('source_type', sa.Enum('SEO', 'SOCIAL_POST', 'LEAD_MAGNET', 'REFERRAL', 'COMMENT_DM', 'STORY_REPLY', 'ORGANIC_SEARCH', 'DIRECT', 'COMMUNITY', name='inboundleadsource'), nullable=False),
    sa.Column('source_detail', sa.String(length=200), nullable=True),
    sa.Column('source_campaign_id', sa.UUID(), nullable=True),
    sa.Column('referral_code_id', sa.UUID(), nullable=True),
    sa.Column('contact_info', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('nurturing_stage', sa.Enum('NEW', 'AWARENESS', 'INTEREST', 'CONSIDERATION', 'EVALUATION', 'CONVERTED', 'DORMANT', name='nurturingstage'), nullable=False),
    sa.Column('engagement_score', sa.Integer(), nullable=False),
    sa.Column('value_touches_received', sa.Integer(), nullable=False),
    sa.Column('sales_touches_received', sa.Integer(), nullable=False),
    sa.Column('first_touch_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_touch_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('converted_to_deal_id', sa.UUID(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['campaign_id'], ['growth_campaigns.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['converted_to_deal_id'], ['deals.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['lead_magnet_id'], ['lead_magnets.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['referral_code_id'], ['referral_codes.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['source_campaign_id'], ['growth_campaigns.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inbound_leads_business_id'), 'inbound_leads', ['business_id'], unique=False)
    op.create_index('ix_inbound_leads_business_source', 'inbound_leads', ['business_id', 'source_type'], unique=False)
    op.create_index('ix_inbound_leads_business_stage', 'inbound_leads', ['business_id', 'nurturing_stage'], unique=False)
    op.create_index(op.f('ix_inbound_leads_campaign_id'), 'inbound_leads', ['campaign_id'], unique=False)
    op.create_index('ix_inbound_leads_conversation', 'inbound_leads', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_inbound_leads_conversation_id'), 'inbound_leads', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_inbound_leads_lead_magnet_id'), 'inbound_leads', ['lead_magnet_id'], unique=False)
    op.create_index(op.f('ix_inbound_leads_nurturing_stage'), 'inbound_leads', ['nurturing_stage'], unique=False)
    op.create_index(op.f('ix_inbound_leads_source_type'), 'inbound_leads', ['source_type'], unique=False)
    op.create_table('message_analyses',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('message_id', sa.UUID(), nullable=False),
    sa.Column('sentiment_score', sa.Numeric(precision=4, scale=3), nullable=False),
    sa.Column('sentiment_label', sa.String(length=20), nullable=False),
    sa.Column('intent_type', sa.String(length=50), nullable=False),
    sa.Column('intent_confidence', sa.Numeric(precision=4, scale=3), nullable=False),
    sa.Column('objections_detected', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('pain_points_detected', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('buying_signals_detected', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('urgency_level', sa.String(length=20), nullable=False),
    sa.Column('language_detected', sa.String(length=10), nullable=False),
    sa.Column('key_entities', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('recommended_action', sa.String(length=50), nullable=True),
    sa.Column('recommended_personality', sa.String(length=50), nullable=True),
    sa.Column('raw_analysis', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_analyses_business_id'), 'message_analyses', ['business_id'], unique=False)
    op.create_index('ix_message_analyses_business_intent', 'message_analyses', ['business_id', 'intent_type'], unique=False)
    op.create_index('ix_message_analyses_conversation', 'message_analyses', ['conversation_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_message_analyses_conversation_id'), 'message_analyses', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_message_analyses_intent_type'), 'message_analyses', ['intent_type'], unique=False)
    op.create_index(op.f('ix_message_analyses_message_id'), 'message_analyses', ['message_id'], unique=True)
    op.create_table('orders',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('deal_id', sa.UUID(), nullable=True),
    sa.Column('order_number', sa.String(length=50), nullable=True),
    sa.Column('items', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('total_amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('shipping_cost', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'PAID', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED', name='orderstatus'), nullable=False),
    sa.Column('payment_method', sa.String(length=50), nullable=True),
    sa.Column('payment_status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', name='paymentstatus'), nullable=False),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('payment_reference', sa.String(length=255), nullable=True),
    sa.Column('payment_gateway', sa.String(length=50), nullable=True),
    sa.Column('shipping_address', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('shipping_provider', sa.String(length=50), nullable=True),
    sa.Column('tracking_number', sa.String(length=100), nullable=True),
    sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('source_channel', sa.String(length=50), nullable=True),
    sa.Column('source_campaign', sa.String(length=200), nullable=True),
    sa.Column('source_workflow_id', sa.UUID(), nullable=True),
    sa.Column('source_agent_id', sa.UUID(), nullable=True),
    sa.Column('first_touch_channel', sa.String(length=50), nullable=True),
    sa.Column('last_touch_channel', sa.String(length=50), nullable=True),
    sa.Column('attribution_model', sa.String(length=20), nullable=False),
    sa.Column('customer_name', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('customer_email', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('customer_phone', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('external_id', sa.String(length=100), nullable=True),
    sa.Column('external_platform', sa.String(length=50), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_business_id'), 'orders', ['business_id'], unique=False)
    op.create_index(op.f('ix_orders_conversation_id'), 'orders', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_orders_deal_id'), 'orders', ['deal_id'], unique=False)
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_source_agent_id'), 'orders', ['source_agent_id'], unique=False)
    op.create_index(op.f('ix_orders_source_channel'), 'orders', ['source_channel'], unique=False)
    op.create_index(op.f('ix_orders_source_workflow_id'), 'orders', ['source_workflow_id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_table('sequence_email_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('subscription_id', sa.UUID(), nullable=False),
    sa.Column('sequence_id', sa.UUID(), nullable=False),
    sa.Column('step_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('recipient_email', sa.String(length=255), nullable=False),
    sa.Column('subject', sa.String(length=500), nullable=True),
    sa.Column('tracking_token', sa.String(length=64), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sequence_id'], ['email_sequences.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['step_id'], ['sequence_steps.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subscription_id'], ['sequence_subscriptions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sequence_email_logs_business_id'), 'sequence_email_logs', ['business_id'], unique=False)
    op.create_index(op.f('ix_sequence_email_logs_conversation_id'), 'sequence_email_logs', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_sequence_email_logs_sequence_id'), 'sequence_email_logs', ['sequence_id'], unique=False)
    op.create_index(op.f('ix_sequence_email_logs_step_id'), 'sequence_email_logs', ['step_id'], unique=False)
    op.create_index(op.f('ix_sequence_email_logs_subscription_id'), 'sequence_email_logs', ['subscription_id'], unique=False)
    op.create_index(op.f('ix_sequence_email_logs_tracking_token'), 'sequence_email_logs', ['tracking_token'], unique=True)
    op.create_table('alerts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('rule_id', sa.UUID(), nullable=True),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('deal_id', sa.UUID(), nullable=True),
    sa.Column('order_id', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('severity', sa.Enum('INFO', 'WARNING', 'CRITICAL', name='alertseverity'), nullable=False),
    sa.Column('status', sa.Enum('UNREAD', 'READ', 'DISMISSED', name='alertstatus'), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=True),
    sa.Column('entity_id', sa.UUID(), nullable=True),
    sa.Column('recommended_action', sa.Text(), nullable=True),
    sa.Column('alert_metadata', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['rule_id'], ['alert_rules.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_business_id'), 'alerts', ['business_id'], unique=False)
    op.create_index(op.f('ix_alerts_conversation_id'), 'alerts', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_alerts_deal_id'), 'alerts', ['deal_id'], unique=False)
    op.create_index(op.f('ix_alerts_order_id'), 'alerts', ['order_id'], unique=False)
    op.create_index(op.f('ix_alerts_rule_id'), 'alerts', ['rule_id'], unique=False)
    op.create_index(op.f('ix_alerts_status'), 'alerts', ['status'], unique=False)
    op.create_table('content_calendar',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('generated_content_id', sa.UUID(), nullable=True),
    sa.Column('catalog_item_id', sa.UUID(), nullable=True),
    sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('timezone', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('platform', sa.String(length=50), nullable=False),
    sa.Column('content_format', sa.String(length=50), nullable=False),
    sa.Column('channel_connection_id', sa.UUID(), nullable=True),
    sa.Column('caption', sa.Text(), nullable=True),
    sa.Column('hashtags', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('alt_text', sa.Text(), nullable=True),
    sa.Column('media_urls', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('cta_text', sa.String(length=500), nullable=True),
    sa.Column('link_in_bio', sa.String(length=1000), nullable=True),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('published_by', sa.UUID(), nullable=True),
    sa.Column('external_post_id', sa.String(length=500), nullable=True),
    sa.Column('external_url', sa.String(length=1000), nullable=True),
    sa.Column('reach', sa.Integer(), nullable=True),
    sa.Column('impressions', sa.Integer(), nullable=True),
    sa.Column('engagement', sa.Integer(), nullable=True),
    sa.Column('clicks', sa.Integer(), nullable=True),
    sa.Column('conversions', sa.Integer(), nullable=True),
    sa.Column('revenue', sa.Integer(), nullable=True),
    sa.Column('workflow_id', sa.UUID(), nullable=True),
    sa.Column('auto_publish', sa.Boolean(), nullable=False),
    sa.Column('requires_approval', sa.Boolean(), nullable=False),
    sa.Column('approved_by', sa.UUID(), nullable=True),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['catalog_item_id'], ['catalog_items.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['channel_connection_id'], ['channel_connections.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['generated_content_id'], ['generated_contents.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['published_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['workflow_id'], ['automation_workflows.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_calendar_business_platform', 'content_calendar', ['business_id', 'platform'], unique=False)
    op.create_index('idx_calendar_business_scheduled', 'content_calendar', ['business_id', 'scheduled_at'], unique=False)
    op.create_index('idx_calendar_business_status', 'content_calendar', ['business_id', 'status'], unique=False)
    op.create_index('idx_calendar_extra_gin', 'content_calendar', ['extra_data'], unique=False, postgresql_using='gin')
    op.create_index('idx_calendar_hashtags_gin', 'content_calendar', ['hashtags'], unique=False, postgresql_using='gin')
    op.create_index('idx_calendar_media_gin', 'content_calendar', ['media_urls'], unique=False, postgresql_using='gin')
    op.create_index('idx_calendar_status_scheduled', 'content_calendar', ['status', 'scheduled_at'], unique=False)
    op.create_index(op.f('ix_content_calendar_business_id'), 'content_calendar', ['business_id'], unique=False)
    op.create_index(op.f('ix_content_calendar_catalog_item_id'), 'content_calendar', ['catalog_item_id'], unique=False)
    op.create_index(op.f('ix_content_calendar_generated_content_id'), 'content_calendar', ['generated_content_id'], unique=False)
    op.create_index(op.f('ix_content_calendar_scheduled_at'), 'content_calendar', ['scheduled_at'], unique=False)
    op.create_table('nps_responses',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('campaign_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('order_id', sa.UUID(), nullable=True),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('feedback_text', sa.Text(), nullable=True),
    sa.Column('category', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['campaign_id'], ['nps_campaigns.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nps_responses_business_id'), 'nps_responses', ['business_id'], unique=False)
    op.create_index('ix_nps_responses_business_score', 'nps_responses', ['business_id', 'score'], unique=False)
    op.create_index(op.f('ix_nps_responses_campaign_id'), 'nps_responses', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_nps_responses_conversation_id'), 'nps_responses', ['conversation_id'], unique=False)
    op.create_table('referral_uses',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('code_id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('referred_conversation_id', sa.UUID(), nullable=True),
    sa.Column('referred_email', sa.String(length=255), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'CONVERTED', 'REWARDED', 'EXPIRED', name='referralstatus'), nullable=False),
    sa.Column('converted_order_id', sa.UUID(), nullable=True),
    sa.Column('reward_given', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['code_id'], ['referral_codes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['converted_order_id'], ['orders.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['referred_conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referral_uses_business_id'), 'referral_uses', ['business_id'], unique=False)
    op.create_index(op.f('ix_referral_uses_code_id'), 'referral_uses', ['code_id'], unique=False)
    op.create_table('revenue_events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('source_channel', sa.String(length=50), nullable=True),
    sa.Column('source_workflow_id', sa.UUID(), nullable=True),
    sa.Column('source_agent_id', sa.UUID(), nullable=True),
    sa.Column('source_campaign', sa.String(length=200), nullable=True),
    sa.Column('touchpoint_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_revenue_events_business_id'), 'revenue_events', ['business_id'], unique=False)
    op.create_index(op.f('ix_revenue_events_event_type'), 'revenue_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_revenue_events_order_id'), 'revenue_events', ['order_id'], unique=False)
    op.create_index(op.f('ix_revenue_events_source_agent_id'), 'revenue_events', ['source_agent_id'], unique=False)
    op.create_index(op.f('ix_revenue_events_source_channel'), 'revenue_events', ['source_channel'], unique=False)
    op.create_index(op.f('ix_revenue_events_source_workflow_id'), 'revenue_events', ['source_workflow_id'], unique=False)
    op.create_table('sales_invoices',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=True),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('invoice_number', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('total_amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('paid_amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('customer_name', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('customer_email', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('customer_phone', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('items', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_invoices_business_id'), 'sales_invoices', ['business_id'], unique=False)
    op.create_index('ix_sales_invoices_business_status', 'sales_invoices', ['business_id', 'status'], unique=False)
    op.create_index(op.f('ix_sales_invoices_invoice_number'), 'sales_invoices', ['invoice_number'], unique=True)
    op.create_index(op.f('ix_sales_invoices_order_id'), 'sales_invoices', ['order_id'], unique=False)
    op.create_table('service_deliveries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=False),
    sa.Column('catalog_item_id', sa.UUID(), nullable=True),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('modality', sa.Enum('HOME_OFFICE', 'CLIENT_OFFICE', 'CLIENT_HOME', 'PROVIDER_OFFICE', 'HYBRID', 'REMOTE', 'ON_SITE', name='servicemodality'), nullable=True),
    sa.Column('solution_type', sa.Enum('TEMPORARY', 'DEFINITIVE', 'CONTINGENCY', 'ANALYTICAL', 'HEURISTIC', 'CREATIVE', 'ARCHITECTURAL', 'DESIGN', 'IMPLEMENTATION', 'PREVENTIVE', 'CORRECTIVE', 'STRUCTURAL', 'INSTALLATION', 'DIAGNOSTIC', 'PROTECTION', 'AUTOMATION', 'COMFORT', 'PSYCHOLOGICAL', 'ADVISORY', 'EMOTIONAL', 'BEHAVIORAL', 'GUIDANCE', 'RELIEF', 'CAUSALITY', 'RITUAL', 'MEANING', 'COMMUNITY', 'MORAL', 'CONSOLATION', name='solutiontype'), nullable=True),
    sa.Column('status', sa.Enum('SCHEDULED', 'CONFIRMED', 'REMINDED', 'IN_PROGRESS', 'PAUSED', 'COMPLETED', 'CANCELLED', 'NO_SHOW', 'RESCHEDULED', name='servicedeliverystatus'), nullable=False),
    sa.Column('location_address', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('meeting_url', sa.Text(), nullable=True),
    sa.Column('provider_notes', sa.Text(), nullable=True),
    sa.Column('client_feedback', sa.Text(), nullable=True),
    sa.Column('client_rating', sa.Integer(), nullable=True),
    sa.Column('materials_used', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('diagnosis', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('follow_up_required', sa.Boolean(), nullable=False),
    sa.Column('follow_up_notes', sa.Text(), nullable=True),
    sa.Column('reminders_sent', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
    sa.Column('actual_duration_minutes', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['catalog_item_id'], ['catalog_items.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_deliveries_business_id'), 'service_deliveries', ['business_id'], unique=False)
    op.create_index(op.f('ix_service_deliveries_conversation_id'), 'service_deliveries', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_service_deliveries_order_id'), 'service_deliveries', ['order_id'], unique=False)
    op.create_index(op.f('ix_service_deliveries_status'), 'service_deliveries', ['status'], unique=False)
    op.create_table('shipments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=False),
    sa.Column('config_id', sa.UUID(), nullable=True),
    sa.Column('carrier', sa.Enum('ANDREANI', 'CORREO_ARGENTINO', 'OCA', 'MERCADO_ENVIOS', 'DHL', 'FEDEX', 'UPS', 'STARKEN', 'SERVIENTREGA', 'LOCAL', 'OTHER', name='carriertype'), nullable=False),
    sa.Column('service_type', sa.Enum('STANDARD', 'EXPRESS', 'SAME_DAY', 'OVERNIGHT', 'INTERNATIONAL', 'ECONOMY', name='servicetype'), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'LABEL_CREATED', 'PICKED_UP', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'EXCEPTION', 'RETURNED', 'CANCELLED', name='shipmentstatus'), nullable=False),
    sa.Column('tracking_number', sa.String(length=100), nullable=True),
    sa.Column('tracking_url', sa.Text(), nullable=True),
    sa.Column('label_url', sa.Text(), nullable=True),
    sa.Column('label_data', sa.Text(), nullable=True),
    sa.Column('from_address', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('to_address', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('package', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('shipping_cost', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('insurance_amount', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('declared_value', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('estimated_delivery_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_delivery_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('picked_up_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('customer_notified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('notification_channel', sa.String(length=50), nullable=True),
    sa.Column('carrier_response', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('last_tracking_check_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['config_id'], ['shipment_configs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shipments_business_id'), 'shipments', ['business_id'], unique=False)
    op.create_index(op.f('ix_shipments_order_id'), 'shipments', ['order_id'], unique=False)
    op.create_index(op.f('ix_shipments_status'), 'shipments', ['status'], unique=False)
    op.create_index(op.f('ix_shipments_tracking_number'), 'shipments', ['tracking_number'], unique=False)
    op.create_table('social_proofs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('order_id', sa.UUID(), nullable=True),
    sa.Column('item_type', sa.Enum('TESTIMONIAL', 'REVIEW', 'CASE_STUDY', 'RATING', 'VIDEO_TESTIMONIAL', 'BEFORE_AFTER', 'UGC_PHOTO', 'UGC_VIDEO', name='socialprooftype'), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'AUTO_APPROVED', name='socialproofstatus'), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('headline', sa.String(length=300), nullable=True),
    sa.Column('customer_name', sa.String(length=255), nullable=True),
    sa.Column('customer_photo_url', sa.String(length=500), nullable=True),
    sa.Column('media_urls', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('sentiment_score', sa.Numeric(precision=4, scale=3), nullable=False),
    sa.Column('ai_summary', sa.Text(), nullable=True),
    sa.Column('key_quotes', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('themes_detected', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('usage_count', sa.Integer(), nullable=False),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('used_in_campaigns', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('approved_by', sa.UUID(), nullable=True),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('rejection_reason', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_social_proofs_business_id'), 'social_proofs', ['business_id'], unique=False)
    op.create_index('ix_social_proofs_business_sentiment', 'social_proofs', ['business_id', 'sentiment_score'], unique=False)
    op.create_index('ix_social_proofs_business_status', 'social_proofs', ['business_id', 'status'], unique=False)
    op.create_index('ix_social_proofs_business_type', 'social_proofs', ['business_id', 'item_type'], unique=False)
    op.create_index(op.f('ix_social_proofs_conversation_id'), 'social_proofs', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_social_proofs_order_id'), 'social_proofs', ['order_id'], unique=False)
    op.create_table('value_sequence_enrollments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('sequence_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('inbound_lead_id', sa.UUID(), nullable=True),
    sa.Column('current_step', sa.Integer(), nullable=False),
    sa.Column('total_steps', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('messages_sent', sa.Integer(), nullable=False),
    sa.Column('messages_read', sa.Integer(), nullable=False),
    sa.Column('messages_replied', sa.Integer(), nullable=False),
    sa.Column('last_engagement_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('converted_to_deal_id', sa.UUID(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['converted_to_deal_id'], ['deals.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['inbound_lead_id'], ['inbound_leads.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['sequence_id'], ['value_sequences.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_value_enrollments_conversation', 'value_sequence_enrollments', ['conversation_id'], unique=False)
    op.create_index('ix_value_enrollments_sequence', 'value_sequence_enrollments', ['sequence_id', 'status'], unique=False)
    op.create_index(op.f('ix_value_sequence_enrollments_business_id'), 'value_sequence_enrollments', ['business_id'], unique=False)
    op.create_index(op.f('ix_value_sequence_enrollments_conversation_id'), 'value_sequence_enrollments', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_value_sequence_enrollments_sequence_id'), 'value_sequence_enrollments', ['sequence_id'], unique=False)
    op.create_table('appointments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('service_delivery_id', sa.UUID(), nullable=True),
    sa.Column('order_id', sa.UUID(), nullable=True),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('client_name', sa.String(length=255), nullable=True),
    sa.Column('client_email', sa.String(length=255), nullable=True),
    sa.Column('client_phone', sa.String(length=50), nullable=True),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('timezone', sa.String(length=50), nullable=False),
    sa.Column('modality', sa.Enum('HOME_OFFICE', 'CLIENT_OFFICE', 'CLIENT_HOME', 'PROVIDER_OFFICE', 'HYBRID', 'REMOTE', 'ON_SITE', name='servicemodality'), nullable=True),
    sa.Column('solution_type', sa.Enum('TEMPORARY', 'DEFINITIVE', 'CONTINGENCY', 'ANALYTICAL', 'HEURISTIC', 'CREATIVE', 'ARCHITECTURAL', 'DESIGN', 'IMPLEMENTATION', 'PREVENTIVE', 'CORRECTIVE', 'STRUCTURAL', 'INSTALLATION', 'DIAGNOSTIC', 'PROTECTION', 'AUTOMATION', 'COMFORT', 'PSYCHOLOGICAL', 'ADVISORY', 'EMOTIONAL', 'BEHAVIORAL', 'GUIDANCE', 'RELIEF', 'CAUSALITY', 'RITUAL', 'MEANING', 'COMMUNITY', 'MORAL', 'CONSOLATION', name='solutiontype'), nullable=True),
    sa.Column('service_name', sa.String(length=255), nullable=True),
    sa.Column('location_address', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('meeting_url', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'NO_SHOW', name='appointmentstatus'), nullable=False),
    sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('confirmation_sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('confirmation_received_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('feedback_sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('feedback_received_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('provider_notes', sa.Text(), nullable=True),
    sa.Column('preparation_notes', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['service_delivery_id'], ['service_deliveries.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointments_business_id'), 'appointments', ['business_id'], unique=False)
    op.create_index(op.f('ix_appointments_order_id'), 'appointments', ['order_id'], unique=False)
    op.create_index(op.f('ix_appointments_service_delivery_id'), 'appointments', ['service_delivery_id'], unique=False)
    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)
    op.create_table('payment_reminders',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=False),
    sa.Column('invoice_id', sa.UUID(), nullable=True),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('reminder_level', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('message_content', sa.Text(), nullable=True),
    sa.Column('channel_platform', sa.String(length=50), nullable=False),
    sa.Column('response_received', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['invoice_id'], ['sales_invoices.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_reminders_business_id'), 'payment_reminders', ['business_id'], unique=False)
    op.create_index('ix_payment_reminders_business_status', 'payment_reminders', ['business_id', 'status'], unique=False)
    op.create_index(op.f('ix_payment_reminders_order_id'), 'payment_reminders', ['order_id'], unique=False)
    op.create_table('shipment_tracking_events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('shipment_id', sa.UUID(), nullable=False),
    sa.Column('event_code', sa.String(length=50), nullable=True),
    sa.Column('event_description', sa.String(length=255), nullable=False),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('carrier_status', sa.String(length=100), nullable=True),
    sa.Column('event_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shipment_tracking_events_shipment_id'), 'shipment_tracking_events', ['shipment_id'], unique=False)
    op.create_table('ugc_requests',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('order_id', sa.UUID(), nullable=True),
    sa.Column('campaign_id', sa.UUID(), nullable=True),
    sa.Column('content_type', sa.String(length=50), nullable=False),
    sa.Column('request_message', sa.Text(), nullable=False),
    sa.Column('incentive_offered', sa.String(length=200), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'SENT', 'RECEIVED', 'APPROVED', 'REJECTED', name='ugcrequeststatus'), nullable=False),
    sa.Column('response_media_urls', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('response_text', sa.Text(), nullable=True),
    sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('social_proof_id', sa.UUID(), nullable=True),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['campaign_id'], ['growth_campaigns.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['social_proof_id'], ['social_proofs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ugc_requests_business_id'), 'ugc_requests', ['business_id'], unique=False)
    op.create_index('ix_ugc_requests_business_status', 'ugc_requests', ['business_id', 'status'], unique=False)
    op.create_index(op.f('ix_ugc_requests_campaign_id'), 'ugc_requests', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_ugc_requests_conversation_id'), 'ugc_requests', ['conversation_id'], unique=False)
    op.create_index('ix_ugc_requests_order', 'ugc_requests', ['order_id'], unique=False)
    op.create_index(op.f('ix_ugc_requests_order_id'), 'ugc_requests', ['order_id'], unique=False)


def downgrade() -> None:
    pass
