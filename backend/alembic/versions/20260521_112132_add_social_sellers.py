"""add social sellers tables

Revision ID: social_sellers_20250521
Revises: 91c3d4e5f6a7
Create Date: 2025-05-21 11:20:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'social_sellers_20250521'
down_revision = '91c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('social_sellers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('personality_slug', sa.String(length=100), nullable=True),
        sa.Column('voice_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('stats', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('ai_auto_reply', sa.Boolean(), nullable=False),
        sa.Column('greeting_message', sa.Text(), nullable=True),
        sa.Column('closing_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_social_sellers_business_id'), 'social_sellers', ['business_id'], unique=False)

    op.create_table('seller_customer_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('first_contact_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_contact_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_interactions', sa.Integer(), nullable=False),
        sa.Column('deals_closed', sa.Integer(), nullable=False),
        sa.Column('total_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('relationship_stage', sa.String(length=30), nullable=False),
        sa.Column('loyalty_score', sa.Integer(), nullable=False),
        sa.Column('next_best_action', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['seller_id'], ['social_sellers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seller_customer_relationships_seller_id'), 'seller_customer_relationships', ['seller_id'], unique=False)
    op.create_index(op.f('ix_seller_customer_relationships_customer_id'), 'seller_customer_relationships', ['customer_id'], unique=False)

    op.create_table('seller_performances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('leads_acquired', sa.Integer(), nullable=False),
        sa.Column('messages_sent', sa.Integer(), nullable=False),
        sa.Column('conversations_active', sa.Integer(), nullable=False),
        sa.Column('deals_won', sa.Integer(), nullable=False),
        sa.Column('revenue', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('conversion_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('best_performing_hour', sa.Integer(), nullable=True),
        sa.Column('best_performing_content_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['seller_id'], ['social_sellers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seller_performances_seller_id'), 'seller_performances', ['seller_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_seller_performances_seller_id'), table_name='seller_performances')
    op.drop_table('seller_performances')
    op.drop_index(op.f('ix_seller_customer_relationships_customer_id'), table_name='seller_customer_relationships')
    op.drop_index(op.f('ix_seller_customer_relationships_seller_id'), table_name='seller_customer_relationships')
    op.drop_table('seller_customer_relationships')
    op.drop_index(op.f('ix_social_sellers_business_id'), table_name='social_sellers')
    op.drop_table('social_sellers')
