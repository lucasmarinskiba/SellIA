"""Payment API endpoints."""

from uuid import UUID
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

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
    conversation_id: Optional[UUID] = None
    description: Optional[str] = None
    reference_id: Optional[str] = None


class CreateCheckoutRequest(BaseModel):
    customer_email: str
    customer_name: str
    items: list
    amount: Decimal
    currency: str = "USD"
    order_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None


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
async def create_transaction(
    business_id: UUID,
    request: CreateTransactionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create payment transaction."""
    return await PaymentService.create_transaction(
        business_id=business_id,
        amount=request.amount,
        currency=request.currency,
        method=request.method,
        customer_id=request.customer_id,
        order_id=request.order_id,
        location_id=request.location_id,
        conversation_id=request.conversation_id,
        description=request.description,
        reference_id=request.reference_id,
        db=db
    )


@router.post("/businesses/{business_id}/checkout/mercadopago")
async def create_mercadopago_checkout(
    business_id: UUID,
    request: CreateCheckoutRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create MercadoPago checkout."""
    return await PaymentService.create_mercadopago_checkout(
        business_id=business_id,
        customer_email=request.customer_email,
        customer_name=request.customer_name,
        items=request.items,
        amount=request.amount,
        currency=request.currency,
        order_id=request.order_id,
        conversation_id=request.conversation_id,
        db=db
    )


@router.post("/businesses/{business_id}/webhooks/mercadopago")
async def handle_mercadopago_webhook(
    business_id: UUID,
    request: ProcessWebhookRequest,
    db: AsyncSession = Depends(get_db)
):
    """Handle MercadoPago webhook notification."""
    return await PaymentService.process_mercadopago_webhook(
        business_id=business_id,
        event_data=request.dict(),
        db=db
    )


@router.post("/businesses/{business_id}/refunds")
async def create_refund(
    business_id: UUID,
    request: CreateRefundRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create refund request."""
    return await PaymentService.create_refund(
        transaction_id=request.transaction_id,
        business_id=business_id,
        amount=request.amount,
        reason=request.reason,
        db=db
    )


@router.post("/businesses/{business_id}/reconcile")
async def reconcile_transaction(
    business_id: UUID,
    request: ReconcileTransactionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reconcile order with payment transaction."""
    return await PaymentService.reconcile_transaction(
        order_id=request.order_id,
        transaction_id=request.transaction_id,
        business_id=business_id,
        db=db
    )


@router.get("/businesses/{business_id}/transactions")
async def get_transactions(
    business_id: UUID,
    status: Optional[str] = Query(None),
    location_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get transactions."""
    return await PaymentService.get_transactions(
        business_id=business_id,
        status=status,
        location_id=location_id,
        limit=limit,
        db=db
    )


@router.get("/businesses/{business_id}/settlements/metrics")
async def get_settlement_metrics(
    business_id: UUID,
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get settlement metrics."""
    return await PaymentService.get_settlement_metrics(
        business_id=business_id,
        period_days=period_days,
        db=db
    )


@router.get("/businesses/{business_id}/payments/metrics")
async def get_payment_metrics(
    business_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get payment metrics."""
    return await PaymentService.get_payment_metrics(
        business_id=business_id,
        db=db
    )
