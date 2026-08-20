"""Phase 45: Product Management & Inventory."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(255), nullable=False, unique=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=False)
    subcategory = Column(String(255), nullable=True)
    cost_price = Column(Float, default=0)
    base_price = Column(Float, default=0)
    images = Column(ARRAY(String), nullable=True)
    attributes = Column(JSONB, nullable=True)
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(500), nullable=True)
    seo_keywords = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), nullable=True)
    quantity_on_hand = Column(Integer, default=0)
    quantity_reserved = Column(Integer, default=0)
    quantity_available = Column(Integer, default=0)
    reorder_point = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    stockout_alert = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    variant_sku = Column(String(255), nullable=False)
    variant_name = Column(String(255), nullable=False)
    attributes = Column(JSONB, nullable=True)  # size, color, etc
    price_modifier = Column(Float, default=0)
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ContentTemplate(Base):
    __tablename__ = "content_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    template_type = Column(String(50), nullable=False)  # product_title, description, social_post
    template_name = Column(String(255), nullable=False)
    content_template = Column(Text, nullable=False)
    variables = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ProductPerformance(Base):
    __tablename__ = "product_performance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    revenue = Column(Float, default=0)
    conversion_rate = Column(Float, default=0)
    rating = Column(Float, default=0)
    reviews_count = Column(Integer, default=0)
    rank_in_category = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
