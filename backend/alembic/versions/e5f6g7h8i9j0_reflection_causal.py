"""Add reflection and causal reasoning tables

Revision ID: e5f6g7h8i9j0
Revises: 0ecfa96b7780
Create Date: 2026-05-23 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, None] = '0ecfa96b7780'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    if bind is None:
        return False
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("agent_reflections"):
        op.create_table(
            'agent_reflections',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('agent_type', sa.String(50), nullable=False),
            sa.Column('what_went_well', sa.Text(), nullable=True),
            sa.Column('what_could_improve', sa.Text(), nullable=True),
            sa.Column('customer_insights', sa.Text(), nullable=True),
            sa.Column('future_recommendations', sa.Text(), nullable=True),
            sa.Column('score', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("chain_of_thought_logs"):
        op.create_table(
            'chain_of_thought_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column('thought_steps', postgresql.JSONB(), server_default='[]'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("objection_patterns"):
        op.create_table(
            'objection_patterns',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('pattern_name', sa.String(100), nullable=False),
            sa.Column('objection_text', sa.String(200), nullable=False),
            sa.Column('root_cause', sa.Text(), nullable=True),
            sa.Column('frequency_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('frequency_percent', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('overcome_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('overcome_rate', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('affected_segments', postgresql.JSONB(), server_default='[]'),
            sa.Column('recommended_response', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("causal_analyses"):
        op.create_table(
            'causal_analyses',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('deal_outcome', sa.String(50), nullable=False),
            sa.Column('surface_reason', sa.Text(), nullable=True),
            sa.Column('root_cause', sa.Text(), nullable=True),
            sa.Column('contributing_factors', postgresql.JSONB(), server_default='[]'),
            sa.Column('recommended_fix', sa.Text(), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )


def downgrade() -> None:
    if _has_table("causal_analyses"):
        op.drop_table('causal_analyses')
    if _has_table("objection_patterns"):
        op.drop_table('objection_patterns')
    if _has_table("chain_of_thought_logs"):
        op.drop_table('chain_of_thought_logs')
    if _has_table("agent_reflections"):
        op.drop_table('agent_reflections')
