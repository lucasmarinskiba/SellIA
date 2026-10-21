"""Financial Planner Agent Models"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class FinancialPlan(Base):
    """Plan financiero con proyecciones y escenarios."""
    __tablename__ = "financial_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_name = Column(String(255), nullable=False)
    revenue_projections = Column(JSONB, default=list, nullable=False)  # [{month, amount}, ...]
    expense_projections = Column(JSONB, default=list, nullable=False)  # [{month, amount}, ...]
    cash_flow = Column(JSONB, default=list, nullable=False)  # [{month, inflow, outflow, net}, ...]
    break_even_month = Column(Integer, nullable=True)
    scenarios = Column(JSONB, default=dict, nullable=False)  # {optimistic: {...}, base: {...}, pessimistic: {...}}
    metrics = Column(JSONB, default=dict, nullable=False)  # {ltv, cac, runway_months, ...}
    assumptions = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
