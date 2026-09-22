"""FOMO conversion tracking + testing models."""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, ForeignKey, func, Index, Float, Boolean, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConversionEvent(Base):
    """Track conversions linked to FOMO copy variants."""
    __tablename__ = "conversion_events"
    __table_args__ = (
        Index("idx_business_conversions", "business_id"),
        Index("idx_link_conversions", "link_id"),
        Index("idx_variant_conversions", "fomo_variant_id"),
        Index("idx_platform_conversions", "platform_name"),
        Index("idx_created_at", "created_at"),
        # Makes duplicate-webhook ingestion (Mercado Libre resends notifications)
        # a DB-enforced no-op instead of a check-then-insert race. Only enforced
        # when a source actually supplies a stable per-event id — most sources
        # (manual logs) leave external_event_id NULL and stay unconstrained.
        # On an existing database this index is added by
        # conversion_events_bootstrap.ensure_conversion_event_dedupe_column().
        Index(
            "uq_conversion_dedupe", "business_id", "platform_name", "external_listing_id", "external_event_id",
            unique=True, postgresql_where=text("external_event_id IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    link_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE"))

    # Which FOMO variant caused this conversion (if A/B test)
    fomo_variant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_link_fomo.id", ondelete="SET NULL"), nullable=True)

    # Platform + external listing ID for reference
    platform_name: Mapped[str] = mapped_column(String(50))
    external_listing_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # A stable per-event id from the source (e.g. Mercado Libre's order id).
    # Paired with (business_id, platform_name, external_listing_id) in a
    # partial unique index so a resent webhook can't double-record a sale.
    external_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Conversion metadata
    conversion_value: Mapped[float] = mapped_column(default=0.0)  # revenue if available
    conversion_type: Mapped[str] = mapped_column(String(50))  # purchase, inquiry, click, add_to_cart

    # Raw event from platform webhook
    raw_event_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class FOMABTest(Base):
    """A/B test for FOMO copy variants."""
    # Not "fomo_ab_tests": app.domains.fomo.models.FOMOABTest already owns that name, and the
    # clash made SQLAlchemy mapper configuration fail app-wide.
    __tablename__ = "seo_fomo_ab_tests"
    __table_args__ = (
        Index("idx_link_ab_tests", "link_id"),
        Index("idx_business_ab_tests", "business_id"),
        Index("idx_status_ab_tests", "status"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    link_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE"))

    # Variants being tested
    variant_a_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_link_fomo.id", ondelete="CASCADE"))
    variant_b_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_link_fomo.id", ondelete="CASCADE"))
    variant_c_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_link_fomo.id", ondelete="CASCADE"), nullable=True)

    # Traffic split (20/20/60 default)
    variant_a_split: Mapped[float] = mapped_column(default=0.20)
    variant_b_split: Mapped[float] = mapped_column(default=0.20)
    variant_c_split: Mapped[float] = mapped_column(default=0.60)

    # Test status
    status: Mapped[str] = mapped_column(String(20))  # running, completed, paused
    min_conversions_for_winner: Mapped[int] = mapped_column(default=100)

    # Winner
    winner_variant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_link_fomo.id", ondelete="SET NULL"), nullable=True)
    winner_announced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metrics
    total_conversions: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FOMADecayLog(Base):
    """Track when FOMO copy effectiveness degrades."""
    __tablename__ = "fomo_decay_logs"
    __table_args__ = (
        Index("idx_link_decay", "link_id"),
        Index("idx_business_decay", "business_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    link_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE"))
    fomo_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_link_fomo.id", ondelete="CASCADE"))

    # Decay metrics
    previous_ctr: Mapped[float] = mapped_column()
    current_ctr: Mapped[float] = mapped_column()
    decay_percentage: Mapped[float] = mapped_column()  # (prev - curr) / prev * 100

    # Action taken
    action: Mapped[str] = mapped_column(String(50))  # regenerate, rotate, pause
    regenerated_fomo_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_link_fomo.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


FOMO_PHASE1_TABLES = [
    ConversionEvent.__table__,
    FOMABTest.__table__,
    FOMADecayLog.__table__,
]
