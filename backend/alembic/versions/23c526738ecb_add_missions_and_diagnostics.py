"""Add missions and diagnostics tables

Revision ID: add_missions_and_diagnostics
Revises: fcbf51db9f0f
Create Date: 2026-05-22 10:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '23c526738ecb'
down_revision: Union[str, None] = '0ecfa96b7780'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Mission status enum
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mission_status') THEN CREATE TYPE mission_status AS ENUM ('draft', 'proposed', 'approved', 'running', 'completed', 'failed', 'cancelled'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mission_category') THEN CREATE TYPE mission_category AS ENUM ('launch', 'seo', 'ads', 'recovery', 'expansion', 'branding', 'logistics', 'automation'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mission_creator') THEN CREATE TYPE mission_creator AS ENUM ('ai', 'user'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mission_step_status') THEN CREATE TYPE mission_step_status AS ENUM ('pending', 'running', 'completed', 'failed', 'skipped', 'waiting_approval'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'diagnostic_category') THEN CREATE TYPE diagnostic_category AS ENUM ('sales', 'branding', 'traffic', 'seo', 'logistics', 'ads', 'conversion', 'retention'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'diagnostic_severity') THEN CREATE TYPE diagnostic_severity AS ENUM ('info', 'warning', 'critical'); END IF; END $$;")

    # missions table
    op.create_table(
        'missions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('playbook_slug', sa.String(100), nullable=True, index=True),
        sa.Column('target_platforms', postgresql.JSONB(), server_default='[]'),
        sa.Column('expected_impact', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_by', sa.String(50), nullable=False, server_default='ai'),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # mission_steps table
    op.create_table(
        'mission_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('mission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('missions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('step_number', sa.Integer(), nullable=False, default=1),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_params', postgresql.JSONB(), server_default='{}'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approved_by_user', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('computer_use_session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('computer_use_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # business_diagnostics table
    op.create_table(
        'business_diagnostics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('mission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('missions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('diagnostic_date', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('finding', sa.Text(), nullable=False),
        sa.Column('metric_value', sa.String(100), nullable=True),
        sa.Column('benchmark_value', sa.String(100), nullable=True),
        sa.Column('recommended_mission_slug', sa.String(100), nullable=True),
        sa.Column('context_data', postgresql.JSONB(), server_default='{}'),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('business_diagnostics')
    op.drop_table('mission_steps')
    op.drop_table('missions')
    op.execute("DROP TYPE mission_status")
    op.execute("DROP TYPE mission_category")
    op.execute("DROP TYPE mission_creator")
    op.execute("DROP TYPE mission_step_status")
    op.execute("DROP TYPE diagnostic_category")
    op.execute("DROP TYPE diagnostic_severity")
