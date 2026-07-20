"""add_diagnostic_and_support_fields

Revision ID: 56acfbe6b0a9
Revises: 5a8ff9a13ae4
Create Date: 2026-05-19 22:45:19.546361+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '56acfbe6b0a9'
down_revision: Union[str, None] = '5a8ff9a13ae4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === diagnostic_runs ===
    op.create_table(
        'diagnostic_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('diagnostic_type', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('findings', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('severity', sa.String(20), nullable=False, server_default='info'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # === support_tickets (create if not exists for auto-resolve) ===
    op.create_table(
        'support_tickets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('category', sa.String(50), nullable=False, server_default='other'),
        sa.Column('priority', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ai_suggested_answer', sa.Text(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('last_customer_reply', sa.Text(), nullable=True),
        sa.Column('last_customer_reply_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('csat_rating', sa.Integer(), nullable=True),
        sa.Column('csat_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === synthetic_checks ===
    op.create_table(
        'synthetic_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False, index=True),
        sa.Column('check_type', sa.String(50), nullable=False),
        sa.Column('target_url', sa.String(500), nullable=True),
        sa.Column('expected_status', sa.Integer(), nullable=True),
        sa.Column('expected_keyword', sa.String(255), nullable=True),
        sa.Column('interval_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('alert_severity', sa.String(20), nullable=False, server_default='warning'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === synthetic_results ===
    op.create_table(
        'synthetic_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('check_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('synthetic_checks.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === system_health_snapshots ===
    op.create_table(
        'system_health_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('overall_status', sa.String(20), nullable=False),
        sa.Column('checks_total', sa.Integer(), nullable=False),
        sa.Column('checks_passed', sa.Integer(), nullable=False),
        sa.Column('avg_response_time_ms', sa.Float(), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # === feature_flags ===
    op.create_table(
        'feature_flags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled_plans', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('rollout_percentage', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('user_id_allowlist', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('feature_flags')
    op.drop_table('system_health_snapshots')
    op.drop_table('synthetic_results')
    op.drop_table('synthetic_checks')
    op.drop_table('support_tickets')
    op.drop_table('diagnostic_runs')
