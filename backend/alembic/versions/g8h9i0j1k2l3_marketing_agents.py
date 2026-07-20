"""marketing_agents

Revision ID: g8h9i0j1k2l3
Revises: f6g7h8i9j0k1
Create Date: 2026-05-26 14:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'g8h9i0j1k2l3'
down_revision: Union[str, None] = 'f7g8h9i0j1k2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # === ad_campaigns ===
    if not inspector.has_table("ad_campaigns"):
        op.create_table(
            'ad_campaigns',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('campaign_name', sa.String(255), nullable=False),
            sa.Column('platform', sa.String(50), nullable=False),
            sa.Column('objective', sa.String(100), nullable=False),
            sa.Column('target_audience', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('budget', sa.Numeric(12, 2), nullable=True),
            sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # === ad_variants ===
    if not inspector.has_table("ad_variants"):
        op.create_table(
            'ad_variants',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ad_campaigns.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('variant_name', sa.String(255), nullable=False),
            sa.Column('headline', sa.String(255), nullable=False),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('cta', sa.String(100), nullable=False),
            sa.Column('image_prompt', sa.Text(), nullable=True),
            sa.Column('targeting', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('predicted_ctr', sa.Numeric(5, 4), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # === pitch_decks ===
    if not inspector.has_table("pitch_decks"):
        op.create_table(
            'pitch_decks',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('slides', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('metrics', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
            sa.Column('pdf_url', sa.String(500), nullable=True),
            sa.Column('html_url', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # === pitch_slides ===
    if not inspector.has_table("pitch_slides"):
        op.create_table(
            'pitch_slides',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('deck_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pitch_decks.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('slide_number', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('chart_data', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # === kpi_dashboards ===
    if not inspector.has_table("kpi_dashboards"):
        op.create_table(
            'kpi_dashboards',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('dashboard_name', sa.String(255), nullable=False),
            sa.Column('widgets', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('refresh_interval', sa.Integer(), nullable=False, server_default='300'),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # === kpi_widgets ===
    if not inspector.has_table("kpi_widgets"):
        op.create_table(
            'kpi_widgets',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('dashboard_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('kpi_dashboards.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('widget_type', sa.String(50), nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('data_source', sa.String(255), nullable=False),
            sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('alerts', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )


def downgrade() -> None:
    op.drop_table('kpi_widgets')
    op.drop_table('kpi_dashboards')
    op.drop_table('pitch_slides')
    op.drop_table('pitch_decks')
    op.drop_table('ad_variants')
    op.drop_table('ad_campaigns')
