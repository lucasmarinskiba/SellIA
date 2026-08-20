"""Unified analytics dashboard — consolidated metrics across all locations."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Decimal, Enum as SQLEnum, Index, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class DashboardPeriod(str, Enum):
    """Time period for dashboard metrics."""
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class UnifiedLocationMetric(Base):
    """Consolidated daily metrics per location."""
    __tablename__ = "unified_location_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Date
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Foot traffic
    total_visitors = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    avg_dwell_minutes = Column(Integer, default=0)
    peak_hour = Column(Integer, nullable=True)  # 0-23

    # Staff
    staff_on_shift = Column(Integer, default=0)
    tasks_assigned = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    task_completion_rate = Column(Decimal(5, 2), default=0)  # %

    # Inventory
    stock_outs = Column(Integer, default=0)
    low_stock_alerts = Column(Integer, default=0)
    demo_units_used = Column(Integer, default=0)

    # Feedback
    nps_avg = Column(Decimal(3, 1), default=0)
    nps_detractors = Column(Integer, default=0)
    sentiment_positive_pct = Column(Decimal(5, 2), default=0)
    sentiment_negative_pct = Column(Decimal(5, 2), default=0)

    # Revenue
    base_revenue = Column(Decimal(12, 2), default=0)
    final_revenue = Column(Decimal(12, 2), default=0)
    total_discounts = Column(Decimal(12, 2), default=0)
    revenue_per_visitor = Column(Decimal(8, 2), default=0)

    # Pricing
    peak_hour_discounts_applied = Column(Integer, default=0)
    discount_codes_used = Column(Integer, default=0)
    ab_test_conversions = Column(Integer, default=0)

    # Orders linked to visits
    online_orders_from_visits = Column(Integer, default=0)
    attributed_revenue = Column(Decimal(12, 2), default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_date", "location_id", "date"),
        Index("idx_business_date", "business_id", "date"),
    )


class BusinessDashboardSummary(Base):
    """High-level business metrics across all locations."""
    __tablename__ = "business_dashboard_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Period
    date = Column(String(10), nullable=False)  # YYYY-MM-DD (latest update)

    # Aggregate metrics
    total_locations = Column(Integer, default=0)
    active_locations = Column(Integer, default=0)

    # Visitors & traffic
    total_visitors_month = Column(Integer, default=0)
    unique_visitors_month = Column(Integer, default=0)
    avg_visitors_per_location = Column(Decimal(8, 1), default=0)
    traffic_trend = Column(String(20), default="stable")  # improving, stable, declining

    # Staff performance
    avg_task_completion_rate = Column(Decimal(5, 2), default=0)
    avg_nps_by_location = Column(Decimal(3, 1), default=0)

    # Revenue
    total_revenue_month = Column(Decimal(12, 2), default=0)
    attributed_revenue_month = Column(Decimal(12, 2), default=0)
    attribution_rate = Column(Decimal(5, 2), default=0)  # attributed / total %
    revenue_per_location = Column(Decimal(10, 2), default=0)

    # Pricing performance
    avg_discount_rate = Column(Decimal(5, 2), default=0)
    ab_test_winning_variants = Column(Integer, default=0)

    # Inventory
    avg_inventory_turnover = Column(Decimal(5, 2), default=0)
    total_stock_outs = Column(Integer, default=0)

    # Health score (0-100)
    overall_health_score = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_date", "business_id", "date"),
    )


class LocationComparison(Base):
    """Compare metrics across locations (benchmark + outliers)."""
    __tablename__ = "location_comparison"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Period
    date = Column(String(10), nullable=False)

    # Ranking
    location_id_best_visitors = Column(UUID(as_uuid=True), nullable=True)
    location_id_best_revenue = Column(UUID(as_uuid=True), nullable=True)
    location_id_best_nps = Column(UUID(as_uuid=True), nullable=True)
    location_id_best_conversion = Column(UUID(as_uuid=True), nullable=True)

    # Outliers (need attention)
    location_id_lowest_visitors = Column(UUID(as_uuid=True), nullable=True)
    location_id_lowest_revenue = Column(UUID(as_uuid=True), nullable=True)
    location_id_lowest_nps = Column(UUID(as_uuid=True), nullable=True)

    # Variance
    visitor_variance_pct = Column(Decimal(5, 2), default=0)
    revenue_variance_pct = Column(Decimal(5, 2), default=0)
    nps_variance = Column(Decimal(3, 1), default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_comparison", "business_id", "date"),
    )


class FunnelStageMetric(Base):
    """Track conversion through each stage of funnel."""
    __tablename__ = "funnel_stage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Date
    date = Column(String(10), nullable=False)

    # Funnel stages
    online_leads = Column(Integer, default=0)
    proximity_invites_sent = Column(Integer, default=0)
    proximity_invites_opened = Column(Integer, default=0)
    location_visits = Column(Integer, default=0)
    visitor_feedback_submitted = Column(Integer, default=0)
    online_orders_placed = Column(Integer, default=0)
    repeat_purchases = Column(Integer, default=0)

    # Conversion rates
    lead_to_visit_rate = Column(Decimal(5, 2), default=0)
    visit_to_order_rate = Column(Decimal(5, 2), default=0)
    order_to_repeat_rate = Column(Decimal(5, 2), default=0)
    overall_funnel_rate = Column(Decimal(5, 2), default=0)

    # Time metrics
    avg_days_lead_to_visit = Column(Integer, nullable=True)
    avg_days_visit_to_order = Column(Integer, nullable=True)
    avg_days_order_to_repeat = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_funnel", "location_id", "date"),
    )
