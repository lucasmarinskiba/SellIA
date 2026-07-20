"""proactive outreach engine

Revision ID: 99k2f3a4b5c6
Revises: 0e797dd2bbe
Create Date: 2026-05-20 20:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '99k2f3a4b5c6'
down_revision: Union[str, None] = '0e797dd2bbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("outreach_opportunities"):
        op.create_table(
            'outreach_opportunities',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('opportunity_type', sa.String(length=50), nullable=False),
            sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
            sa.Column('trigger_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.Column('suggested_message', sa.Text(), nullable=True),
            sa.Column('suggested_channel', sa.String(length=20), nullable=False, server_default='whatsapp'),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('outcome', sa.String(length=50), nullable=True),
            sa.Column('revenue_generated', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_outreach_opportunities_business_id'), 'outreach_opportunities', ['business_id'], unique=False)
        op.create_index(op.f('ix_outreach_opportunities_customer_id'), 'outreach_opportunities', ['customer_id'], unique=False)
        op.create_index(op.f('ix_outreach_opportunities_opportunity_type'), 'outreach_opportunities', ['opportunity_type'], unique=False)
        op.create_index(op.f('ix_outreach_opportunities_status'), 'outreach_opportunities', ['status'], unique=False)
        op.create_index('ix_outreach_opportunities_business_status', 'outreach_opportunities', ['business_id', 'status'], unique=False)
        op.create_index('ix_outreach_opportunities_business_type', 'outreach_opportunities', ['business_id', 'opportunity_type'], unique=False)

    if not inspector.has_table("outreach_rules"):
        op.create_table(
            'outreach_rules',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('rule_name', sa.String(length=100), nullable=False),
            sa.Column('rule_type', sa.String(length=50), nullable=False),
            sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.Column('message_template', sa.Text(), nullable=False),
            sa.Column('channel', sa.String(length=20), nullable=False, server_default='whatsapp'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_outreach_rules_business_id'), 'outreach_rules', ['business_id'], unique=False)
        op.create_index(op.f('ix_outreach_rules_rule_type'), 'outreach_rules', ['rule_type'], unique=False)
        op.create_index('ix_outreach_rules_business_active', 'outreach_rules', ['business_id', 'is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_outreach_rules_business_active', table_name='outreach_rules')
    op.drop_index(op.f('ix_outreach_rules_rule_type'), table_name='outreach_rules')
    op.drop_index(op.f('ix_outreach_rules_business_id'), table_name='outreach_rules')
    op.drop_table('outreach_rules')
    op.drop_index('ix_outreach_opportunities_business_type', table_name='outreach_opportunities')
    op.drop_index('ix_outreach_opportunities_business_status', table_name='outreach_opportunities')
    op.drop_index(op.f('ix_outreach_opportunities_status'), table_name='outreach_opportunities')
    op.drop_index(op.f('ix_outreach_opportunities_opportunity_type'), table_name='outreach_opportunities')
    op.drop_index(op.f('ix_outreach_opportunities_customer_id'), table_name='outreach_opportunities')
    op.drop_index(op.f('ix_outreach_opportunities_business_id'), table_name='outreach_opportunities')
    op.drop_table('outreach_opportunities')
