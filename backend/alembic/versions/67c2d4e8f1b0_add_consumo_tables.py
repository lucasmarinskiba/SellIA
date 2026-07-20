"""add_consumo_tables

Revision ID: 67c2d4e8f1b0
Revises: 56acfbe6b0a9
Create Date: 2026-05-20 09:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '67c2d4e8f1b0'
down_revision: Union[str, None] = '56acfbe6b0a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === ai_call_logs ===
    op.create_table(
        'ai_call_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('provider', sa.String(50), nullable=False, index=True),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False, index=True),
        sa.Column('tokens_input', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_output', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('cache_hit', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('was_batched', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_ai_call_logs_created_at', 'ai_call_logs', ['created_at'])

    # === onboarding_progress ===
    op.create_table(
        'onboarding_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('account_created', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('business_created', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('channel_connected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('agent_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('first_conversation', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('catalog_added', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('automation_created', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('step_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('step_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('help_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('help_context', sa.Text(), nullable=True),
        sa.Column('current_step', sa.String(50), nullable=False, server_default='account_created'),
        sa.Column('stuck_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ai_interventions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === churn_risk_signals ===
    op.create_table(
        'churn_risk_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('signals', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('action_taken', sa.String(50), nullable=True),
        sa.Column('action_result', sa.String(50), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === quality_gate_configs ===
    op.create_table(
        'quality_gate_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('min_confidence_threshold', sa.Float(), nullable=False, server_default='0.70'),
        sa.Column('auto_escalate_on_low_confidence', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_ai_messages_before_human', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('quality_gate_configs')
    op.drop_table('churn_risk_signals')
    op.drop_table('onboarding_progress')
    op.drop_index('ix_ai_call_logs_created_at', table_name='ai_call_logs')
    op.drop_table('ai_call_logs')
