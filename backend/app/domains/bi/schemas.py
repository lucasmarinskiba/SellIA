"""BI Schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FunnelMetricsResponse(BaseModel):
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
    conversion_lead_to_qualified: Decimal
    conversion_qualified_to_deal: Decimal
    conversion_deal_to_order: Decimal
    conversion_order_to_repeat: Decimal
    revenue_total: Decimal
    avg_order_value: Decimal
    created_at: datetime


class CohortMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    cohort_month: str
    cohort_size: int
    period_months: int
    active_customers: int
    revenue: Decimal
    retention_rate: Decimal
    created_at: datetime


class ChurnPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    conversation_id: UUID
    risk_level: str
    churn_probability: Decimal
    predicted_churn_date: datetime | None
    factors: list
    recommended_action: str | None
    model_version: str
    is_active: bool
    created_at: datetime


class LtvPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    conversation_id: UUID
    predicted_ltv: Decimal
    predicted_orders: int
    prediction_horizon_months: int
    confidence_score: Decimal
    factors: list
    model_version: str
    is_active: bool
    created_at: datetime


class InsightAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    insight_type: str
    severity: str
    title: str
    description: str | None
    metric_name: str | None
    metric_change_percent: Decimal | None
    recommended_action: str | None
    action_taken: bool
    action_result: str | None
    is_active: bool
    created_at: datetime
