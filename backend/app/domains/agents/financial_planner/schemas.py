"""Financial Planner Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FinancialScenario(BaseModel):
    name: str  # optimistic | base | pessimistic
    monthly_data: list[dict[str, Any]] = []
    total_revenue: float | None = None
    total_expense: float | None = None
    net_result: float | None = None


class FinancialPlanBase(BaseModel):
    plan_name: str


class FinancialPlanCreate(FinancialPlanBase):
    historical_data: dict[str, Any] = {}  # {revenues: [...], expenses: [...]}
    assumptions: dict[str, Any] = {}  # {growth_rate, cac, ltv, churn, ...}


class FinancialPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    plan_name: str
    revenue_projections: list[dict[str, Any]] = []
    expense_projections: list[dict[str, Any]] = []
    cash_flow: list[dict[str, Any]] = []
    break_even_month: int | None = None
    scenarios: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    assumptions: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class FinancialPlanExportOut(BaseModel):
    plan_id: UUID
    format: str
    content: str
    filename: str
