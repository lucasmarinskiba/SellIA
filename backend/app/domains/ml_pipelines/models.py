"""Phase 2: ML Pipelines - Predictive Models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base


class LeadScoringModel(Base):
    __tablename__ = "lead_scoring_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Raw features
    engagement_score = Column(Float, default=0)  # 0-100 based on email opens, clicks
    response_time_hours = Column(Float, default=0)  # avg time to respond
    email_opens = Column(Integer, default=0)
    email_clicks = Column(Integer, default=0)
    phone_calls = Column(Integer, default=0)
    demo_attended = Column(Boolean, default=False)
    website_visits = Column(Integer, default=0)
    pages_viewed = Column(Integer, default=0)
    time_on_site_minutes = Column(Float, default=0)

    # Predicted score (0-100)
    lead_score = Column(Float, default=0)
    confidence = Column(Float, default=0)  # 0-1
    tier = Column(String(20), default="cold")  # hot, warm, cold

    # Reasoning
    top_factors = Column(ARRAY(String), nullable=True)  # ["high_engagement", "demo_attended", ...]

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class ChurnPredictionModel(Base):
    __tablename__ = "churn_prediction_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Features
    days_since_last_purchase = Column(Integer, default=0)
    days_since_last_email = Column(Integer, default=0)
    purchase_frequency_per_month = Column(Float, default=0)
    avg_order_value = Column(Float, default=0)
    total_lifetime_value = Column(Float, default=0)
    support_tickets = Column(Integer, default=0)
    nps_score = Column(Integer, nullable=True)
    engagement_trend = Column(String(20), default="stable")  # increasing, stable, declining

    # Prediction
    churn_probability = Column(Float, default=0)  # 0-1
    churn_risk = Column(String(20), default="low")  # high, medium, low
    days_until_churn = Column(Integer, nullable=True)

    # Retention actions
    recommended_action = Column(String(100), nullable=True)  # "special_offer", "loyalty_program", "check_in"

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class CLVModel(Base):
    __tablename__ = "clv_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Historical data
    total_spent = Column(Float, default=0)
    total_orders = Column(Integer, default=0)
    avg_order_value = Column(Float, default=0)
    purchase_frequency_days = Column(Float, default=0)
    customer_lifespan_days = Column(Integer, default=0)
    repeat_rate = Column(Float, default=0)  # % of customers who buy again

    # CLV prediction (3-year window)
    predicted_clv_12m = Column(Float, default=0)  # next 12 months
    predicted_clv_36m = Column(Float, default=0)  # next 36 months
    clv_segment = Column(String(20), default="standard")  # vip, standard, at_risk

    # Propensity models
    upsell_propensity = Column(Float, default=0)  # 0-1: likelihood to buy higher tier
    crosssell_propensity = Column(Float, default=0)  # 0-1: likelihood to buy complementary
    expansion_propensity = Column(Float, default=0)  # 0-1: likelihood to increase spend

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class ChannelRoutingModel(Base):
    __tablename__ = "channel_routing_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Channel affinity (0-1, sum = 1)
    email_affinity = Column(Float, default=0.3)
    sms_affinity = Column(Float, default=0.2)
    whatsapp_affinity = Column(Float, default=0.2)
    phone_affinity = Column(Float, default=0.15)
    in_app_affinity = Column(Float, default=0.15)

    # Recommended channel
    primary_channel = Column(String(20), default="email")  # email, sms, whatsapp, phone, in_app
    secondary_channel = Column(String(20), nullable=True)

    # Response metrics per channel
    email_response_rate = Column(Float, default=0)
    sms_response_rate = Column(Float, default=0)
    whatsapp_response_rate = Column(Float, default=0)
    phone_response_rate = Column(Float, default=0)

    # Optimal send times (by channel)
    email_optimal_hour = Column(Integer, nullable=True)  # 0-23
    sms_optimal_hour = Column(Integer, nullable=True)
    whatsapp_optimal_hour = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
