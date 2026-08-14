"""Phase 33 Database Models - Multi-Platform Seller Automation."""

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, Enum, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid
import enum

from backend.app.database import Base


class PlatformEnum(str, enum.Enum):
    """Platform types."""
    MERCADO_LIBRE = "mercado_libre"
    AMAZON = "amazon"
    HOTMART = "hotmart"


class ListingStatusEnum(str, enum.Enum):
    """Listing status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELISTED = "delisted"
    SUSPENDED = "suspended"


class PricingStrategyEnum(str, enum.Enum):
    """Pricing strategy types."""
    UNDERCUT_COMPETITOR = "undercut_competitor"
    MAINTAIN_MARGIN = "maintain_margin"
    SCARCITY_PREMIUM = "scarcity_premium"
    SEASONAL_SURGE = "seasonal_surge"
    FIRST_MOVER = "first_mover"


class Product(Base):
    """Master product catalog (unified across platforms)."""
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(String(255), nullable=False)  # Link to seller account
    sku = Column(String(255), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(255), nullable=False)
    cost = Column(Float, nullable=False)  # COGS
    price_base = Column(Float, nullable=False)  # Target/baseline price
    images = Column(ARRAY(String), nullable=True)  # List of image URLs
    brand = Column(String(255), nullable=True)
    stock_total = Column(Integer, nullable=False)
    stock_reserved = Column(Integer, default=0)  # Reserved from recent sales
    is_digital = Column(Boolean, default=False)  # Digital vs physical
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_seller_sku', 'seller_id', 'sku'),
        Index('idx_category', 'category'),
    )


class PlatformListing(Base):
    """Per-platform SKU mapping + listing metadata."""
    __tablename__ = "platform_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    platform = Column(String(50), nullable=False)  # 'mercado_libre', 'amazon', 'hotmart'
    platform_sku = Column(String(255), nullable=False)  # ML item_id, ASIN, Hotmart product_id
    listing_url = Column(String(500), nullable=False)
    status = Column(String(50), default='active')  # active, inactive, delisted
    current_stock = Column(Integer, default=0)  # Latest sync
    current_price = Column(Float, nullable=False)
    rating = Column(Float, default=0)  # Stars (0-5)
    rating_count = Column(Integer, default=0)  # Number of reviews
    sales_this_month = Column(Integer, default=0)
    best_seller_rank = Column(Integer, nullable=True)  # #1, #2, etc (per category)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_platform_listing', 'platform', 'platform_sku'),
        Index('idx_product_platform', 'product_id', 'platform'),
    )


class PriceHistory(Base):
    """Track price changes over time (for analytics)."""
    __tablename__ = "price_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey('platform_listings.id'), nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    strategy = Column(String(50), nullable=False)  # Pricing strategy applied
    reason = Column(Text, nullable=True)  # Why price changed
    competitor_price = Column(Float, nullable=True)
    inventory_level = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_listing_history', 'listing_id', 'timestamp'),
    )


class CompetitorPrice(Base):
    """Monitor competitor prices in real-time."""
    __tablename__ = "competitor_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    competitor_name = Column(String(255), nullable=False)
    competitor_sku = Column(String(255), nullable=True)
    price = Column(Float, nullable=False)
    stock_level = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    sales_velocity = Column(Float, nullable=True)  # Units/day
    best_seller_rank = Column(Integer, nullable=True)
    last_checked = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_competitor_product', 'product_id', 'platform'),
    )


class KeywordResearch(Base):
    """Keyword research + ranking data."""
    __tablename__ = "keyword_research"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    keyword = Column(String(255), nullable=False)
    search_volume = Column(Integer, nullable=False)  # Monthly searches
    competition = Column(String(50), nullable=False)  # low, medium, high
    difficulty = Column(Float, nullable=False)  # 0-1 ranking difficulty
    opportunity_score = Column(Float, nullable=False)  # 0-1 recommended
    current_rank = Column(Integer, nullable=True)  # Current position (#1, #10, etc)
    rank_trend = Column(String(50), nullable=True)  # up, down, stable
    conversion_rate = Column(Float, nullable=True)  # % of searchers who buy
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_keyword_product', 'product_id', 'keyword'),
        Index('idx_keyword_rank', 'product_id', 'current_rank'),
    )


class ListingVersion(Base):
    """A/B test different listing variations."""
    __tablename__ = "listing_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey('platform_listings.id'), nullable=False)
    version_num = Column(Integer, nullable=False)  # v1, v2, v3
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    bullet_points = Column(ARRAY(String), nullable=True)  # Amazon bullets
    keywords = Column(ARRAY(String), nullable=True)
    a_b_test_group = Column(String(50), nullable=True)  # control, treatment_a, treatment_b
    is_active = Column(Boolean, default=True)
    conversions = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    conversion_rate = Column(Float, nullable=True)
    avg_rating = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_listing_versions', 'listing_id', 'is_active'),
    )


class CustomerReview(Base):
    """Customer reviews pulled from each platform."""
    __tablename__ = "customer_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey('platform_listings.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    platform_review_id = Column(String(255), nullable=True)
    reviewer_name = Column(String(255), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_text = Column(Text, nullable=False)
    is_flagged = Column(Boolean, default=False)  # Negative/spam
    seller_response = Column(Text, nullable=True)  # Response from seller
    response_date = Column(DateTime, nullable=True)
    helpful_count = Column(Integer, default=0)  # Upvotes
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_listing_reviews', 'listing_id', 'rating'),
        Index('idx_flagged_reviews', 'listing_id', 'is_flagged'),
    )


class Order(Base):
    """Unified order tracking across platforms."""
    __tablename__ = "orders_unified"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform = Column(String(50), nullable=False)
    platform_order_id = Column(String(255), nullable=False)
    listing_id = Column(UUID(as_uuid=True), ForeignKey('platform_listings.id'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    buyer_id = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    order_status = Column(String(50), nullable=False)  # pending, shipped, delivered, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_order_platform', 'platform', 'platform_order_id'),
        Index('idx_order_listing', 'listing_id', 'created_at'),
    )


class FOOMMessage(Base):
    """Generated urgency/FOOM messages (cached)."""
    __tablename__ = "foom_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey('platform_listings.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    urgency_badge = Column(String(255), nullable=True)  # 🔥, ⭐, etc
    scarcity_message = Column(String(255), nullable=True)  # "Only X left"
    social_proof = Column(String(255), nullable=True)  # "100+ sold"
    call_to_action = Column(String(255), nullable=True)  # "Buy now"
    inventory_level = Column(Integer, nullable=True)
    sales_velocity = Column(Float, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_foom_listing', 'listing_id', 'platform'),
    )


class SellerMetrics(Base):
    """Daily seller metrics per platform."""
    __tablename__ = "seller_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    metric_date = Column(DateTime, default=datetime.utcnow)
    active_listings = Column(Integer, default=0)
    bestseller_count = Column(Integer, default=0)  # #1 rankings
    top_5_count = Column(Integer, default=0)  # Top 5 rankings
    avg_rating = Column(Float, nullable=True)  # Seller rating
    total_reviews = Column(Integer, default=0)
    daily_orders = Column(Integer, default=0)
    daily_gmv = Column(Float, default=0)
    conversion_rate = Column(Float, nullable=True)
    return_rate = Column(Float, nullable=True)

    __table_args__ = (
        Index('idx_seller_metrics', 'seller_id', 'platform', 'metric_date'),
    )


class AdvertisingCampaign(Base):
    """Auto-launched advertising campaigns (Mercado Ads, Amazon Sponsored)."""
    __tablename__ = "advertising_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey('platform_listings.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    campaign_name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), nullable=False)  # sponsored_products, manual_ads
    daily_budget = Column(Float, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(50), default='active')  # active, paused, ended
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Float, default=0)
    revenue = Column(Float, default=0)
    acos = Column(Float, nullable=True)  # Advertising Cost of Sale
    roas = Column(Float, nullable=True)  # Return on Ad Spend
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_campaign_listing', 'listing_id', 'status'),
        Index('idx_campaign_platform', 'platform', 'start_date'),
    )


class PlatformCredential(Base):
    """OAuth/API credentials for platform connections."""
    __tablename__ = "platform_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)  # mercado_libre, amazon, hotmart
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    seller_username = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_seller_platform', 'seller_id', 'platform'),
        Index('idx_active_credentials', 'seller_id', 'is_active'),
    )


class InventorySyncLog(Base):
    """Audit trail: all inventory sync operations."""
    __tablename__ = "inventory_sync_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    old_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    sync_status = Column(String(50), nullable=False)  # success, failed
    error_message = Column(Text, nullable=True)
    sync_timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_sync_product', 'product_id', 'sync_timestamp'),
    )
