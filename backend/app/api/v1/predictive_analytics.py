"""Predictive analytics API — demand + churn + revenue forecasting."""

from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.predictive.predictive_service import PredictiveAnalyticsService

router = APIRouter(prefix="/api/v1", tags=["predictive-analytics"])


class PredictChurnRequest(BaseModel):
    customer_id: UUID
    days_since_purchase: int
    purchase_frequency: Decimal
    engagement_score: Optional[Decimal] = None


class PredictPurchaseTimingRequest(BaseModel):
    customer_id: UUID
    avg_purchase_interval: int
    last_purchase_date: str  # YYYY-MM-DD


class ForecastDemandRequest(BaseModel):
    product_category: str
    historical_units: List[int]
    forecast_days: int = 30


class ForecastRevenueRequest(BaseModel):
    historical_revenue: List[float]
    new_customer_ratio: Optional[Decimal] = Decimal("0.3")
    forecast_horizon: str = "next_30_days"


class EvaluateAccuracyRequest(BaseModel):
    prediction_type: str
    predictions: List[float]
    actuals: List[float]


@router.post("/businesses/{business_id}/predict-churn")
def predict_churn(
    business_id: UUID,
    request: PredictChurnRequest,
    db: Session = Depends(get_db)
):
    """Predict customer churn probability."""
    return PredictiveAnalyticsService.predict_churn(
        business_id=business_id,
        customer_id=request.customer_id,
        days_since_purchase=request.days_since_purchase,
        purchase_frequency=request.purchase_frequency,
        engagement_score=request.engagement_score or Decimal("5"),
        db=db
    )


@router.post("/businesses/{business_id}/predict-purchase-timing")
def predict_purchase_timing(
    business_id: UUID,
    request: PredictPurchaseTimingRequest,
    db: Session = Depends(get_db)
):
    """Predict next purchase timing."""
    last_purchase = datetime.fromisoformat(f"{request.last_purchase_date}T00:00:00+00:00")
    return PredictiveAnalyticsService.predict_purchase_timing(
        business_id=business_id,
        customer_id=request.customer_id,
        avg_purchase_interval=request.avg_purchase_interval,
        last_purchase_date=last_purchase,
        db=db
    )


@router.post("/businesses/{business_id}/forecast-demand")
def forecast_demand(
    business_id: UUID,
    request: ForecastDemandRequest,
    db: Session = Depends(get_db)
):
    """Forecast product demand."""
    return PredictiveAnalyticsService.forecast_demand(
        business_id=business_id,
        product_category=request.product_category,
        historical_units=request.historical_units,
        forecast_days=request.forecast_days,
        db=db
    )


@router.post("/businesses/{business_id}/forecast-revenue")
def forecast_revenue(
    business_id: UUID,
    request: ForecastRevenueRequest,
    db: Session = Depends(get_db)
):
    """Forecast business revenue."""
    return PredictiveAnalyticsService.forecast_revenue(
        business_id=business_id,
        historical_revenue=request.historical_revenue,
        new_customer_ratio=request.new_customer_ratio,
        forecast_horizon=request.forecast_horizon,
        db=db
    )


@router.post("/businesses/{business_id}/evaluate-accuracy")
def evaluate_accuracy(
    business_id: UUID,
    request: EvaluateAccuracyRequest,
    db: Session = Depends(get_db)
):
    """Evaluate prediction model accuracy."""
    return PredictiveAnalyticsService.evaluate_prediction_accuracy(
        business_id=business_id,
        prediction_type=request.prediction_type,
        predictions=request.predictions,
        actuals=request.actuals,
        db=db
    )
