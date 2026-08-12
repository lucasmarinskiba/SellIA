"""Phase 30: Churn Prevention + ABM Intent Scoring.

Revision ID: 0035
Revises: 0034
Create Date: 2026-08-12 11:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0035'
down_revision = '0034'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create churn_predictions table
    op.create_table(
        'churn_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', sa.String(255), nullable=False),
        sa.Column('churn_probability', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(50), nullable=True),
        sa.Column('churn_reasons', postgresql.JSONB(), nullable=True),
        sa.Column('predicted_churn_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_risk', 'churn_predictions', ['customer_id', 'risk_level'])
    op.create_index('idx_probability', 'churn_predictions', ['churn_probability'])
    op.create_index('idx_predicted_date', 'churn_predictions', ['predicted_churn_date'])

    # Create expansion_opportunities table
    op.create_table(
        'expansion_opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', sa.String(255), nullable=False),
        sa.Column('opportunity_type', sa.String(50), nullable=False),
        sa.Column('base_feature', sa.String(255), nullable=True),
        sa.Column('adjacent_feature', sa.String(255), nullable=True),
        sa.Column('revenue_potential', sa.Float(), nullable=False),
        sa.Column('likelihood_score', sa.Float(), nullable=True),
        sa.Column('recommended_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_opp', 'expansion_opportunities', ['customer_id', 'opportunity_type'])
    op.create_index('idx_revenue_potential', 'expansion_opportunities', ['revenue_potential'])

    # Create abm_intent_scores table
    op.create_table(
        'abm_intent_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', sa.String(255), nullable=False),
        sa.Column('intent_score', sa.Integer(), nullable=True),
        sa.Column('intent_level', sa.String(50), nullable=True),
        sa.Column('top_signals', postgresql.JSONB(), nullable=True),
        sa.Column('trending', sa.String(50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_account_intent', 'abm_intent_scores', ['account_id', 'intent_score'])
    op.create_index('idx_intent_level', 'abm_intent_scores', ['intent_level'])

    # Create retention_campaigns table
    op.create_table(
        'retention_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', sa.String(255), nullable=False),
        sa.Column('churn_prediction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('campaign_type', sa.String(50), nullable=True),
        sa.Column('playbook_message', sa.Text(), nullable=False),
        sa.Column('offer_type', sa.String(50), nullable=True),
        sa.Column('offer_value', sa.String(255), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('converted', sa.Boolean(), nullable=True),
        sa.Column('converted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['churn_prediction_id'], ['churn_predictions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_campaign', 'retention_campaigns', ['customer_id', 'campaign_type'])
    op.create_index('idx_converted', 'retention_campaigns', ['converted'])

    # Create win_back_playbooks table
    op.create_table(
        'win_back_playbooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('churn_reason', sa.String(50), nullable=False),
        sa.Column('segment', sa.String(50), nullable=False),
        sa.Column('message_template', sa.Text(), nullable=False),
        sa.Column('offer_template', sa.Text(), nullable=True),
        sa.Column('executive_escalation_message', sa.Text(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reason_segment', 'win_back_playbooks', ['churn_reason', 'segment'])
    op.create_index('idx_success_rate', 'win_back_playbooks', ['success_rate'])

    # Create customer_engagement_metrics table
    op.create_table(
        'customer_engagement_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', sa.String(255), nullable=False),
        sa.Column('metric_date', sa.DateTime(), nullable=False),
        sa.Column('login_count', sa.Integer(), nullable=True),
        sa.Column('features_used_pct', sa.Float(), nullable=True),
        sa.Column('support_tickets_count', sa.Integer(), nullable=True),
        sa.Column('nps_score', sa.Integer(), nullable=True),
        sa.Column('health_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_date', 'customer_engagement_metrics', ['customer_id', 'metric_date'])
    op.create_index('idx_health_score', 'customer_engagement_metrics', ['health_score'])

    # Create customer_health_scorecards table
    op.create_table(
        'customer_health_scorecards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', sa.String(255), nullable=False),
        sa.Column('health_score', sa.Integer(), nullable=True),
        sa.Column('health_level', sa.String(50), nullable=True),
        sa.Column('churn_risk', sa.String(50), nullable=True),
        sa.Column('churn_probability', sa.Float(), nullable=True),
        sa.Column('expansion_potential', sa.Float(), nullable=True),
        sa.Column('expansion_opportunities_count', sa.Integer(), nullable=True),
        sa.Column('abm_intent_score', sa.Integer(), nullable=True),
        sa.Column('abm_intent_level', sa.String(50), nullable=True),
        sa.Column('trending', sa.String(50), nullable=True),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('snapshot_date', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_health', 'customer_health_scorecards', ['customer_id', 'health_level'])
    op.create_index('idx_snapshot_date', 'customer_health_scorecards', ['snapshot_date'])


def downgrade() -> None:
    op.drop_index('idx_snapshot_date', table_name='customer_health_scorecards')
    op.drop_index('idx_customer_health', table_name='customer_health_scorecards')
    op.drop_table('customer_health_scorecards')
    op.drop_index('idx_health_score', table_name='customer_engagement_metrics')
    op.drop_index('idx_customer_date', table_name='customer_engagement_metrics')
    op.drop_table('customer_engagement_metrics')
    op.drop_index('idx_success_rate', table_name='win_back_playbooks')
    op.drop_index('idx_reason_segment', table_name='win_back_playbooks')
    op.drop_table('win_back_playbooks')
    op.drop_index('idx_converted', table_name='retention_campaigns')
    op.drop_index('idx_customer_campaign', table_name='retention_campaigns')
    op.drop_table('retention_campaigns')
    op.drop_index('idx_intent_level', table_name='abm_intent_scores')
    op.drop_index('idx_account_intent', table_name='abm_intent_scores')
    op.drop_table('abm_intent_scores')
    op.drop_index('idx_revenue_potential', table_name='expansion_opportunities')
    op.drop_index('idx_customer_opp', table_name='expansion_opportunities')
    op.drop_table('expansion_opportunities')
    op.drop_index('idx_predicted_date', table_name='churn_predictions')
    op.drop_index('idx_probability', table_name='churn_predictions')
    op.drop_index('idx_customer_risk', table_name='churn_predictions')
    op.drop_table('churn_predictions')
