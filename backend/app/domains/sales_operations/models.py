"""Phase 43: Sales Operations Intelligence - Department Management."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class SalesTeamPerformance(Base):
    __tablename__ = "sales_team_performance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sales_quota = Column(Float, default=0)
    sales_actual = Column(Float, default=0)
    quota_attainment = Column(Float, default=0)
    win_rate = Column(Float, default=0)
    average_deal_size = Column(Float, default=0)
    sales_cycle_days = Column(Integer, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class PipelineHealth(Base):
    __tablename__ = "pipeline_health"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    total_opportunities = Column(Integer, default=0)
    pipeline_value = Column(Float, default=0)
    forecasted_revenue = Column(Float, default=0)
    stage_distribution = Column(JSONB, nullable=True)
    days_sales_outstanding = Column(Integer, default=0)
    pipeline_coverage_ratio = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class SalesProcess(Base):
    __tablename__ = "sales_process"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    process_name = Column(String(255), nullable=False)
    stage_sequence = Column(JSONB, nullable=True)
    avg_duration = Column(Integer, default=0)
    win_rate_by_stage = Column(JSONB, nullable=True)
    bottleneck_stage = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class CompetitiveWinLoss(Base):
    __tablename__ = "competitive_win_loss"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    competitor_name = Column(String(255), nullable=True)
    outcome = Column(String(20), nullable=False)  # won, lost
    loss_reason = Column(Text, nullable=True)
    win_reason = Column(Text, nullable=True)
    competitive_factors = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class SalesEnablement(Base):
    __tablename__ = "sales_enablement"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    training_topic = Column(String(255), nullable=False)
    training_completed = Column(Boolean, default=False)
    competency_score = Column(Float, default=0)
    recommended_resources = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class SalesForecasting(Base):
    __tablename__ = "sales_forecasting"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    forecast_period = Column(String(50), nullable=False)  # monthly, quarterly, yearly
    forecasted_revenue = Column(Float, default=0)
    confidence_level = Column(Float, default=0)
    contributing_deals = Column(JSONB, nullable=True)
    vs_quota = Column(Float, default=0)
    scenario = Column(String(50), default="base")  # base, upside, downside
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class SalesOperationsMetrics(Base):
    __tablename__ = "sales_operations_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    team_size = Column(Integer, default=0)
    total_headcount = Column(Integer, default=0)
    revenue_per_rep = Column(Float, default=0)
    sales_cycle_length_days = Column(Integer, default=0)
    average_contract_value = Column(Float, default=0)
    customer_acquisition_cost = Column(Float, default=0)
    customer_lifetime_value = Column(Float, default=0)
    churn_rate = Column(Float, default=0)
    gross_retention_rate = Column(Float, default=0)
    net_retention_rate = Column(Float, default=0)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
