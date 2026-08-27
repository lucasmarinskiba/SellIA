"""Cash-flow API schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CashFlowPointOut(BaseModel):
    date: date
    revenue_forecast: Decimal = Field(decimal_places=2)
    cogs_forecast: Decimal = Field(decimal_places=2)
    opex: Decimal = Field(decimal_places=2)
    tax_provision: Decimal = Field(decimal_places=2)
    inflow_from_prior_sales: Decimal = Field(decimal_places=2)
    operating_cash_flow: Decimal = Field(decimal_places=2)
    net_cash_flow: Decimal = Field(decimal_places=2)
    cumulative_balance: Decimal = Field(decimal_places=2)
    confidence_q10: Decimal = Field(decimal_places=2)
    confidence_q90: Decimal = Field(decimal_places=2)


class CashFlowForecastOut(BaseModel):
    business_id: str
    start_date: date
    horizon_days: int
    beginning_balance: Decimal = Field(decimal_places=2)
    end_balance: Decimal = Field(decimal_places=2)
    min_balance: Decimal = Field(decimal_places=2)
    max_balance: Decimal = Field(decimal_places=2)
    min_balance_date: date
    runway_days: Optional[int] = None
    assumptions: dict = {}
    computed_at: datetime
    points: list[CashFlowPointOut]


class CashFlowRequest(BaseModel):
    horizon_days: int = Field(90, ge=30, le=365)
    payment_delay_days: int = Field(3, ge=0, le=30)
    cogs_pct: Decimal = Field(Decimal("0.35"), ge=0, le=1)
    opex_daily: Decimal = Field(Decimal("500.00"), ge=0)
    tax_rate: Decimal = Field(Decimal("0.21"), ge=0, le=1)
