"""Payment API endpoints."""

from uuid import UUID
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.payments.payment_service import PaymentService

router = APIRouter(prefix="/api/v1", tags=["payments"])


class CreateTransactionRequest(BaseModel):
    amount: Decimal
    currency: str = "USD"
    method: str
    customer_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    description: Optional[str] = None
    reference_id: Optional[str] = None


class CreateCheckoutRequest(BaseModel):
    customer_email: str
    customer_name: str
    items: list
    amount: Decimal
    currency: str = "USD"
    order_id: Optional[UUID] = None


class ProcessWebhookRequest(BaseModel):
    type: str
    data: dict


class CreateRefundRequest(BaseModel):
    transaction_id: UUID
    amount: Decimal
    reason: str


class ReconcileTransactionRequest(BaseModel):
    order_id: UUID
    transaction_id: Optional[UUID] = None


@router.post("/businesses/{business_id}/transactions")
def create_transaction(
    business_id: UUID,
    request: CreateTransactionRequest,
    db: Session = Depends(get_db)
):
    """Create payment transaction."""
    return PaymentService.create_transaction(
        business_id=business_id,
        amount=request.amount,
        currency=request.currency,
        method=request.method,
        customer_id=request.customer_id,
        order_id=request.order_id,
        location_id=request.location_id,
        description=request.description,
        reference_id=request.reference_id,
        db=db
    )


@router.post("/businesses/{business_id}/checkout/mercadopago")
def create_mercadopago_checkout(
    business_id: UUID,
    request: CreateCheckoutRequest,
    db: Session = Depends(get_db)
):
    """Create MercadoPago checkout."""
    return PaymentService.create_mercadopago_checkout(
        business_id=business_id,
        customer_email=request.customer_email,
        customer_name=request.customer_name,
        items=request.items,
        amount=request.amount,
        currency=request.currency,
        order_id=request.order_id,
        db=db
    )


@router.post("/businesses/{business_id}/webhooks/mercadopago")
def handle_mercadopago_webhook(
    business_id: UUID,
    request: ProcessWebhookRequest,
    db: Session = Depends(get_db)
):
    """Handle MercadoPago webhook notification."""
    return PaymentService.process_mercadopago_webhook(
        business_id=business_id,
        event_data=request.dict(),
        db=db
    )


@router.post("/businesses/{business_id}/refunds")
def create_refund(
    business_id: UUID,
    request: CreateRefundRequest,
    db: Session = Depends(get_db)
):
    """Create refund request."""
    return PaymentService.create_refund(
        transaction_id=request.transaction_id,
        business_id=business_id,
        amount=request.amount,
        reason=request.reason,
        db=db
    )


@router.post("/businesses/{business_id}/reconcile")
def reconcile_transaction(
    business_id: UUID,
    request: ReconcileTransactionRequest,
    db: Session = Depends(get_db)
):
    """Reconcile order with payment transaction."""
    return PaymentService.reconcile_transaction(
        order_id=request.order_id,
        transaction_id=request.transaction_id,
        business_id=business_id,
        db=db
    )


@router.get("/businesses/{business_id}/transactions")
def get_transactions(
    business_id: UUID,
    status: Optional[str] = Query(None),
    location_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get transactions."""
    return PaymentService.get_transactions(
        business_id=business_id,
        status=status,
        location_id=location_id,
        limit=limit,
        db=db
    )


@router.get("/businesses/{business_id}/settlements/metrics")
def get_settlement_metrics(
    business_id: UUID,
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get settlement metrics."""
    return PaymentService.get_settlement_metrics(
        business_id=business_id,
        period_days=period_days,
        db=db
    )


@router.get("/businesses/{business_id}/payments/metrics")
def get_payment_metrics(
    business_id: UUID,
    db: Session = Depends(get_db)
):
    """Get payment metrics."""
    return PaymentService.get_payment_metrics(
        business_id=business_id,
        db=db
    )
