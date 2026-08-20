"""Phase 42: Accounting Intelligence - Financial Operations."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class TransactionType(str, Enum):
    REVENUE = "revenue"
    EXPENSE = "expense"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"

class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Float, default=0)
    currency = Column(String(10), default="USD")
    reference_id = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    transaction_date = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class RevenueRecognition(Base):
    __tablename__ = "revenue_recognition"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contract_value = Column(Float, default=0)
    recognition_schedule = Column(JSONB, nullable=True)
    recognized_amount = Column(Float, default=0)
    recognition_date = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class CostAnalysis(Base):
    __tablename__ = "cost_analysis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    cost_category = Column(String(100), nullable=False)  # cogs, opex, marketing, sales, etc
    total_cost = Column(Float, default=0)
    cost_per_unit = Column(Float, default=0)
    cost_breakdown = Column(JSONB, nullable=True)
    efficiency_score = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ProfitMarginAnalysis(Base):
    __tablename__ = "profit_margin_analysis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    gross_margin = Column(Float, default=0)
    net_margin = Column(Float, default=0)
    margin_trend = Column(JSONB, nullable=True)  # historical trend
    optimization_opportunity = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class CashFlowForecast(Base):
    __tablename__ = "cash_flow_forecast"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    forecast_period = Column(String(50), nullable=False)  # monthly, quarterly, yearly
    inflow_forecast = Column(Float, default=0)
    outflow_forecast = Column(Float, default=0)
    net_cash_forecast = Column(Float, default=0)
    confidence_level = Column(Float, default=0)
    scenario = Column(String(50), default="base")  # base, optimistic, pessimistic
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class BudgetAllocation(Base):
    __tablename__ = "budget_allocation"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    department = Column(String(100), nullable=False)  # sales, marketing, ops, etc
    budget_amount = Column(Float, default=0)
    spent_amount = Column(Float, default=0)
    roi_target = Column(Float, default=0)
    roi_actual = Column(Float, default=0)
    allocation_date = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class FinancialMetrics(Base):
    __tablename__ = "financial_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_revenue = Column(Float, default=0)
    total_expense = Column(Float, default=0)
    net_profit = Column(Float, default=0)
    profit_margin = Column(Float, default=0)
    cash_position = Column(Float, default=0)
    accounts_receivable = Column(Float, default=0)
    accounts_payable = Column(Float, default=0)
    debt_to_equity = Column(Float, default=0)
    burn_rate = Column(Float, default=0)
    runway_months = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
