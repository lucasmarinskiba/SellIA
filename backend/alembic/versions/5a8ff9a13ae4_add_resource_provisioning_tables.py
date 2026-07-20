"""add_resource_provisioning_tables

Revision ID: 5a8ff9a13ae4
Revises: 69a2f112522c
Create Date: 2026-05-19 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5a8ff9a13ae4'
down_revision: Union[str, None] = '69a2f112522c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === resource_requests ===
    op.create_table(
        'resource_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('resource_type', sa.String(50), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('parameters', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', index=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('provider_reference', sa.String(255), nullable=True),
    )
    op.create_index('ix_resource_requests_type_status', 'resource_requests', ['resource_type', 'status'])

    # === resource_jobs ===
    op.create_table(
        'resource_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resource_requests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('result', postgresql.JSONB(), nullable=True, server_default='{}'),
    )

    # === resource_events ===
    op.create_table(
        'resource_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resource_requests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('resource_events')
    op.drop_table('resource_jobs')
    op.drop_table('resource_requests')
