"""Forecasting API schemas."""

from datetime import date, datetime
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
    key: str | None
    label: str | None
    is_active: bool
    intermittent: bool
    last_run_at: datetime | None
    last_wape: float | None
    last_mase: float | None


class RunRequest(BaseModel):
    horizon: int = Field(28, ge=7, le=180)
    reconcile: bool = True


class ForecastPointOut(BaseModel):
    date: date
    step: int
    yhat: float
    q10: float | None
    q50: float | None
    q90: float | None


class ForecastResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    series_key: str
    label: str | None = None
    level: str | None = None
    target: str | None = None
    origin_date: str | None = None
    run_at: str | None = None
    model_weights: dict = {}
    backtest: dict = {}
    reconciled: bool = False
    status: str | None = None
    points: list[ForecastPointOut] = []
