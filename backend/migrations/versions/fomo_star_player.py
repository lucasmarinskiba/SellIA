"""FOMO Star Player: Full A/B testing, events, analytics, A/B framework

Revision ID: fomo_001
Revises:
Create Date: 2026-08-27 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'fomo_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # FOMO Campaigns (expand existing with A/B test support)
    op.add_column('fomo_campaigns', sa.Column('trigger_type', sa.String(50), nullable=True))
    op.add_column('fomo_campaigns', sa.Column('config', postgresql.JSONB(), nullable=True))
    op.add_column('fomo_campaigns', sa.Column('status', sa.String(20), server_default='active'))
    op.add_column('fomo_campaigns', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))

    # FOMO Events (real-time activity tracking)
    op.create_table(
        'fomo_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fomo_campaigns.id', ondelete='CASCADE')),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_fomo_events_campaign', 'fomo_events', ['campaign_id', 'created_at'])

    # FOMO A/B Tests
    op.create_table(
        'fomo_ab_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fomo_campaigns.id', ondelete='CASCADE')),
        sa.Column('variant_a', postgresql.JSONB(), nullable=False),
        sa.Column('variant_b', postgresql.JSONB(), nullable=False),
        sa.Column('variant_a_conversions', sa.Integer(), server_default='0'),
        sa.Column('variant_a_views', sa.Integer(), server_default='0'),
        sa.Column('variant_b_conversions', sa.Integer(), server_default='0'),
        sa.Column('variant_b_views', sa.Integer(), server_default='0'),
        sa.Column('winner', sa.String(1), nullable=True),
        sa.Column('status', sa.String(20), server_default='running'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_fomo_ab_tests_campaign', 'fomo_ab_tests', ['campaign_id'])

    # FOMO Metrics (daily aggregates)
    op.create_table(
        'fomo_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fomo_campaigns.id', ondelete='CASCADE')),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('impressions', sa.Integer(), server_default='0'),
        sa.Column('conversions', sa.Integer(), server_default='0'),
        sa.Column('revenue', sa.Numeric(15, 2), server_default='0'),
        sa.UniqueConstraint('campaign_id', 'date', name='uq_fomo_metrics_campaign_date'),
    )
    op.create_index('idx_fomo_metrics_campaign', 'fomo_metrics', ['campaign_id', 'date'])


def downgrade() -> None:
    op.drop_index('idx_fomo_metrics_campaign')
    op.drop_table('fomo_metrics')

    op.drop_index('idx_fomo_ab_tests_campaign')
    op.drop_table('fomo_ab_tests')

    op.drop_index('idx_fomo_events_campaign')
    op.drop_table('fomo_events')

    op.drop_column('fomo_campaigns', 'user_id')
    op.drop_column('fomo_campaigns', 'status')
    op.drop_column('fomo_campaigns', 'config')
    op.drop_column('fomo_campaigns', 'trigger_type')
