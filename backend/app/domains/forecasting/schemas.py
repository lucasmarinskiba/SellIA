"""Forecasting API schemas."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeriesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    series_key: str
    level: str
    target: str
    grain: str
    key: Optional[str]
    label: Optional[str]
    is_active: bool
    intermittent: bool
    last_run_at: Optional[datetime]
    last_wape: Optional[float]
    last_mase: Optional[float]


class RunRequest(BaseModel):
    horizon: int = Field(28, ge=7, le=180)
    reconcile: bool = True


class ForecastPointOut(BaseModel):
    date: date
    step: int
    yhat: float
    q10: Optional[float]
    q50: Optional[float]
    q90: Optional[float]


class ForecastResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    series_key: str
    label: Optional[str] = None
    level: Optional[str] = None
    target: Optional[str] = None
    origin_date: Optional[str] = None
    run_at: Optional[str] = None
    model_weights: dict = {}
    backtest: dict = {}
    reconciled: bool = False
    status: Optional[str] = None
    points: list[ForecastPointOut] = []
