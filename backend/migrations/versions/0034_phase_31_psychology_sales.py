"""Phase 31: Psychology Sales schema.

Revision ID: 0034
Revises: 0033
Create Date: 2026-08-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0034'
down_revision = '0033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create discovery_responses table
    op.create_table(
        'discovery_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('question_category', sa.String(50), nullable=True),
        sa.Column('sentiment', sa.String(50), nullable=True),
        sa.Column('urgency_level', sa.Integer(), nullable=True),
        sa.Column('pain_points', postgresql.JSONB(), nullable=True),
        sa.Column('needs_identified', postgresql.JSONB(), nullable=True),
        sa.Column('asked_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_deal_category', 'discovery_responses', ['deal_id', 'question_category'])
    op.create_index('idx_urgency', 'discovery_responses', ['urgency_level'])

    # Create need_narratives table
    op.create_table(
        'need_narratives',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('narrative', sa.Text(), nullable=False),
        sa.Column('financial_impact_calculated', sa.Float(), nullable=True),
        sa.Column('pain_points', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_deal_impact', 'need_narratives', ['deal_id', 'financial_impact_calculated'])

    # Create objection_handling table
    op.create_table(
        'objection_handling',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('objection_text', sa.Text(), nullable=False),
        sa.Column('objection_type', sa.String(50), nullable=True),
        sa.Column('objection_source', sa.String(50), nullable=True),
        sa.Column('response_generated', sa.Text(), nullable=True),
        sa.Column('response_delivered', sa.Text(), nullable=True),
        sa.Column('prospect_response', sa.Text(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('resolution_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_deal_type', 'objection_handling', ['deal_id', 'objection_type'])
    op.create_index('idx_resolved', 'objection_handling', ['resolved'])

    # Create close_attempts table
    op.create_table(
        'close_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('close_step', sa.Integer(), nullable=False),
        sa.Column('commitment_asked', sa.Text(), nullable=False),
        sa.Column('psychology_principle', sa.String(255), nullable=True),
        sa.Column('prospect_response', sa.Text(), nullable=True),
        sa.Column('response_sentiment', sa.String(50), nullable=True),
        sa.Column('committed', sa.Boolean(), nullable=True),
        sa.Column('commitment_type', sa.String(50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_deal_step', 'close_attempts', ['deal_id', 'close_step'])
    op.create_index('idx_committed', 'close_attempts', ['committed'])

    # Create sales_conversations table
    op.create_table(
        'sales_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('conversation_json', postgresql.JSONB(), nullable=True),
        sa.Column('sentiment_progression', postgresql.JSONB(), nullable=True),
        sa.Column('discovery_questions_asked', sa.Integer(), nullable=True),
        sa.Column('need_narrative_used', sa.Boolean(), nullable=True),
        sa.Column('urgency_triggers_used', postgresql.JSONB(), nullable=True),
        sa.Column('objections_handled', sa.Integer(), nullable=True),
        sa.Column('closes_attempted', sa.Integer(), nullable=True),
        sa.Column('deal_won', sa.Boolean(), nullable=True),
        sa.Column('deal_value', sa.Float(), nullable=True),
        sa.Column('sales_cycle_days', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_deal_won', 'sales_conversations', ['deal_id', 'deal_won'])
    op.create_index('idx_closed_at', 'sales_conversations', ['closed_at'])

    # Create sales_rep_performance_psychology table
    op.create_table(
        'sales_rep_performance_psychology',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rep_id', sa.String(255), nullable=False),
        sa.Column('discovery_questions_per_call', sa.Float(), nullable=True),
        sa.Column('percent_prospects_opening_up', sa.Float(), nullable=True),
        sa.Column('narratives_deployed', sa.Integer(), nullable=True),
        sa.Column('avg_financial_impact_quantified', sa.Float(), nullable=True),
        sa.Column('urgency_triggers_per_deal', sa.Float(), nullable=True),
        sa.Column('close_attempts_per_deal', sa.Float(), nullable=True),
        sa.Column('close_rate', sa.Float(), nullable=True),
        sa.Column('average_closes_to_win', sa.Float(), nullable=True),
        sa.Column('sales_cycle_avg_days', sa.Integer(), nullable=True),
        sa.Column('aov', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rep_id', 'sales_rep_performance_psychology', ['rep_id'])
    op.create_index('idx_close_rate', 'sales_rep_performance_psychology', ['close_rate'])


def downgrade() -> None:
    op.drop_index('idx_close_rate', table_name='sales_rep_performance_psychology')
    op.drop_index('idx_rep_id', table_name='sales_rep_performance_psychology')
    op.drop_table('sales_rep_performance_psychology')
    op.drop_index('idx_closed_at', table_name='sales_conversations')
    op.drop_index('idx_deal_won', table_name='sales_conversations')
    op.drop_table('sales_conversations')
    op.drop_index('idx_committed', table_name='close_attempts')
    op.drop_index('idx_deal_step', table_name='close_attempts')
    op.drop_table('close_attempts')
    op.drop_index('idx_resolved', table_name='objection_handling')
    op.drop_index('idx_deal_type', table_name='objection_handling')
    op.drop_table('objection_handling')
    op.drop_index('idx_deal_impact', table_name='need_narratives')
    op.drop_table('need_narratives')
    op.drop_index('idx_urgency', table_name='discovery_responses')
    op.drop_index('idx_deal_category', table_name='discovery_responses')
    op.drop_table('discovery_responses')
