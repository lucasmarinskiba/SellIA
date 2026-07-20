"""Analytics & BI Pydantic Schemas."""

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any


class FunnelMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    period: str
    period_type: str
    leads_count: int
    qualified_count: int
    deals_count: int
    orders_count: int
    repeat_orders_count: int
    conversion_lead_to_qualified: float
    conversion_qualified_to_deal: float
    conversion_deal_to_order: float
    conversion_order_to_repeat: float
    revenue_total: float
    avg_order_value: float
    created_at: datetime
    custom_stages: Optional[list[dict[str, Any]]] = None


class ChurnPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    conversation_id: UUID
    risk_level: str
    churn_probability: float
    predicted_churn_date: Optional[datetime] = None
    factors: list[str]
    recommended_action: Optional[str] = None
    created_at: datetime


class LtvPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    conversation_id: UUID
    predicted_ltv: float
    predicted_orders: int
    prediction_horizon_months: int
    confidence_score: float
    factors: list[str]
    created_at: datetime


class InsightAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    insight_type: str
    severity: str
    title: str
    description: Optional[str] = None
    metric_name: Optional[str] = None
    metric_change_percent: Optional[float] = None
    recommended_action: Optional[str] = None
    action_taken: bool
    created_at: datetime


class DashboardSummaryResponse(BaseModel):
    business_id: UUID
    period: str
    revenue_total: float
    orders_count: int
    leads_count: int
    conversion_rate: float
    nps_score: int
    at_risk_customers: int
    avg_ltv: float
    top_segment: str
    insights_today: int
    kpis: Optional[list[dict[str, Any]]] = None
