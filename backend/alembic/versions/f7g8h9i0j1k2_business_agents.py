"""Add business autonomous agents tables

Revision ID: f7g8h9i0j1k2
Revises: f6g7h8i9j0k1
Create Date: 2026-05-26 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = 'f7g8h9i0j1k2'
down_revision: Union[str, None] = '0ecfa96b7780'
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
    # Market Analyst
    if not _has_table("market_analysis_jobs"):
        op.create_table(
            'market_analysis_jobs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('target_market', sa.String(255), nullable=False),
            sa.Column('competitors_analyzed', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('trends_found', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('report_url', sa.String(500), nullable=True),
            sa.Column('report_data', postgresql.JSONB(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("competitor_snapshots"):
        op.create_table(
            'competitor_snapshots',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('market_analysis_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('url', sa.String(500), nullable=True),
            sa.Column('price_range', sa.String(100), nullable=True),
            sa.Column('key_features', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('strengths', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('weaknesses', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('sentiment_score', sa.Numeric(3, 2), nullable=True),
            sa.Column('raw_data', postgresql.JSONB(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # Financial Planner
    if not _has_table("financial_plans"):
        op.create_table(
            'financial_plans',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('plan_name', sa.String(255), nullable=False),
            sa.Column('revenue_projections', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('expense_projections', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('cash_flow', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('break_even_month', sa.Integer(), nullable=True),
            sa.Column('scenarios', postgresql.JSONB(), server_default='{}', nullable=False),
            sa.Column('metrics', postgresql.JSONB(), server_default='{}', nullable=False),
            sa.Column('assumptions', postgresql.JSONB(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # Acquisition Strategist
    if not _has_table("acquisition_strategies"):
        op.create_table(
            'acquisition_strategies',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('strategy_name', sa.String(255), nullable=False),
            sa.Column('channels', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('funnel_stages', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('cac_target', sa.Numeric(10, 2), nullable=True),
            sa.Column('ltv_target', sa.Numeric(10, 2), nullable=True),
            sa.Column('sequences', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('budget_allocation', postgresql.JSONB(), server_default='{}', nullable=False),
            sa.Column('expected_results', postgresql.JSONB(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    # Landing Page Builder
    if not _has_table("landing_page_jobs"):
        op.create_table(
            'landing_page_jobs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('catalog_items.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('template_used', sa.String(100), nullable=True, server_default='modern'),
            sa.Column('generated_code_url', sa.String(500), nullable=True),
            sa.Column('preview_url', sa.String(500), nullable=True),
            sa.Column('variants', postgresql.JSONB(), server_default='[]', nullable=False),
            sa.Column('generated_code', postgresql.JSONB(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )


def downgrade() -> None:
    if _has_table("landing_page_jobs"):
        op.drop_table('landing_page_jobs')
    if _has_table("acquisition_strategies"):
        op.drop_table('acquisition_strategies')
    if _has_table("financial_plans"):
        op.drop_table('financial_plans')
    if _has_table("competitor_snapshots"):
        op.drop_table('competitor_snapshots')
    if _has_table("market_analysis_jobs"):
        op.drop_table('market_analysis_jobs')
