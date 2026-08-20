"""Attribution API."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domains.attribution.attribution_service import AttributionService

router = APIRouter(prefix="/api/v1", tags=["attribution"])


class LogTouchpointRequest(BaseModel):
    channel: str
    source: Optional[str] = None
    interaction_type: str


class AttributeRevenueRequest(BaseModel):
    order_id: UUID
    order_value: float
    attribution_model: str


@router.post("/customers/{customer_id}/touchpoints")
def log_touchpoint(customer_id: UUID, business_id: UUID, request: LogTouchpointRequest, db: Session = Depends(get_db)):
    return AttributionService.log_touchpoint(business_id, customer_id, request.channel, request.source or "", request.interaction_type, db)


@router.post("/businesses/{business_id}/attribute-revenue")
def attribute_revenue(business_id: UUID, request: AttributeRevenueRequest, db: Session = Depends(get_db)):
    return AttributionService.attribute_revenue(request.order_id, business_id, request.order_value, request.attribution_model, db)


@router.get("/businesses/{business_id}/channel-performance")
def get_channel_performance(business_id: UUID, days: int = Query(30), db: Session = Depends(get_db)):
    return AttributionService.get_channel_performance(business_id, days, db)


@router.get("/businesses/{business_id}/attribution/metrics")
def get_metrics(business_id: UUID, db: Session = Depends(get_db)):
    return AttributionService.get_metrics(business_id, db)
