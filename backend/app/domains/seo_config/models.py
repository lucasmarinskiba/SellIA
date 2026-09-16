"""SEO Configuration & Publication Link Models."""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, ForeignKey, func, Boolean, Index, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SEOConfig(Base):
    """Global SEO configuration & per-platform toggles."""
    __tablename__ = "seo_config"
    __table_args__ = (
        UniqueConstraint("business_id", name="uq_seo_config_business"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    # Global toggle: if False, all SEO is disabled regardless of platform/link settings
    global_seo_enabled: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PlatformSEOStatus(Base):
    """Per-platform SEO enable/disable status."""
    __tablename__ = "platform_seo_status"
    __table_args__ = (
        UniqueConstraint("connection_id", name="uq_platform_seo_connection"),
        Index("idx_business_platform_seo", "business_id", "connection_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    connection_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("integration_connections.id", ondelete="CASCADE"))

    # Platform name cache for quick access (e.g., "mercado-libre", "amazon", "shopify")
    platform_name: Mapped[str] = mapped_column(String(50))

    # SEO enabled for this platform
    seo_enabled: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PublicationLink(Base):
    """Publication URLs for SEO positioning (social/marketplace posts, listing links, etc)."""
    __tablename__ = "publication_links"
    __table_args__ = (
        Index("idx_business_publication", "business_id"),
        Index("idx_product_publication", "product_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    # Optional: link to specific product if it's product-related
    product_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)

    # Optional: if link came from a platform integration
    connection_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("integration_connections.id", ondelete="SET NULL"), nullable=True)

    # The URL to optimize
    url: Mapped[str] = mapped_column(String(500))

    # User-provided title/label for the link
    title: Mapped[str] = mapped_column(String(255))

    # Platform/source: instagram, tiktok, mercado-libre, amazon, shopify, custom, etc.
    platform_source: Mapped[str] = mapped_column(String(50))

    # SEO enabled for this specific link
    seo_enabled: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PublicationLinkFOMO(Base):
    """Generated FOMO copy for a publication link."""
    __tablename__ = "publication_link_fomo"
    __table_args__ = (
        Index("idx_link_fomo", "link_id"),
        Index("idx_business_fomo", "business_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    link_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE"))

    # Generated FOMO elements
    urgency_trigger: Mapped[str | None] = mapped_column(String(100), nullable=True)  # limited_stock, ending_soon, best_seller
    social_proof_element: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g., "500+ sales this month"
    scarcity_message: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g., "Only 3 left in stock"
    call_to_action: Mapped[str] = mapped_column(String(255))  # e.g., "Get it now before it's gone"

    # Full generated copy for the link
    generated_copy: Mapped[str] = mapped_column(Text)  # Complete FOMO-optimized description

    # Quality metrics
    fomo_score: Mapped[float] = mapped_column(default=0.0)  # 0-100, how strong the FOMO
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PlatformSyncLog(Base):
    """Track every attempt to sync FOMO copy to a platform."""
    __tablename__ = "platform_sync_logs"
    __table_args__ = (
        Index("idx_link_sync", "link_id"),
        Index("idx_business_sync", "business_id"),
        Index("idx_platform_sync", "platform_name"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    link_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE"))
    fomo_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_link_fomo.id", ondelete="SET NULL"), nullable=True)

    # Platform target
    platform_name: Mapped[str] = mapped_column(String(50))
    external_listing_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # What was synced
    sync_type: Mapped[str] = mapped_column(String(50))  # title_update, description_update, full_update

    # Status
    status: Mapped[str] = mapped_column(String(20))  # pending, synced, failed, skipped
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sync metadata
    data_sent: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


SEO_CONFIG_TABLES = [
    SEOConfig.__table__,
    PlatformSEOStatus.__table__,
    PublicationLink.__table__,
    PublicationLinkFOMO.__table__,
    PlatformSyncLog.__table__,
]
