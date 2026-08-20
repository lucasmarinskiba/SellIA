"""Predictive modeling API."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domains.predictive.predictive_service import PredictiveService

router = APIRouter(prefix="/api/v1", tags=["predictive"])


class LeadScoreRequest(BaseModel):
    rfm_score: float = 0
    engagement: float = 0
    frequency: float = 0


class ChurnRiskRequest(BaseModel):
    days_since_purchase: int = 0
    engagement: float = 0
    frequency: float = 0


class CreateSegmentRequest(BaseModel):
    name: str
    rules: dict
    segmentation_type: str


@router.post("/customers/{customer_id}/lead-score")
def calculate_lead_score(customer_id: UUID, business_id: UUID, request: LeadScoreRequest, db: Session = Depends(get_db)):
    return PredictiveService.calculate_lead_score(customer_id, business_id, request.rfm_score, request.engagement, request.frequency, db)


@router.post("/customers/{customer_id}/churn-risk")
def calculate_churn_risk(customer_id: UUID, business_id: UUID, request: ChurnRiskRequest, db: Session = Depends(get_db)):
    return PredictiveService.calculate_churn_risk(customer_id, business_id, request.days_since_purchase, request.engagement, request.frequency, db)


@router.post("/businesses/{business_id}/segments")
def create_segment(business_id: UUID, request: CreateSegmentRequest, db: Session = Depends(get_db)):
    return PredictiveService.create_segment(business_id, request.name, request.rules, request.segmentation_type, db)


@router.get("/businesses/{business_id}/predictive/metrics")
def get_metrics(business_id: UUID, db: Session = Depends(get_db)):
    return PredictiveService.get_metrics(business_id, db)
