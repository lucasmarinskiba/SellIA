"""Add user memory tables

Revision ID: s9t0u1v2w3x4
Revises: r8s9t0u1v2w3
Create Date: 2026-08-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's9t0u1v2w3x4'
down_revision = 'r8s9t0u1v2w3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_memory table
    op.create_table(
        'user_memory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preferred_language', sa.String(10), nullable=False, server_default='es'),
        sa.Column('preferred_tone', sa.String(50), nullable=False, server_default='professional'),
        sa.Column('industry_focus', sa.String(100), nullable=True),
        sa.Column('business_stage', sa.String(50), nullable=True),
        sa.Column('primary_business_type', sa.String(100), nullable=True),
        sa.Column('target_audience_summary', sa.Text(), nullable=True),
        sa.Column('key_challenges', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('key_interests', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('technologies_used', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('total_conversations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_messages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('favorite_agents', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('frequently_asked_topics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('user_actions_taken', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('email_notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notification_frequency', sa.String(50), nullable=False, server_default='daily'),
        sa.Column('preferred_contact_time', sa.String(100), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('satisfaction_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('churn_risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('lifetime_value_estimate', sa.String(50), nullable=False, server_default='low'),
        sa.Column('feature_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('beta_programs', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('last_active_business_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_active_conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_active_agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_memory_user_id'), 'user_memory', ['user_id'], unique=False)

    # Create user_memory_events table
    op.create_table(
        'user_memory_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_memory_events_user_id'), 'user_memory_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_memory_events_event_type'), 'user_memory_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_user_memory_events_created_at'), 'user_memory_events', ['created_at'], unique=False)

    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preference_key', sa.String(100), nullable=False),
        sa.Column('preference_value', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'preference_key', name='uq_user_preferences_user_id_preference_key')
    )
    op.create_index(op.f('ix_user_preferences_user_id'), 'user_preferences', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_preferences_preference_key'), 'user_preferences', ['preference_key'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_preferences_preference_key'), table_name='user_preferences')
    op.drop_index(op.f('ix_user_preferences_user_id'), table_name='user_preferences')
    op.drop_table('user_preferences')
    op.drop_index(op.f('ix_user_memory_events_created_at'), table_name='user_memory_events')
    op.drop_index(op.f('ix_user_memory_events_event_type'), table_name='user_memory_events')
    op.drop_index(op.f('ix_user_memory_events_user_id'), table_name='user_memory_events')
    op.drop_table('user_memory_events')
    op.drop_index(op.f('ix_user_memory_user_id'), table_name='user_memory')
    op.drop_table('user_memory')
