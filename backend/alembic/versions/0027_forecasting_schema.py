"""Create forecasting schema for deal intelligence."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision = '0027'
down_revision = '0026_collaboration'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE SCHEMA IF NOT EXISTS forecasting')

    # Deal scores table
    op.create_table(
        'deal_scores',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('deal_id', sa.String(255), nullable=False, index=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('win_probability', sa.Float, nullable=False),
        sa.Column('confidence_level', sa.Float, nullable=False),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('engagement_velocity', sa.Float, nullable=False),
        sa.Column('days_in_stage', sa.Integer, nullable=False),
        sa.Column('proposal_status', sa.String(50)),
        sa.Column('ai_score_factors', JSONB, nullable=False),
        sa.Column('last_updated', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='forecasting',
    )

    # Revenue forecast snapshots
    op.create_table(
        'revenue_forecasts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('forecast_date', sa.Date, nullable=False),
        sa.Column('total_pipeline', sa.Float, nullable=False),
        sa.Column('projected_30d', sa.Float, nullable=False),
        sa.Column('projected_60d', sa.Float, nullable=False),
        sa.Column('projected_90d', sa.Float, nullable=False),
        sa.Column('confidence_30d', sa.Float, nullable=False),
        sa.Column('confidence_60d', sa.Float, nullable=False),
        sa.Column('confidence_90d', sa.Float, nullable=False),
        sa.Column('deal_breakdown', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='forecasting',
    )

    # At-risk deals
    op.create_table(
        'at_risk_deals',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('deal_id', sa.String(255), nullable=False, index=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('risk_score', sa.Float, nullable=False),
        sa.Column('risk_reason', sa.String(255), nullable=False),
        sa.Column('days_without_activity', sa.Integer, nullable=False),
        sa.Column('suggested_action', sa.String(500)),
        sa.Column('action_taken', sa.String(500)),
        sa.Column('resolved', sa.Boolean, default=False),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('resolved_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='forecasting',
    )

    # Win/loss analysis
    op.create_table(
        'deal_outcomes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('outcome', sa.String(50), nullable=False),
        sa.Column('final_value', sa.Float),
        sa.Column('actual_close_date', sa.Date, nullable=False),
        sa.Column('days_to_close', sa.Integer, nullable=False),
        sa.Column('forecasted_probability', sa.Float),
        sa.Column('forecast_accuracy', sa.Float),
        sa.Column('win_loss_reason', sa.String(500)),
        sa.Column('engagement_touches', sa.Integer, default=0),
        sa.Column('proposal_count', sa.Integer, default=0),
        sa.Column('decision_factors', JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='forecasting',
    )

    # Forecasting metrics (aggregate)
    op.create_table(
        'forecasting_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('metric_date', sa.Date, nullable=False),
        sa.Column('forecast_accuracy_30d', sa.Float),
        sa.Column('forecast_accuracy_60d', sa.Float),
        sa.Column('forecast_accuracy_90d', sa.Float),
        sa.Column('total_deals_analyzed', sa.Integer, default=0),
        sa.Column('total_outcomes', sa.Integer, default=0),
        sa.Column('actual_vs_forecast', JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='forecasting',
    )

    # Create indexes
    op.create_index('idx_deal_scores_deal_id', 'deal_scores', ['deal_id'], schema='forecasting')
    op.create_index('idx_deal_scores_user_id', 'deal_scores', ['user_id'], schema='forecasting')
    op.create_index('idx_revenue_forecasts_user_id', 'revenue_forecasts', ['user_id'], schema='forecasting')
    op.create_index('idx_at_risk_deals_deal_id', 'at_risk_deals', ['deal_id'], schema='forecasting')
    op.create_index('idx_at_risk_deals_user_id', 'at_risk_deals', ['user_id'], schema='forecasting')
    op.create_index('idx_deal_outcomes_user_id', 'deal_outcomes', ['user_id'], schema='forecasting')
    op.create_index('idx_forecasting_metrics_user_id', 'forecasting_metrics', ['user_id'], schema='forecasting')


def downgrade():
    op.execute('DROP SCHEMA IF EXISTS forecasting CASCADE')
