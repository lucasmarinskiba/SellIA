"""Fraud detection API — order + account fraud scoring."""

from uuid import UUID
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.fraud.fraud_service import FraudDetectionService

router = APIRouter(prefix="/api/v1", tags=["fraud-detection"])


class ScoreOrderFraudRequest(BaseModel):
    order_id: str
    customer_id: UUID
    order_value: Decimal
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None


class ScoreAccountFraudRequest(BaseModel):
    customer_id: UUID


class AddBlacklistRequest(BaseModel):
    entity_type: str  # email, ip, card_token, phone
    entity_value: str
    fraud_reason: Optional[str] = None


@router.post("/businesses/{business_id}/score-order-fraud")
def score_order_fraud(
    business_id: UUID,
    request: ScoreOrderFraudRequest,
    db: Session = Depends(get_db)
):
    """Score fraud risk for order."""
    return FraudDetectionService.score_order_fraud(
        business_id=business_id,
        order_id=request.order_id,
        customer_id=request.customer_id,
        order_value=request.order_value,
        ip_address=request.ip_address,
        device_fingerprint=request.device_fingerprint,
        billing_address=request.billing_address,
        shipping_address=request.shipping_address,
        db=db
    )


@router.post("/businesses/{business_id}/score-account-fraud")
def score_account_fraud(
    business_id: UUID,
    request: ScoreAccountFraudRequest,
    db: Session = Depends(get_db)
):
    """Score fraud risk for customer account."""
    return FraudDetectionService.score_account_fraud(
        business_id=business_id,
        customer_id=request.customer_id,
        db=db
    )


@router.post("/businesses/{business_id}/blacklist")
def add_to_blacklist(
    business_id: UUID,
    request: AddBlacklistRequest,
    db: Session = Depends(get_db)
):
    """Add entity to fraud blacklist."""
    return FraudDetectionService.add_to_blacklist(
        business_id=business_id,
        entity_type=request.entity_type,
        entity_value=request.entity_value,
        fraud_reason=request.fraud_reason,
        db=db
    )


@router.get("/businesses/{business_id}/fraud-summary")
def get_fraud_summary(
    business_id: UUID,
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Get fraud detection summary."""
    return FraudDetectionService.get_fraud_summary(
        business_id=business_id,
        date=date,
        db=db
    )
