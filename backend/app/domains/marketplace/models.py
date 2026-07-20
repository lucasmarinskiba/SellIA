"""
SellIA Marketplace

Users can discover, purchase and manage digital goods, services,
apps, templates, and integrations to grow their business.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class MarketplaceCategory(str, enum.Enum):
    TEMPLATE = "template"           # Website templates, email templates
    APP = "app"                     # Third-party app integrations
    SERVICE = "service"             # Done-for-you services
    DIGITAL_PRODUCT = "digital_product"  # E-books, courses, presets
    PROGRAM = "program"             # Software/plugins
    BUNDLE = "bundle"               # Bundled offerings


class MarketplaceItem(Base):
    """An item available for purchase in the marketplace."""
    __tablename__ = "marketplace_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    short_description = Column(String(500), nullable=True)
    category = Column(Enum(MarketplaceCategory), nullable=False, index=True)
    tags = Column(JSONB, default=list, nullable=False)

    # Pricing
    price_usd = Column(Numeric(10, 2), nullable=False)
    compare_price_usd = Column(Numeric(10, 2), nullable=True)  # Original price for discounts
    currency = Column(String(3), default="USD", nullable=False)

    # Media
    thumbnail_url = Column(String(500), nullable=True)
    preview_urls = Column(JSONB, default=list, nullable=False)  # Array of image URLs
    demo_url = Column(String(500), nullable=True)

    # Product details
    extra_data = Column(JSONB, default=dict, nullable=False)
    # For apps: {api_endpoints, setup_instructions, oauth_required}
    # For templates: {file_format, pages_included, compatible_with}
    # For services: {delivery_time, revisions_included, scope}

    # Stats
    rating_avg = Column(Numeric(2, 1), default=0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    purchase_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)

    # FOMO / Urgency
    is_limited = Column(Boolean, default=False, nullable=False)
    stock_remaining = Column(Integer, nullable=True)
    offer_ends_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_approved = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class MarketplacePurchase(Base):
    """A purchase transaction in the marketplace."""
    __tablename__ = "marketplace_purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_items.id", ondelete="CASCADE"), nullable=False, index=True)

    price_paid = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="completed", nullable=False)  # pending | completed | refunded | disputed

    # Delivery
    delivery_data = Column(JSONB, default=dict, nullable=False)  # download_links, api_keys, access_tokens
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    # Review
    rating = Column(Integer, nullable=True)
    review_text = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
