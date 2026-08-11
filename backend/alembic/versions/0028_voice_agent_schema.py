"""Create voice agent schema for call handling."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision = '0028'
down_revision = '0027'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE SCHEMA IF NOT EXISTS voice_agent')

    # Agent personalities/instructions
    op.create_table(
        'agent_personas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('system_prompt', sa.Text, nullable=False),
        sa.Column('voice_id', sa.String(100)),
        sa.Column('language', sa.String(10), default='en-US'),
        sa.Column('speaking_rate', sa.Float, default=1.0),
        sa.Column('temperature', sa.Float, default=0.7),
        sa.Column('instructions', JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        schema='voice_agent',
    )

    # Call records
    op.create_table(
        'calls',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('twilio_call_id', sa.String(255), unique=True, nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('agent_persona_id', UUID(as_uuid=True), nullable=False),
        sa.Column('contact_number', sa.String(20), nullable=False),
        sa.Column('contact_name', sa.String(255)),
        sa.Column('deal_id', sa.String(255), index=True),
        sa.Column('call_type', sa.String(50), nullable=False),  # inbound, outbound
        sa.Column('status', sa.String(50), nullable=False),  # queued, ringing, in-progress, completed, failed
        sa.Column('direction', sa.String(50), nullable=False),  # inbound, outbound
        sa.Column('duration_seconds', sa.Integer, default=0),
        sa.Column('recording_url', sa.String(500)),
        sa.Column('transcript', sa.Text),
        sa.Column('transcript_summary', sa.Text),
        sa.Column('sentiment', sa.String(50)),
        sa.Column('sentiment_score', sa.Float),
        sa.Column('started_at', sa.DateTime),
        sa.Column('ended_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='voice_agent',
    )

    # Call transcripts (detailed)
    op.create_table(
        'call_transcripts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('call_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('speaker', sa.String(50), nullable=False),  # agent, customer, system
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('timestamp', sa.Float, nullable=False),
        sa.Column('confidence', sa.Float),
        sa.Column('emotion', sa.String(50)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='voice_agent',
    )

    # Call events (state changes)
    op.create_table(
        'call_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('call_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_data', JSONB),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='voice_agent',
    )

    # Call actions (agent actions during call)
    op.create_table(
        'call_actions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('call_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('action_data', JSONB),
        sa.Column('result', sa.String(500)),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='voice_agent',
    )

    # Voice webhooks (Twilio status updates)
    op.create_table(
        'voice_webhooks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('webhook_type', sa.String(100), nullable=False),
        sa.Column('twilio_call_id', sa.String(255)),
        sa.Column('payload', JSONB, nullable=False),
        sa.Column('processed', sa.Boolean, default=False),
        sa.Column('processed_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='voice_agent',
    )

    # Call analytics (aggregate)
    op.create_table(
        'call_analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('metric_date', sa.Date, nullable=False),
        sa.Column('total_calls', sa.Integer, default=0),
        sa.Column('total_duration_seconds', sa.Integer, default=0),
        sa.Column('avg_duration_seconds', sa.Float),
        sa.Column('completed_calls', sa.Integer, default=0),
        sa.Column('failed_calls', sa.Integer, default=0),
        sa.Column('avg_sentiment_score', sa.Float),
        sa.Column('calls_by_hour', JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='voice_agent',
    )

    # Create indexes
    op.create_index('idx_calls_user_id', 'calls', ['user_id'], schema='voice_agent')
    op.create_index('idx_calls_deal_id', 'calls', ['deal_id'], schema='voice_agent')
    op.create_index('idx_calls_status', 'calls', ['status'], schema='voice_agent')
    op.create_index('idx_call_transcripts_call_id', 'call_transcripts', ['call_id'], schema='voice_agent')
    op.create_index('idx_call_events_call_id', 'call_events', ['call_id'], schema='voice_agent')
    op.create_index('idx_call_actions_call_id', 'call_actions', ['call_id'], schema='voice_agent')
    op.create_index('idx_call_analytics_user_id', 'call_analytics', ['user_id'], schema='voice_agent')


def downgrade():
    op.execute('DROP SCHEMA IF EXISTS voice_agent CASCADE')
