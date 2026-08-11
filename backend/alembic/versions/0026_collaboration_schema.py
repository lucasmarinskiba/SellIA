"""Add collaboration schema for team features

Revision ID: 0026_collaboration
Revises:
Create Date: 2026-08-11 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0026_collaboration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE SCHEMA IF NOT EXISTS collaboration')

    op.create_table(
        'deal_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('deal_id', sa.String(255), nullable=False, index=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('mentions', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        schema='collaboration'
    )

    op.create_table(
        'approval_chains',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('action_id', sa.String(255), nullable=False, index=True),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('requested_by', sa.String(255), nullable=False),
        sa.Column('approvers', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('approval_status', sa.String(20), default='pending'),
        sa.Column('decision_by', sa.String(255), nullable=True),
        sa.Column('decision_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        schema='collaboration'
    )

    op.create_table(
        'deal_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('shared_by', sa.String(255), nullable=False),
        sa.Column('shared_with', sa.String(255), nullable=False),
        sa.Column('permissions', sa.String(20), default='read'),
        sa.Column('shared_at', sa.DateTime, server_default=sa.func.now()),
        schema='collaboration'
    )

    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(255), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('actor_id', sa.String(255), nullable=False),
        sa.Column('changes', postgresql.JSONB, nullable=True),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now(), index=True),
        schema='collaboration'
    )

    op.create_index('idx_deal_comments_deal_id', 'deal_comments', ['deal_id'], schema='collaboration')
    op.create_index('idx_approval_chains_action_id', 'approval_chains', ['action_id'], schema='collaboration')


def downgrade():
    op.drop_schema('collaboration', cascade=True)
