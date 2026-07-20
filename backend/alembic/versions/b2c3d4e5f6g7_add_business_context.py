"""Add business_contexts table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-22 11:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'business_contexts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('business_type', sa.Enum('physical_products', 'digital_products', 'services', 'consulting', 'software', 'food_beverage', 'fashion_beauty', 'health_wellness', 'home_decor', 'handcraft', 'other', name='business_type'), nullable=False, server_default='other'),
        sa.Column('sales_model', sa.Enum('b2c', 'b2b', 'b2b2c', 'd2c', 'marketplace', name='sales_model'), nullable=False, server_default='b2c'),
        sa.Column('geographic_reach', sa.Enum('local', 'regional', 'national', 'cross_border', 'global', name='geographic_reach'), nullable=False, server_default='local'),
        sa.Column('presence_type', sa.Enum('local_physical', 'home_office', 'showroom', 'online_only', 'hybrid', name='presence_type'), nullable=False, server_default='online_only'),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('target_audience', sa.Text(), nullable=True),
        sa.Column('value_proposition', sa.Text(), nullable=True),
        sa.Column('price_range', sa.String(50), nullable=True),
        sa.Column('average_ticket', sa.Integer(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state_province', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=False, server_default='Argentina'),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('has_physical_location', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('serves_home_office', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('does_delivery', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('does_pickup', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shipping_radius_km', sa.Integer(), nullable=True),
        sa.Column('channels_configured', postgresql.JSONB(), server_default='{}'),
        sa.Column('ads_configured', postgresql.JSONB(), server_default='{}'),
        sa.Column('shipping_configured', postgresql.JSONB(), server_default='{}'),
        sa.Column('website_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('seo_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_marketing_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('primary_goal', sa.String(50), nullable=True),
        sa.Column('monthly_revenue_goal', sa.Integer(), nullable=True),
        sa.Column('monthly_leads_goal', sa.Integer(), nullable=True),
        sa.Column('target_countries', postgresql.JSONB(), server_default='[]'),
        sa.Column('ai_recommended_playbooks', postgresql.JSONB(), server_default='[]'),
        sa.Column('ai_priority_actions', postgresql.JSONB(), server_default='[]'),
        sa.Column('ai_brand_voice', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('business_contexts')
    op.execute("DROP TYPE business_type")
    op.execute("DROP TYPE sales_model")
    op.execute("DROP TYPE geographic_reach")
    op.execute("DROP TYPE presence_type")
