from sqlalchemy import Column, String, Text, Integer, Numeric, Boolean, DateTime, ForeignKey, Index, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4

from app.core.database import Base

# Association table for product categories
product_categories = Table(
    'storefront_product_categories_association',
    Base.metadata,
    Column('product_id', UUID(as_uuid=True), ForeignKey('storefront_products.id', ondelete='CASCADE')),
    Column('category_id', UUID(as_uuid=True), ForeignKey('storefront_product_categories.id', ondelete='CASCADE')),
)


class Product(Base):
    # Namespaced (not plain 'products') -- app.models.platform_integration.py
    # ALSO declares a table literally named 'products' (multi-marketplace
    # listings, a different concept) on this same Base.metadata. Both
    # modules failed to import for unrelated reasons until this session's
    # fixes, so this collision was never actually exercised before; now
    # that both load, whichever won registration first silently caused
    # the other's router to be skipped. Neither table exists in the live
    # DB yet (confirmed via direct query), so renaming here is data-loss
    # -free -- this is a storefront/checkout product, not a marketplace
    # listing, so it gets the more specific name.
    __tablename__ = 'storefront_products'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey('websites.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text(), nullable=True)
    short_description = Column(String(500), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    compare_at_price = Column(Numeric(10, 2), nullable=True)  # Original price for showing discount
    sku = Column(String(100), nullable=True)
    barcode = Column(String(100), nullable=True)
    weight = Column(Numeric(8, 2), nullable=True)  # kg
    inventory_count = Column(Integer(), default=0)
    track_inventory = Column(Boolean(), default=True)
    featured_image_url = Column(String(2048), nullable=True)
    images = Column(JSON(), default=list)  # Array of image URLs
    # Python attribute renamed from `metadata` -- that name is reserved by
    # SQLAlchemy's Declarative API (every Base subclass already has a class
    # -level `metadata` for the table registry), so declaring a column
    # attribute with that exact name raises InvalidRequestError at class
    # -definition time. That failure took down this entire module's import
    # (and with it every Product/ShoppingCart/Order-dependent router) --
    # confirmed via production logs: "Skipped extra router ... products.py:
    # Attribute name 'metadata' is reserved". The DB column itself really is
    # named `metadata` (see alembic/versions/003_add_products_tables.py), so
    # keep that via Column("metadata", ...) and only rename the Python side.
    extra_data = Column("metadata", JSON(), default=dict)  # Custom fields, seo data, etc.
    status = Column(String(50), default='DRAFT')  # DRAFT, PUBLISHED, ARCHIVED
    is_active = Column(Boolean(), default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    variants = relationship('app.domains.products.models.ProductVariant', back_populates='product', cascade='all, delete-orphan')
    categories = relationship('app.domains.products.models.ProductCategory', secondary=product_categories, back_populates='products')
    cart_items = relationship('app.domains.products.models.CartItem', back_populates='product', cascade='all, delete-orphan')
    order_items = relationship('app.domains.products.models.OrderItem', back_populates='product')

    __table_args__ = (
        Index('ix_products_website_id', 'website_id'),
        Index('ix_products_website_id_status', 'website_id', 'status'),
        Index('ix_products_website_id_slug', 'website_id', 'slug'),
    )


class ProductVariant(Base):
    __tablename__ = 'storefront_product_variants'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('storefront_products.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)  # e.g., "Red XL"
    sku = Column(String(100), nullable=True)
    price = Column(Numeric(10, 2), nullable=True)  # Override product price if set
    inventory_count = Column(Integer(), default=0)
    attributes = Column(JSON(), default=dict)  # {color: "red", size: "XL"}
    is_available = Column(Boolean(), default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    product = relationship('app.domains.products.models.Product', back_populates='variants')
    cart_items = relationship('app.domains.products.models.CartItem', back_populates='variant')
    order_items = relationship('app.domains.products.models.OrderItem', back_populates='variant')

    __table_args__ = (
        Index('ix_product_variants_product_id', 'product_id'),
    )


class ProductCategory(Base):
    __tablename__ = 'storefront_product_categories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey('websites.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text(), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('storefront_product_categories.id'), nullable=True)
    image_url = Column(String(2048), nullable=True)
    is_active = Column(Boolean(), default=True)
    display_order = Column(Integer(), default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    products = relationship('app.domains.products.models.Product', secondary=product_categories, back_populates='categories')

    __table_args__ = (
        Index('ix_product_categories_website_id', 'website_id'),
    )


class ShoppingCart(Base):
    __tablename__ = 'storefront_shopping_carts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey('websites.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(String(255), nullable=True)  # For anonymous carts
    user_id = Column(UUID(as_uuid=True), nullable=True)  # For logged-in users
    status = Column(String(50), default='ACTIVE')  # ACTIVE, ABANDONED, CONVERTED
    subtotal = Column(Numeric(10, 2), default=0)
    tax = Column(Numeric(10, 2), default=0)
    shipping = Column(Numeric(10, 2), default=0)
    discount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), default=0)
    coupon_code = Column(String(100), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    extra_data = Column("metadata", JSON(), default=dict)  # see Product.extra_data for why
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    abandoned_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    items = relationship('app.domains.products.models.CartItem', back_populates='cart', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_shopping_carts_website_id', 'website_id'),
        Index('ix_shopping_carts_session_id', 'session_id'),
    )


class CartItem(Base):
    __tablename__ = 'storefront_cart_items'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey('storefront_shopping_carts.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('storefront_products.id', ondelete='CASCADE'), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey('storefront_product_variants.id'), nullable=True)
    quantity = Column(Integer(), default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)  # Price at time of add-to-cart
    line_total = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cart = relationship('app.domains.products.models.ShoppingCart', back_populates='items')
    product = relationship('app.domains.products.models.Product', back_populates='cart_items')
    variant = relationship('app.domains.products.models.ProductVariant', back_populates='cart_items')

    __table_args__ = (
        Index('ix_cart_items_cart_id', 'cart_id'),
        Index('ix_cart_items_product_id', 'product_id'),
    )


class Order(Base):
    __tablename__ = 'storefront_orders'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey('websites.id', ondelete='CASCADE'), nullable=False)
    order_number = Column(String(50), nullable=False, unique=True)  # User-friendly ID like ORD-2026-001
    session_id = Column(String(255), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), default='PENDING')  # PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED
    payment_status = Column(String(50), default='UNPAID')  # UNPAID, PAID, FAILED, REFUNDED
    payment_method = Column(String(50), nullable=True)  # stripe, mercado_pago, bank_transfer
    payment_id = Column(String(255), nullable=True)  # External payment processor ID
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0)
    shipping_cost = Column(Numeric(10, 2), default=0)
    discount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=True)
    shipping_address = Column(JSON(), nullable=True)  # {street, city, state, zip, country}
    billing_address = Column(JSON(), nullable=True)
    notes = Column(Text(), nullable=True)
    extra_data = Column("metadata", JSON(), default=dict)  # see Product.extra_data for why
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    items = relationship('app.domains.products.models.OrderItem', back_populates='order', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_orders_website_id', 'website_id'),
        Index('ix_orders_website_id_status', 'website_id', 'status'),
        Index('ix_orders_website_id_created_at', 'website_id', 'created_at'),
        Index('ix_orders_payment_status', 'payment_status'),
    )


class OrderItem(Base):
    __tablename__ = 'storefront_order_items'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('storefront_orders.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('storefront_products.id'), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey('storefront_product_variants.id'), nullable=True)
    product_name = Column(String(255), nullable=False)  # Snapshot at time of order
    product_sku = Column(String(100), nullable=True)
    variant_name = Column(String(255), nullable=True)
    quantity = Column(Integer(), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)

    # Relationships
    order = relationship('app.domains.products.models.Order', back_populates='items')
    product = relationship('app.domains.products.models.Product', back_populates='order_items')
    variant = relationship('app.domains.products.models.ProductVariant', back_populates='order_items')

    __table_args__ = (
        Index('ix_order_items_order_id', 'order_id'),
        Index('ix_order_items_product_id', 'product_id'),
    )
