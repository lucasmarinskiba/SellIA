"""Add products, cart, and orders tables for Tier 4

Revision ID: 003_add_products_tables
Revises: 002_add_analytics_tables
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_products_tables'
down_revision = '002_add_analytics_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('website_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(500), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('compare_at_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('barcode', sa.String(100), nullable=True),
        sa.Column('weight', sa.Numeric(8, 2), nullable=True),
        sa.Column('inventory_count', sa.Integer(), server_default='0'),
        sa.Column('track_inventory', sa.Boolean(), server_default='true'),
        sa.Column('featured_image_url', sa.String(2048), nullable=True),
        sa.Column('images', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('status', sa.String(50), server_default='DRAFT'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['website_id'], ['websites.id'], name=op.f('fk_products_website_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_products'))
    )

    op.create_index('ix_products_website_id', 'products', ['website_id'])
    op.create_index('ix_products_website_id_status', 'products', ['website_id', 'status'])
    op.create_index('ix_products_website_id_slug', 'products', ['website_id', 'slug'])

    # product_variants table
    op.create_table(
        'product_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('inventory_count', sa.Integer(), server_default='0'),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('is_available', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_product_variants_product_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_product_variants'))
    )

    op.create_index('ix_product_variants_product_id', 'product_variants', ['product_id'])

    # product_categories table
    op.create_table(
        'product_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('website_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('image_url', sa.String(2048), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['website_id'], ['websites.id'], name=op.f('fk_product_categories_website_id')),
        sa.ForeignKeyConstraint(['parent_id'], ['product_categories.id'], name=op.f('fk_product_categories_parent_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_product_categories'))
    )

    op.create_index('ix_product_categories_website_id', 'product_categories', ['website_id'])

    # product_categories_association table
    op.create_table(
        'product_categories_association',
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_product_categories_association_product_id')),
        sa.ForeignKeyConstraint(['category_id'], ['product_categories.id'], name=op.f('fk_product_categories_association_category_id')),
        sa.PrimaryKeyConstraint('product_id', 'category_id', name=op.f('pk_product_categories_association'))
    )

    # shopping_carts table
    op.create_table(
        'shopping_carts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('website_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), server_default='ACTIVE'),
        sa.Column('subtotal', sa.Numeric(10, 2), server_default='0'),
        sa.Column('tax', sa.Numeric(10, 2), server_default='0'),
        sa.Column('shipping', sa.Numeric(10, 2), server_default='0'),
        sa.Column('discount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('total', sa.Numeric(10, 2), server_default='0'),
        sa.Column('coupon_code', sa.String(100), nullable=True),
        sa.Column('customer_email', sa.String(255), nullable=True),
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('abandoned_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['website_id'], ['websites.id'], name=op.f('fk_shopping_carts_website_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_shopping_carts'))
    )

    op.create_index('ix_shopping_carts_website_id', 'shopping_carts', ['website_id'])
    op.create_index('ix_shopping_carts_session_id', 'shopping_carts', ['session_id'])

    # cart_items table
    op.create_table(
        'cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('line_total', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['cart_id'], ['shopping_carts.id'], name=op.f('fk_cart_items_cart_id')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_cart_items_product_id')),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], name=op.f('fk_cart_items_variant_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cart_items'))
    )

    op.create_index('ix_cart_items_cart_id', 'cart_items', ['cart_id'])
    op.create_index('ix_cart_items_product_id', 'cart_items', ['product_id'])

    # orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('website_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_number', sa.String(50), nullable=False, unique=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), server_default='PENDING'),
        sa.Column('payment_status', sa.String(50), server_default='UNPAID'),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('payment_id', sa.String(255), nullable=True),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax', sa.Numeric(10, 2), server_default='0'),
        sa.Column('shipping_cost', sa.Numeric(10, 2), server_default='0'),
        sa.Column('discount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('total', sa.Numeric(10, 2), nullable=False),
        sa.Column('customer_email', sa.String(255), nullable=False),
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('shipping_address', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('billing_address', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['website_id'], ['websites.id'], name=op.f('fk_orders_website_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_orders'))
    )

    op.create_index('ix_orders_website_id', 'orders', ['website_id'])
    op.create_index('ix_orders_website_id_status', 'orders', ['website_id', 'status'])
    op.create_index('ix_orders_website_id_created_at', 'orders', ['website_id', 'created_at'])
    op.create_index('ix_orders_payment_status', 'orders', ['payment_status'])

    # order_items table
    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('product_sku', sa.String(100), nullable=True),
        sa.Column('variant_name', sa.String(255), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('line_total', sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name=op.f('fk_order_items_order_id')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_order_items_product_id')),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], name=op.f('fk_order_items_variant_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_order_items'))
    )

    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_product_id', 'order_items', ['product_id'])


def downgrade() -> None:
    op.drop_index('ix_order_items_product_id', table_name='order_items')
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_table('order_items')

    op.drop_index('ix_orders_payment_status', table_name='orders')
    op.drop_index('ix_orders_website_id_created_at', table_name='orders')
    op.drop_index('ix_orders_website_id_status', table_name='orders')
    op.drop_index('ix_orders_website_id', table_name='orders')
    op.drop_table('orders')

    op.drop_index('ix_cart_items_product_id', table_name='cart_items')
    op.drop_index('ix_cart_items_cart_id', table_name='cart_items')
    op.drop_table('cart_items')

    op.drop_index('ix_shopping_carts_session_id', table_name='shopping_carts')
    op.drop_index('ix_shopping_carts_website_id', table_name='shopping_carts')
    op.drop_table('shopping_carts')

    op.drop_table('product_categories_association')

    op.drop_index('ix_product_categories_website_id', table_name='product_categories')
    op.drop_table('product_categories')

    op.drop_index('ix_product_variants_product_id', table_name='product_variants')
    op.drop_table('product_variants')

    op.drop_index('ix_products_website_id_slug', table_name='products')
    op.drop_index('ix_products_website_id_status', table_name='products')
    op.drop_index('ix_products_website_id', table_name='products')
    op.drop_table('products')
