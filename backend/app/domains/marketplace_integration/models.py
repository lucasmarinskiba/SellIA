"""Phase 44: Multi-Platform Marketplace Integration."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class PlatformType(str, Enum):
    AMAZON = "amazon"
    MERCADO_LIBRE = "mercado_libre"
    EBAY = "ebay"
    SHOPIFY = "shopify"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    HOTMART = "hotmart"
    CLICKBANK = "clickbank"
    ALIEXPRESS = "aliexpress"

class MarketplaceConnection(Base):
    __tablename__ = "marketplace_connections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # amazon, mercado_libre, etc
    account_name = Column(String(255), nullable=False)
    auth_token = Column(Text, nullable=True)
    api_key = Column(Text, nullable=True)
    seller_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    sync_enabled = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone.utc), nullable=True)
    sync_config = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ProductSync(Base):
    __tablename__ = "product_syncs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_connections.id", ondelete="CASCADE"), nullable=False)
    local_sku = Column(String(255), nullable=False)
    platform_sku = Column(String(255), nullable=False)
    platform_id = Column(String(255), nullable=False)
    product_name = Column(String(500), nullable=False)
    price = Column(Float, default=0)
    stock_quantity = Column(Integer, default=0)
    sync_status = Column(String(50), default="synced")  # synced, pending, error
    last_error = Column(Text, nullable=True)
    auto_sync = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class DynamicPricing(Base):
    __tablename__ = "dynamic_pricing"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    product_sync_id = Column(UUID(as_uuid=True), ForeignKey("product_syncs.id", ondelete="CASCADE"), nullable=False)
    base_price = Column(Float, default=0)
    current_price = Column(Float, default=0)
    competitor_price = Column(Float, nullable=True)
    demand_factor = Column(Float, default=1.0)
    inventory_factor = Column(Float, default=1.0)
    margin_target = Column(Float, default=0.3)
    price_history = Column(JSONB, nullable=True)
    last_updated = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class MarketplaceMetrics(Base):
    __tablename__ = "marketplace_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_platforms_connected = Column(Integer, default=0)
    total_products_synced = Column(Integer, default=0)
    total_inventory_value = Column(Float, default=0)
    total_platform_sales = Column(Float, default=0)
    active_listings = Column(Integer, default=0)
    average_sell_through_rate = Column(Float, default=0)
    platform_revenue_breakdown = Column(JSONB, nullable=True)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
