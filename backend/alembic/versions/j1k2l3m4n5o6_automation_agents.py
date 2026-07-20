"""automation_agents

Revision ID: j1k2l3m4n5o6
Revises: 4abdebee717d
Create Date: 2026-05-26 14:35:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'j1k2l3m4n5o6'
down_revision: Union[str, None] = '4abdebee717d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    try:
        inspector = inspect(bind)
        return inspector.has_table(table_name)
    except Exception:
        return False


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════
    # Agent 13: Customer Service Auto-Agent
    # ═══════════════════════════════════════════════════════
    if not _has_table("service_bot_configs"):
        op.create_table(
            'service_bot_configs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('name', sa.String(255), nullable=False, server_default='SellIA Support'),
            sa.Column('greeting_message', sa.Text(), nullable=False, server_default='¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?'),
            sa.Column('fallback_message', sa.Text(), nullable=False, server_default='No estoy seguro de entender. ¿Te gustaría que te conecte con un agente humano?'),
            sa.Column('escalation_threshold', sa.Numeric(3, 2), nullable=False, server_default='0.75'),
            sa.Column('hours_active', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('channels', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )

    if not _has_table("service_interactions"):
        op.create_table(
            'service_interactions',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('bot_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('service_bot_configs.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('channel', sa.String(20), nullable=False),
            sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column('messages', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('escalated', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('escalation_reason', sa.Text(), nullable=True),
            sa.Column('satisfaction_score', sa.Numeric(3, 2), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_service_interactions_created', 'service_interactions', ['created_at'])

    # ═══════════════════════════════════════════════════════
    # Agent 14: Lead Qualifier Auto-Agent
    # ═══════════════════════════════════════════════════════
    if not _has_table("lead_qualifications"):
        op.create_table(
            'lead_qualifications',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column('bant_score', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('qualification_score', sa.Numeric(5, 2), nullable=False, server_default='0.0'),
            sa.Column('status', sa.String(20), nullable=False, server_default='nurture'),
            sa.Column('routing_destination', sa.String(100), nullable=True),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_lead_qualifications_score', 'lead_qualifications', ['qualification_score'])
        op.create_index('ix_lead_qualifications_status', 'lead_qualifications', ['status'])

    # ═══════════════════════════════════════════════════════
    # Agent 15: Auto-Responder Pilot Agent
    # ═══════════════════════════════════════════════════════
    if not _has_table("auto_responder_rules"):
        op.create_table(
            'auto_responder_rules',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('rule_name', sa.String(255), nullable=False),
            sa.Column('trigger_type', sa.String(30), nullable=False),
            sa.Column('trigger_config', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('response_template', sa.Text(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )

    if not _has_table("auto_response_logs"):
        op.create_table(
            'auto_response_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auto_responder_rules.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('trigger_fired', sa.String(100), nullable=False),
            sa.Column('response_sent', sa.Text(), nullable=False),
            sa.Column('customer_replied', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('outcome', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_auto_response_logs_created', 'auto_response_logs', ['created_at'])


def downgrade() -> None:
    if _has_table("auto_response_logs"):
        op.drop_index('ix_auto_response_logs_created', table_name='auto_response_logs')
        op.drop_table('auto_response_logs')
    if _has_table("auto_responder_rules"):
        op.drop_table('auto_responder_rules')
    if _has_table("lead_qualifications"):
        op.drop_index('ix_lead_qualifications_score', table_name='lead_qualifications')
        op.drop_index('ix_lead_qualifications_status', table_name='lead_qualifications')
        op.drop_table('lead_qualifications')
    if _has_table("service_interactions"):
        op.drop_index('ix_service_interactions_created', table_name='service_interactions')
        op.drop_table('service_interactions')
    if _has_table("service_bot_configs"):
        op.drop_table('service_bot_configs')
