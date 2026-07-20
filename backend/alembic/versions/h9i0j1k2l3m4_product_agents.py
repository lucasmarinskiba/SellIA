"""product_agents

Revision ID: h9i0j1k2l3m4
Revises: f6g7h8i9j0k1
Create Date: 2026-05-26 14:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'h9i0j1k2l3m4'
down_revision: Union[str, None] = 'g8h9i0j1k2l3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # App Builder tables
    if not inspector.has_table("app_build_jobs"):
        op.create_table(
            'app_build_jobs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('app_name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('features', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('tech_stack', sa.String(100), nullable=False, server_default='nextjs-fastapi-postgres'),
            sa.Column('status', sa.Enum('pending', 'analyzing', 'generating', 'completed', 'failed', name='appbuildstatus'), nullable=False, index=True, server_default='pending'),
            sa.Column('code_zip_url', sa.String(1000), nullable=True),
            sa.Column('preview_url', sa.String(1000), nullable=True),
            sa.Column('deploy_instructions', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )

    if not inspector.has_table("app_features"):
        op.create_table(
            'app_features',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_build_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('feature_name', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('estimated_hours', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )

    # CRM Builder tables
    if not inspector.has_table("crm_build_jobs"):
        op.create_table(
            'crm_build_jobs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('crm_name', sa.String(255), nullable=False),
            sa.Column('modules', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('status', sa.Enum('pending', 'generating', 'completed', 'failed', name='crmbuildstatus'), nullable=False, index=True, server_default='pending'),
            sa.Column('code_url', sa.String(1000), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )

    if not inspector.has_table("crm_modules"):
        op.create_table(
            'crm_modules',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crm_build_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('module_name', sa.String(100), nullable=False),
            sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade() -> None:
    op.drop_table('crm_modules')
    op.drop_table('crm_build_jobs')
    op.drop_table('app_features')
    op.drop_table('app_build_jobs')
    op.execute("DROP TYPE IF EXISTS crmbuildstatus")
    op.execute("DROP TYPE IF EXISTS appbuildstatus")
