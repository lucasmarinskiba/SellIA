"""Phase 32: Platform Monetization FOOM.

Revision ID: 0036
Revises: 0035
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0036'
down_revision = '0035'


def upgrade() -> None:
    op.create_table(
        'user_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('segment_type', sa.String(50), nullable=False),
        sa.Column('segment_score', sa.Integer()),
        sa.Column('days_since_login', sa.Integer()),
        sa.Column('login_count_7d', sa.Integer()),
        sa.Column('feature_usage_pct', sa.Float()),
        sa.Column('feature_limit_hits_7d', sa.Integer()),
        sa.Column('team_size', sa.Integer()),
        sa.Column('api_calls_month', sa.Integer()),
        sa.Column('churn_risk', sa.Float()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_segment', 'user_segments', ['user_id', 'segment_type'])

    op.create_table(
        'upgrade_triggers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('segment_type', sa.String(50)),
        sa.Column('trigger_type', sa.String(50)),
        sa.Column('trigger_message', sa.Text()),
        sa.Column('shown_at', sa.DateTime()),
        sa.Column('clicked_at', sa.DateTime()),
        sa.Column('converted_at', sa.DateTime()),
        sa.Column('revenue_generated', sa.Float()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_triggers', 'upgrade_triggers', ['user_id'])

    op.create_table(
        'ab_test_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('test_name', sa.String(255)),
        sa.Column('element_type', sa.String(50)),
        sa.Column('variant_a', sa.Text()),
        sa.Column('variant_b', sa.Text()),
        sa.Column('start_date', sa.DateTime()),
        sa.Column('end_date', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_test_name', 'ab_test_variants', ['test_name'])

    op.create_table(
        'conversion_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255)),
        sa.Column('trigger_id', postgresql.UUID(as_uuid=True)),
        sa.Column('test_variant', sa.String(50)),
        sa.Column('event_type', sa.String(50)),
        sa.Column('event_timestamp', sa.DateTime()),
        sa.Column('revenue_attributed', sa.Float()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_events', 'conversion_events', ['user_id'])

    op.create_table(
        'ab_test_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('test_id', postgresql.UUID(as_uuid=True)),
        sa.Column('variant', sa.String(50)),
        sa.Column('impressions', sa.Integer()),
        sa.Column('conversions', sa.Integer()),
        sa.Column('revenue', sa.Float()),
        sa.Column('conversion_rate', sa.Float()),
        sa.Column('statistical_significance', sa.Float()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_test_results', 'ab_test_results', ['test_id'])

    op.create_table(
        'monetization_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_date', sa.Date()),
        sa.Column('total_free_users', sa.Integer()),
        sa.Column('freemium_active', sa.Integer()),
        sa.Column('freemium_stale', sa.Integer()),
        sa.Column('total_conversions', sa.Integer()),
        sa.Column('total_revenue', sa.Float()),
        sa.Column('avg_conversion_rate', sa.Float()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_snapshot_date', 'monetization_metrics', ['snapshot_date'])


def downgrade() -> None:
    op.drop_table('monetization_metrics')
    op.drop_table('ab_test_results')
    op.drop_table('conversion_events')
    op.drop_table('ab_test_variants')
    op.drop_table('upgrade_triggers')
    op.drop_table('user_segments')
