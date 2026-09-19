"""Platform-algorithm-aware positioning score models."""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, ForeignKey, func, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PublicationLinkPositioningScore(Base):
    """Composite 0-100 positioning score snapshot for one link, one point in time."""
    __tablename__ = "publication_link_positioning_scores"
    __table_args__ = (
        Index("idx_link_positioning", "link_id"),
        Index("idx_business_positioning", "business_id"),
        Index("idx_computed_at_positioning", "computed_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True
    )
    link_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE")
    )

    platform_name: Mapped[str] = mapped_column(String(50))
    composite_score: Mapped[float] = mapped_column(default=0.0)  # 0-100, mean of available sub-scores

    # Per-dimension sub-scores (community "5 pillar" model for marketplaces,
    # plus an engagement pillar for social platforms). Nullable because not
    # every platform maps to every pillar, and a pillar with no fetchable
    # signal (e.g. price_competitiveness_score today) stays NULL rather than
    # being fabricated.
    reputation_score: Mapped[float | None] = mapped_column(nullable=True)
    conversion_score: Mapped[float | None] = mapped_column(nullable=True)
    price_competitiveness_score: Mapped[float | None] = mapped_column(nullable=True)
    listing_quality_score: Mapped[float | None] = mapped_column(nullable=True)
    logistics_score: Mapped[float | None] = mapped_column(nullable=True)
    engagement_score: Mapped[float | None] = mapped_column(nullable=True)  # Instagram/social

    # Full raw signal list (list[RankingSignal.as_dict()]) for audit/debug.
    raw_signals: Mapped[dict] = mapped_column(JSONB, default=dict)

    # % of raw_signals with measured=True — surfaced as a trust indicator so a
    # score built mostly from unmeasured/heuristic signals reads as such.
    measured_signal_pct: Mapped[float] = mapped_column(default=0.0)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StorePositioningScore(Base):
    """Composite 0-100 store/brand-presence score, scoped to business + platform
    (NOT to a link — this represents the whole storefront, e.g. an Amazon Brand
    Store), so it lives apart from PublicationLinkPositioningScore."""
    __tablename__ = "store_positioning_scores"
    __table_args__ = (
        Index("idx_business_platform_store_positioning", "business_id", "platform_name"),
        Index("idx_computed_at_store_positioning", "computed_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True
    )
    platform_name: Mapped[str] = mapped_column(String(50))
    composite_score: Mapped[float] = mapped_column(default=0.0)  # 0-100, mean of available sub-scores

    # Nullable: a pillar with no honest signal stays NULL and is excluded from the composite.
    traffic_score: Mapped[float | None] = mapped_column(nullable=True)
    engagement_score: Mapped[float | None] = mapped_column(nullable=True)
    new_visitor_score: Mapped[float | None] = mapped_column(nullable=True)
    content_performance_score: Mapped[float | None] = mapped_column(nullable=True)

    raw_signals: Mapped[dict] = mapped_column(JSONB, default=dict)
    measured_signal_pct: Mapped[float] = mapped_column(default=0.0)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PositioningRecommendation(Base):
    """One concrete, actionable recommendation derived from a ranking signal.

    Exactly one of link_id / store_score_id is set: link-scoped recommendations
    come from PublicationLinkPositioningScore, store-scoped ones from
    StorePositioningScore. (Both nullable in the DB; the services enforce it.)
    """
    __tablename__ = "positioning_recommendations"
    __table_args__ = (
        Index("idx_link_recommendation", "link_id"),
        Index("idx_business_recommendation", "business_id"),
        Index("idx_status_recommendation", "status"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True
    )
    link_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE"), nullable=True
    )
    store_score_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("store_positioning_scores.id", ondelete="SET NULL"),
        nullable=True,
    )
    score_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("publication_link_positioning_scores.id", ondelete="SET NULL"),
        nullable=True,
    )

    signal_key: Mapped[str] = mapped_column(String(100))  # e.g. "seller_claims_rate"
    severity: Mapped[str] = mapped_column(String(20))  # critical, warning, info
    message: Mapped[str] = mapped_column(Text)  # concrete, platform-specific text
    current_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="open")  # open, resolved, dismissed
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


POSITIONING_TABLES = [
    PublicationLinkPositioningScore.__table__,
    StorePositioningScore.__table__,
    PositioningRecommendation.__table__,
]
