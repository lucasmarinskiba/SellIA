"""multimedia_agents

Revision ID: i0j1k2l3m4n5
Revises: f6g7h8i9j0k1, c1d2e3f4g5h6, d4e5f6g7h8i9, e5f6g7h8i9j0
Create Date: 2026-05-26 11:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = 'i0j1k2l3m4n5'
down_revision: Union[str, None] = 'h9i0j1k2l3m4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    try:
        inspector = inspect(bind)
        return inspector.has_table(table_name)
    except NoInspectionAvailable:
        return False


def upgrade() -> None:
    # Music Agent
    if not _has_table("music_generation_jobs"):
        op.create_table(
            'music_generation_jobs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('prompt', sa.Text(), nullable=False),
            sa.Column('genre', sa.String(length=50), nullable=False, server_default='corporate'),
            sa.Column('duration', sa.Integer(), nullable=False, server_default='30'),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('provider_used', sa.String(length=50), nullable=True),
            sa.Column('file_url', sa.String(length=500), nullable=True),
            sa.Column('file_format', sa.String(length=10), nullable=True, server_default='mp3'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("music_tracks"):
        op.create_table(
            'music_tracks',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('music_generation_jobs.id', ondelete='SET NULL'), nullable=True),
            sa.Column('track_name', sa.String(length=255), nullable=False),
            sa.Column('genre', sa.String(length=50), nullable=False),
            sa.Column('mood', sa.String(length=50), nullable=True),
            sa.Column('tempo', sa.Integer(), nullable=True),
            sa.Column('duration', sa.Integer(), nullable=False),
            sa.Column('file_url', sa.String(length=500), nullable=False),
            sa.Column('usage_rights', sa.String(length=50), nullable=True, server_default='commercial'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # Brand Visual Agent
    if not _has_table("brand_kit_jobs"):
        op.create_table(
            'brand_kit_jobs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('brand_name', sa.String(length=255), nullable=False),
            sa.Column('industry', sa.String(length=100), nullable=False),
            sa.Column('colors', postgresql.JSONB(), nullable=True),
            sa.Column('fonts', postgresql.JSONB(), nullable=True),
            sa.Column('logo_url', sa.String(length=500), nullable=True),
            sa.Column('assets', postgresql.JSONB(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("brand_assets"):
        op.create_table(
            'brand_assets',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('brand_kit_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('asset_type', sa.String(length=50), nullable=False),
            sa.Column('file_url', sa.String(length=500), nullable=False),
            sa.Column('config', postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # Viral Video Agent
    if not _has_table("video_generation_jobs"):
        op.create_table(
            'video_generation_jobs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('prompt', sa.Text(), nullable=False),
            sa.Column('platform', sa.String(length=20), nullable=False, server_default='tiktok'),
            sa.Column('duration', sa.Integer(), nullable=False, server_default='15'),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('provider_used', sa.String(length=50), nullable=True),
            sa.Column('video_url', sa.String(length=500), nullable=True),
            sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
            sa.Column('script', postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("video_scripts"):
        op.create_table(
            'video_scripts',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('video_generation_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('hook', sa.Text(), nullable=False),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('cta', sa.Text(), nullable=False),
            sa.Column('duration', sa.Integer(), nullable=False),
            sa.Column('visual_direction', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )


def downgrade() -> None:
    if _has_table("video_scripts"):
        op.drop_table('video_scripts')
    if _has_table("video_generation_jobs"):
        op.drop_table('video_generation_jobs')
    if _has_table("brand_assets"):
        op.drop_table('brand_assets')
    if _has_table("brand_kit_jobs"):
        op.drop_table('brand_kit_jobs')
    if _has_table("music_tracks"):
        op.drop_table('music_tracks')
    if _has_table("music_generation_jobs"):
        op.drop_table('music_generation_jobs')
