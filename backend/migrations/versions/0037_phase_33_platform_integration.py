"""Phase 33: Multi-Platform Seller Automation.

Revision ID: 0037
Revises: 0036
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0037'
down_revision = '0036'


def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', sa.String(255), nullable=False),
        sa.Column('sku', sa.String(255), nullable=False, unique=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(255), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('price_base', sa.Float(), nullable=False),
        sa.Column('images', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('brand', sa.String(255), nullable=True),
        sa.Column('stock_total', sa.Integer(), nullable=False),
        sa.Column('stock_reserved', sa.Integer(), default=0),
        sa.Column('is_digital', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_seller_sku', 'products', ['seller_id', 'sku'])
    op.create_index('idx_category', 'products', ['category'])

    op.create_table(
        'platform_listings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('platform_sku', sa.String(255), nullable=False),
        sa.Column('listing_url', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('current_stock', sa.Integer(), default=0),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('rating', sa.Float(), default=0),
        sa.Column('rating_count', sa.Integer(), default=0),
        sa.Column('sales_this_month', sa.Integer(), default=0),
        sa.Column('best_seller_rank', sa.Integer(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )
    op.create_index('idx_platform_listing', 'platform_listings', ['platform', 'platform_sku'])
    op.create_index('idx_product_platform', 'platform_listings', ['product_id', 'platform'])

    op.create_table(
        'price_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_price', sa.Float(), nullable=False),
        sa.Column('new_price', sa.Float(), nullable=False),
        sa.Column('strategy', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('competitor_price', sa.Float(), nullable=True),
        sa.Column('inventory_level', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['listing_id'], ['platform_listings.id'])
    )
    op.create_index('idx_listing_history', 'price_history', ['listing_id', 'timestamp'])

    op.create_table(
        'competitor_prices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('competitor_name', sa.String(255), nullable=False),
        sa.Column('competitor_sku', sa.String(255), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('stock_level', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('sales_velocity', sa.Float(), nullable=True),
        sa.Column('best_seller_rank', sa.Integer(), nullable=True),
        sa.Column('last_checked', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )
    op.create_index('idx_competitor_product', 'competitor_prices', ['product_id', 'platform'])

    op.create_table(
        'keyword_research',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('keyword', sa.String(255), nullable=False),
        sa.Column('search_volume', sa.Integer(), nullable=False),
        sa.Column('competition', sa.String(50), nullable=False),
        sa.Column('difficulty', sa.Float(), nullable=False),
        sa.Column('opportunity_score', sa.Float(), nullable=False),
        sa.Column('current_rank', sa.Integer(), nullable=True),
        sa.Column('rank_trend', sa.String(50), nullable=True),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )
    op.create_index('idx_keyword_product', 'keyword_research', ['product_id', 'keyword'])
    op.create_index('idx_keyword_rank', 'keyword_research', ['product_id', 'current_rank'])

    op.create_table(
        'listing_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_num', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('bullet_points', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('a_b_test_group', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('conversions', sa.Integer(), default=0),
        sa.Column('impressions', sa.Integer(), default=0),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('avg_rating', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['listing_id'], ['platform_listings.id'])
    )
    op.create_index('idx_listing_versions', 'listing_versions', ['listing_id', 'is_active'])

    op.create_table(
        'customer_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('platform_review_id', sa.String(255), nullable=True),
        sa.Column('reviewer_name', sa.String(255), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=False),
        sa.Column('is_flagged', sa.Boolean(), default=False),
        sa.Column('seller_response', sa.Text(), nullable=True),
        sa.Column('response_date', sa.DateTime(), nullable=True),
        sa.Column('helpful_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['listing_id'], ['platform_listings.id'])
    )
    op.create_index('idx_listing_reviews', 'customer_reviews', ['listing_id', 'rating'])
    op.create_index('idx_flagged_reviews', 'customer_reviews', ['listing_id', 'is_flagged'])

    op.create_table(
        'orders_unified',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('platform_order_id', sa.String(255), nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('buyer_id', sa.String(255), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Integer(), default=1),
        sa.Column('order_status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('shipped_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['listing_id'], ['platform_listings.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )
    op.create_index('idx_order_platform', 'orders_unified', ['platform', 'platform_order_id'])
    op.create_index('idx_order_listing', 'orders_unified', ['listing_id', 'created_at'])

    op.create_table(
        'foom_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('urgency_badge', sa.String(255), nullable=True),
        sa.Column('scarcity_message', sa.String(255), nullable=True),
        sa.Column('social_proof', sa.String(255), nullable=True),
        sa.Column('call_to_action', sa.String(255), nullable=True),
        sa.Column('inventory_level', sa.Integer(), nullable=True),
        sa.Column('sales_velocity', sa.Float(), nullable=True),
        sa.Column('generated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['listing_id'], ['platform_listings.id'])
    )
    op.create_index('idx_foom_listing', 'foom_messages', ['listing_id', 'platform'])

    op.create_table(
        'seller_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', sa.String(255), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('metric_date', sa.DateTime()),
        sa.Column('active_listings', sa.Integer(), default=0),
        sa.Column('bestseller_count', sa.Integer(), default=0),
        sa.Column('top_5_count', sa.Integer(), default=0),
        sa.Column('avg_rating', sa.Float(), nullable=True),
        sa.Column('total_reviews', sa.Integer(), default=0),
        sa.Column('daily_orders', sa.Integer(), default=0),
        sa.Column('daily_gmv', sa.Float(), default=0),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('return_rate', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_seller_metrics', 'seller_metrics', ['seller_id', 'platform', 'metric_date'])

    op.create_table(
        'advertising_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('campaign_name', sa.String(255), nullable=False),
        sa.Column('campaign_type', sa.String(50), nullable=False),
        sa.Column('daily_budget', sa.Float(), nullable=False),
        sa.Column('start_date', sa.DateTime()),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('impressions', sa.Integer(), default=0),
        sa.Column('clicks', sa.Integer(), default=0),
        sa.Column('conversions', sa.Integer(), default=0),
        sa.Column('spend', sa.Float(), default=0),
        sa.Column('revenue', sa.Float(), default=0),
        sa.Column('acos', sa.Float(), nullable=True),
        sa.Column('roas', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['listing_id'], ['platform_listings.id'])
    )
    op.create_index('idx_campaign_listing', 'advertising_campaigns', ['listing_id', 'status'])
    op.create_index('idx_campaign_platform', 'advertising_campaigns', ['platform', 'start_date'])

    op.create_table(
        'inventory_sync_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('old_stock', sa.Integer(), nullable=False),
        sa.Column('new_stock', sa.Integer(), nullable=False),
        sa.Column('sync_status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sync_timestamp', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )
    op.create_index('idx_sync_product', 'inventory_sync_log', ['product_id', 'sync_timestamp'])


def downgrade() -> None:
    op.drop_table('inventory_sync_log')
    op.drop_table('advertising_campaigns')
    op.drop_table('seller_metrics')
    op.drop_table('foom_messages')
    op.drop_table('orders_unified')
    op.drop_table('customer_reviews')
    op.drop_table('listing_versions')
    op.drop_table('keyword_research')
    op.drop_table('competitor_prices')
    op.drop_table('price_history')
    op.drop_table('platform_listings')
    op.drop_table('products')
