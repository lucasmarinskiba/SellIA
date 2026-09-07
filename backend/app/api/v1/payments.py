"""Payment API endpoints."""

from uuid import UUID
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.integrations.mercadopago_webhook import verify_mercadopago_signature
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.payments.payment_service import PaymentService

router = APIRouter(prefix="/api/v1", tags=["payments"])


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    """Same convention as websites.py/catalog.py/channels.py/conversations.py.

    Every route below used to take business_id straight from the URL with no
    user at all -- create_transaction, create_mercadopago_checkout, create_
    refund, reconcile_transaction and both metrics reads worked for ANY
    business_id, no login required. create_refund in particular can trigger
    a real MercadoPago refund (see payment_service.create_refund) -- this
    was a live, unauthenticated financial-fraud vector, not just a data leak.
    """
    result = await db.execute(
        select(Business).where(Business.id == business_id, Business.user_id == user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create payment transaction."""
    await _get_business_for_user(business_id, current_user, db)
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create MercadoPago checkout."""
    await _get_business_for_user(business_id, current_user, db)
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
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle MercadoPago webhook notification.

    Deliberately NOT behind get_current_user -- MercadoPago itself calls
    this, it has no user session. The real security boundary here is the
    signature check below, which this endpoint previously didn't have at
    all: it took a bare {type, data: {id, status, external_reference}}
    JSON body and, for event_data.type == "payment", set the referenced
    transaction's status straight to APPROVED (see payment_service.
    _handle_payment_webhook) -- anyone who created a transaction via the
    equally-unauthenticated create_transaction above (or simply guessed/
    obtained an existing transaction_id) could mark it "paid" with a
    single unsigned POST. Complete payment-confirmation bypass.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not verify_mercadopago_signature(request, body):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    return await PaymentService.process_mercadopago_webhook(
        business_id=business_id,
        event_data=body,
        db=db
    )


@router.post("/businesses/{business_id}/refunds")
async def create_refund(
    business_id: UUID,
    request: CreateRefundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create refund request."""
    await _get_business_for_user(business_id, current_user, db)
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reconcile order with payment transaction."""
    await _get_business_for_user(business_id, current_user, db)
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get transactions."""
    await _get_business_for_user(business_id, current_user, db)
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get settlement metrics."""
    await _get_business_for_user(business_id, current_user, db)
    return await PaymentService.get_settlement_metrics(
        business_id=business_id,
        period_days=period_days,
        db=db
    )


@router.get("/businesses/{business_id}/payments/metrics")
async def get_payment_metrics(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment metrics."""
    await _get_business_for_user(business_id, current_user, db)
    return await PaymentService.get_payment_metrics(
        business_id=business_id,
        db=db
    )
