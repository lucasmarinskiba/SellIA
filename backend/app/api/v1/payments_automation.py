"""
Payments API — Stripe checkout automático + webhooks.

Endpoints:
- POST /api/v1/payments/checkout (crear checkout)
- POST /api/v1/payments/webhook (Stripe webhook)
- POST /api/v1/payments/refund (procesar refund)
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/checkout")
async def create_payment_checkout(
    product: Dict[str, Any],
    buyer: Dict[str, Any],
    metadata: Dict[str, Any] = None,
    stripe_service=None,  # Inyectado desde DI
) -> Dict[str, Any]:
    """
    Crea Stripe checkout automáticamente.

    POST /api/v1/payments/checkout
    {
      "product": {"id": "prod_123", "name": "...", "price": 99.99, "description": "..."},
      "buyer": {"email": "buyer@example.com", "name": "John", "phone": "+1234567890"},
      "metadata": {"order_id": "order_123", "campaign": "email_blast"}
    }
    """

    logger.info(f"Creating checkout for {buyer.get('email')}")

    try:
        result = await stripe_service.create_checkout_session(product, buyer, metadata)

        if result["status"] == "success":
            return {
                "status": "success",
                "checkout_url": result["checkout_url"],
                "session_id": result["session_id"],
                "expires_at": result["expires_at"],
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))

    except Exception as e:
        logger.error(f"Checkout creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscription/checkout")
async def create_subscription_checkout(
    plan: Dict[str, Any],
    buyer: Dict[str, Any],
    stripe_service=None,
) -> Dict[str, Any]:
    """
    Crea checkout para suscripción.

    POST /api/v1/payments/subscription/checkout
    {
      "plan": {"name": "Pro", "price": 29.99, "interval": "month"},
      "buyer": {"email": "buyer@example.com", "name": "John"}
    }
    """

    logger.info(f"Creating subscription checkout for {buyer.get('email')}")

    try:
        result = await stripe_service.create_subscription_checkout(plan, buyer)

        if result["status"] == "success":
            return {
                "status": "success",
                "checkout_url": result["checkout_url"],
                "session_id": result["session_id"],
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))

    except Exception as e:
        logger.error(f"Subscription checkout failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_service=None,
) -> Dict[str, Any]:
    """
    Endpoint para webhooks de Stripe.

    Stripe enviará eventos (payment.success, checkout.completed, etc)
    """

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature")

    logger.info("Processing Stripe webhook")

    try:
        result = await stripe_service.handle_webhook(payload, sig_header)
        return result

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refund")
async def process_refund(
    payment_intent_id: str,
    reason: str = "requested_by_customer",
    stripe_service=None,
) -> Dict[str, Any]:
    """
    Procesa refund automáticamente.

    POST /api/v1/payments/refund
    {
      "payment_intent_id": "pi_xxx",
      "reason": "requested_by_customer"
    }
    """

    logger.info(f"Processing refund for {payment_intent_id}")

    try:
        result = await stripe_service.process_refund(payment_intent_id, reason)

        if result["status"] == "success":
            return {
                "status": "success",
                "refund_id": result["refund_id"],
                "amount_refunded": result["amount"],
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))

    except Exception as e:
        logger.error(f"Refund processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoice")
async def create_invoice(
    customer_email: str,
    amount: float,
    description: str,
    due_date_days: int = 30,
    stripe_service=None,
) -> Dict[str, Any]:
    """
    Crea invoice automáticamente.

    POST /api/v1/payments/invoice
    """

    logger.info(f"Creating invoice for {customer_email}")

    try:
        result = await stripe_service.create_invoice(
            customer_email, amount, description, due_date_days
        )

        if result["status"] == "success":
            return {
                "status": "success",
                "invoice_id": result["invoice_id"],
                "payment_url": result["payment_url"],
                "due_date": result["due_date"],
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))

    except Exception as e:
        logger.error(f"Invoice creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/{customer_id}/balance")
async def get_customer_balance(
    customer_id: str,
    stripe_service=None,
) -> Dict[str, Any]:
    """
    Obtiene balance + history de customer.
    """

    logger.info(f"Getting balance for customer {customer_id}")

    try:
        result = await stripe_service.get_customer_balance(customer_id)

        if result["status"] == "success":
            return result
        else:
            raise HTTPException(status_code=400)

    except Exception as e:
        logger.error(f"Get balance failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
