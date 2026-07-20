"""Financial Planner Schemas"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FinancialScenario(BaseModel):
    name: str  # optimistic | base | pessimistic
    monthly_data: List[Dict[str, Any]] = []
    total_revenue: Optional[float] = None
    total_expense: Optional[float] = None
    net_result: Optional[float] = None


class FinancialPlanBase(BaseModel):
    plan_name: str


class FinancialPlanCreate(FinancialPlanBase):
    historical_data: Dict[str, Any] = {}  # {revenues: [...], expenses: [...]}
    assumptions: Dict[str, Any] = {}  # {growth_rate, cac, ltv, churn, ...}


class FinancialPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    plan_name: str
    revenue_projections: List[Dict[str, Any]] = []
    expense_projections: List[Dict[str, Any]] = []
    cash_flow: List[Dict[str, Any]] = []
    break_even_month: Optional[int] = None
    scenarios: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    assumptions: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class FinancialPlanExportOut(BaseModel):
    plan_id: UUID
    format: str
    content: str
    filename: str
