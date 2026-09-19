"""Models for publication link performance analytics."""

import uuid
from datetime import datetime, date
from uuid import UUID

from sqlalchemy import DateTime, String, ForeignKey, func, Float, Integer, Index, Date
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PublicationLinkMetrics(Base):
    """Daily/weekly performance metrics for a publication link."""
    __tablename__ = "publication_link_metrics"
    __table_args__ = (
        Index("idx_link_metrics", "link_id"),
        Index("idx_business_metrics", "business_id"),
        Index("idx_date_metrics", "metric_date"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    link_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE"))

    # Date of metrics (daily snapshot)
    metric_date: Mapped[date] = mapped_column(Date, index=True)

    # Platform performance
    platform_name: Mapped[str] = mapped_column(String(50))

    # Metrics
    impressions: Mapped[int] = mapped_column(default=0)  # How many times listing was viewed
    clicks: Mapped[int] = mapped_column(default=0)  # Click-throughs from listing
    conversions: Mapped[int] = mapped_column(default=0)  # Orders/purchases

    # Calculated rates
    ctr: Mapped[float] = mapped_column(default=0.0)  # clicks / impressions
    conversion_rate: Mapped[float] = mapped_column(default=0.0)  # conversions / clicks

    # Revenue (if available)
    revenue: Mapped[float] = mapped_column(default=0.0)  # Total revenue from this link this day

    # Provenance flags: True when the value above is an approximation, not a real
    # platform-reported number (e.g. Mercado Libre exposes no clicks endpoint to
    # sellers). Never trust a metric for scoring/CTR math without checking this.
    clicks_estimated: Mapped[bool] = mapped_column(default=False)
    conversions_estimated: Mapped[bool] = mapped_column(default=False)
    revenue_estimated: Mapped[bool] = mapped_column(default=False)

    # Metadata
    data_source: Mapped[str] = mapped_column(String(50))  # 'api', 'webhook', 'manual'
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PublicationLinkPerformanceSummary(Base):
    """Aggregated performance summary (all-time or period)."""
    __tablename__ = "publication_link_perf_summary"
    __table_args__ = (
        Index("idx_link_summary", "link_id"),
        Index("idx_business_summary", "business_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    link_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE"))

    # Period
    period_start: Mapped[date]
    period_end: Mapped[date]

    # Aggregated metrics
    total_impressions: Mapped[int] = mapped_column(default=0)
    total_clicks: Mapped[int] = mapped_column(default=0)
    total_conversions: Mapped[int] = mapped_column(default=0)
    total_revenue: Mapped[float] = mapped_column(default=0.0)

    # Avg rates
    avg_ctr: Mapped[float] = mapped_column(default=0.0)
    avg_conversion_rate: Mapped[float] = mapped_column(default=0.0)

    # Trend
    impressions_trend: Mapped[float | None] = mapped_column(nullable=True)  # % change from prior period
    conversions_trend: Mapped[float | None] = mapped_column(nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


ANALYTICS_TABLES = [
    PublicationLinkMetrics.__table__,
    PublicationLinkPerformanceSummary.__table__,
]
