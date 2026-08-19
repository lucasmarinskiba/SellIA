import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Float, Numeric, Text, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship

from app.core.database import Base


class EventType(str, Enum):
    PAGE_VIEW = "page_view"
    CONVERSION = "conversion"
    FORM_SUBMIT = "form_submit"
    BUTTON_CLICK = "button_click"
    SCROLL = "scroll"
    TIME_ON_PAGE = "time_on_page"


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    event_name = Column(String(255), nullable=True)

    page_url = Column(String(500), nullable=False, index=True)
    page_title = Column(String(255), nullable=True)

    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True)

    user_agent = Column(String(500), nullable=True)
    ip_address = Column(INET, nullable=True)
    country_code = Column(String(2), nullable=True)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)

    event_metadata = Column("metadata", JSONB, default=dict, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    scroll_depth = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    website = relationship("Website", foreign_keys=[website_id])

    __table_args__ = (
        Index('idx_analytics_website_date', 'website_id', 'created_at'),
        Index('idx_analytics_event_date', 'event_type', 'created_at'),
    )


class Conversion(Base):
    __tablename__ = "conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)

    conversion_type = Column(String(100), nullable=False)
    conversion_value = Column(Float, nullable=True)

    session_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)

    source_page = Column(String(500), nullable=True)

    event_metadata = Column("metadata", JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    website = relationship("Website", foreign_keys=[website_id])

    __table_args__ = (
        Index('idx_conversion_website_date', 'website_id', 'created_at'),
    )


# ============================================================
# BI (Business Intelligence) models — used by app.domains.bi.
#
# Re-exported from here (rather than defined directly in bi/models.py) per
# that module's own docstring: "re-exported from analytics to avoid
# duplication". Field shapes match app.domains.bi.schemas response models
# 1:1 (each schema has model_config = ConfigDict(from_attributes=True)).
# ============================================================

class FunnelMetric(Base):
    __tablename__ = "funnel_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    period = Column(String(50), nullable=False)
    period_type = Column(String(20), nullable=False, default="monthly")

    leads_count = Column(Integer, default=0, nullable=False)
    qualified_count = Column(Integer, default=0, nullable=False)
    deals_count = Column(Integer, default=0, nullable=False)
    orders_count = Column(Integer, default=0, nullable=False)
    repeat_orders_count = Column(Integer, default=0, nullable=False)

    conversion_lead_to_qualified = Column(Numeric(6, 4), default=0, nullable=False)
    conversion_qualified_to_deal = Column(Numeric(6, 4), default=0, nullable=False)
    conversion_deal_to_order = Column(Numeric(6, 4), default=0, nullable=False)
    conversion_order_to_repeat = Column(Numeric(6, 4), default=0, nullable=False)

    revenue_total = Column(Numeric(14, 2), default=0, nullable=False)
    avg_order_value = Column(Numeric(14, 2), default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index('idx_funnel_metrics_business_created', 'business_id', 'created_at'),
    )


class CohortMetric(Base):
    __tablename__ = "cohort_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    cohort_month = Column(String(7), nullable=False)  # "YYYY-MM"
    cohort_size = Column(Integer, default=0, nullable=False)
    period_months = Column(Integer, default=0, nullable=False)
    active_customers = Column(Integer, default=0, nullable=False)
    revenue = Column(Numeric(14, 2), default=0, nullable=False)
    retention_rate = Column(Numeric(6, 4), default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index('idx_cohort_metrics_business_month', 'business_id', 'cohort_month'),
    )


class ChurnPrediction(Base):
    __tablename__ = "bi_churn_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    risk_level = Column(String(20), nullable=False, default="low")  # low/medium/high
    churn_probability = Column(Numeric(6, 4), default=0, nullable=False)
    predicted_churn_date = Column(DateTime(timezone=True), nullable=True)
    factors = Column(JSONB, default=list, nullable=False)
    recommended_action = Column(Text, nullable=True)
    model_version = Column(String(50), nullable=False, default="v1")
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class LtvPrediction(Base):
    __tablename__ = "ltv_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    predicted_ltv = Column(Numeric(14, 2), default=0, nullable=False)
    predicted_orders = Column(Integer, default=0, nullable=False)
    prediction_horizon_months = Column(Integer, default=12, nullable=False)
    confidence_score = Column(Numeric(6, 4), default=0, nullable=False)
    factors = Column(JSONB, default=list, nullable=False)
    model_version = Column(String(50), nullable=False, default="v1")
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class InsightAlert(Base):
    __tablename__ = "insight_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    insight_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="info")  # info/warning/critical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    metric_name = Column(String(100), nullable=True)
    metric_change_percent = Column(Numeric(8, 4), nullable=True)
    recommended_action = Column(Text, nullable=True)
    action_taken = Column(Boolean, default=False, nullable=False)
    action_result = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index('idx_insight_alerts_business_active', 'business_id', 'is_active'),
    )
