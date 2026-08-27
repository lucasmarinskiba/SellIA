"""Layer 5: Customer FOMO Generator - User-facing FOMO tools"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'customer_fomo_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('campaign_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('config', postgresql.JSONB, nullable=False),
        sa.Column('performance', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['business_id'], ['business.id']),
    )

    op.create_table(
        'customer_fomo_widgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('widget_type', sa.String(50), nullable=False),
        sa.Column('config', postgresql.JSONB, nullable=False),
        sa.Column('embed_code', sa.Text, nullable=False),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['customer_fomo_campaigns.id']),
    )

    op.create_table(
        'customer_fomo_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('data', postgresql.JSONB, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['customer_fomo_campaigns.id']),
    )

    op.create_table(
        'customer_fomo_automations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('automation_type', sa.String(50), nullable=False),
        sa.Column('trigger', sa.String(100), nullable=False),
        sa.Column('config', postgresql.JSONB, nullable=False),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('executions', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['customer_fomo_campaigns.id']),
    )

    op.create_table(
        'customer_fomo_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('impressions', sa.Integer, default=0),
        sa.Column('clicks', sa.Integer, default=0),
        sa.Column('conversions', sa.Integer, default=0),
        sa.Column('revenue', sa.Numeric(15, 2), default=0),
        sa.Column('avg_conversion_lift', sa.Numeric(5, 2), default=0),
        sa.Column('roi', sa.Numeric(5, 2), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['customer_fomo_campaigns.id']),
    )

    op.create_index('ix_customer_fomo_campaigns_user_id', 'customer_fomo_campaigns', ['user_id'])
    op.create_index('ix_customer_fomo_campaigns_business_id', 'customer_fomo_campaigns', ['business_id'])
    op.create_index('ix_customer_fomo_widgets_campaign_id', 'customer_fomo_widgets', ['campaign_id'])
    op.create_index('ix_customer_fomo_events_campaign_id', 'customer_fomo_events', ['campaign_id'])
    op.create_index('ix_customer_fomo_automations_campaign_id', 'customer_fomo_automations', ['campaign_id'])
    op.create_index('ix_customer_fomo_analytics_campaign_id', 'customer_fomo_analytics', ['campaign_id'])


def downgrade():
    op.drop_index('ix_customer_fomo_analytics_campaign_id')
    op.drop_index('ix_customer_fomo_automations_campaign_id')
    op.drop_index('ix_customer_fomo_events_campaign_id')
    op.drop_index('ix_customer_fomo_widgets_campaign_id')
    op.drop_index('ix_customer_fomo_campaigns_business_id')
    op.drop_index('ix_customer_fomo_campaigns_user_id')
    op.drop_table('customer_fomo_analytics')
    op.drop_table('customer_fomo_automations')
    op.drop_table('customer_fomo_events')
    op.drop_table('customer_fomo_widgets')
    op.drop_table('customer_fomo_campaigns')
