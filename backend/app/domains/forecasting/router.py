"""Demand-forecasting API — /api/v1/businesses/{business_id}/forecasting/*"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.forecasting.schemas import (
    ForecastResponse,
    RunRequest,
    SeriesResponse,
)
from app.domains.forecasting.service import ForecastingService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/forecasting", tags=["Demand Forecasting"])


@router.post("/sync")
async def sync_series(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ForecastingService(db).sync_series(business_id)


@router.get("/series", response_model=list[SeriesResponse])
async def list_series(
    business_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ForecastingService(db).list_series(business_id, active_only=active_only)


@router.post("/run")
async def run_all(
    business_id: UUID,
    body: RunRequest = RunRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ForecastingService(db).run_all(
        business_id, horizon=body.horizon, reconcile=body.reconcile
    )


@router.post("/series/{series_id}/run")
async def run_one(
    business_id: UUID,
    series_id: UUID,
    horizon: int = Query(28, ge=7, le=180),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ForecastingService(db)
    rows = await svc.list_series(business_id, active_only=False)
    row = next((r for r in rows if r.id == series_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="series not found")
    return await svc.run_series(business_id, row, horizon=horizon)


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    business_id: UUID,
    series_key: str = Query(..., description="e.g. total:revenue:daily:*"),
    horizon: int | None = Query(None, ge=1, le=180),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await ForecastingService(db).get_forecast(business_id, series_key, horizon)
    if res is None:
        raise HTTPException(status_code=404, detail="series not found")
    return res


@router.post("/evaluate-accuracy")
async def evaluate_accuracy(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ForecastingService(db).evaluate_accuracy(business_id)


@router.get("/dashboard")
async def dashboard(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ForecastingService(db).dashboard(business_id)
