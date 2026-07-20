"""
Payment processing — Stripe, PayPal, transferencias bancarias.

Webhooks para confirmación de pagos.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import json

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])
logger = logging.getLogger(__name__)

# Mock payment state (TODO: real Stripe integration)
_PAYMENT_INTENTS_DB: Dict[str, Any] = {}


class PaymentIntent(BaseModel):
    """Intención de pago."""
    id: str
    order_id: str
    amount_usd: float
    currency: str = "usd"
    payment_method: str  # stripe, paypal, bank
    status: str  # pending, processing, succeeded, failed
    stripe_session_id: Optional[str] = None


class PaymentConfirmation(BaseModel):
    """Confirmación de pago desde webhook."""
    payment_intent_id: str
    status: str
    amount_received: float
    timestamp: datetime


@router.post("/stripe/create-checkout", tags=["stripe"])
async def create_stripe_checkout(order_id: str, amount_usd: float):
    """
    Crea Stripe Checkout Session.

    En producción: llamar stripe.checkout.Session.create()
    """
    try:
        logger.info(f"Creando Stripe checkout para orden {order_id}, monto ${amount_usd}")

        # TODO: real Stripe API
        # stripe_session = stripe.checkout.Session.create(
        #     payment_method_types=['card'],
        #     line_items=[{
        #         'price_data': {
        #             'currency': 'usd',
        #             'unit_amount': int(amount_usd * 100),  # cents
        #             'product_data': {'name': f'Order {order_id}'},
        #         },
        #         'quantity': 1,
        #     }],
        #     mode='payment',
        #     success_url='https://example.com/success?session_id={CHECKOUT_SESSION_ID}',
        #     cancel_url='https://example.com/cancel',
        #     metadata={'order_id': order_id},
        # )

        # Mock response
        payment_id = f"pi_{order_id}"
        _PAYMENT_INTENTS_DB[payment_id] = {
            "id": payment_id,
            "order_id": order_id,
            "amount_usd": amount_usd,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        }

        return {
            "status": "session_created",
            "payment_id": payment_id,
            "amount": amount_usd,
            "checkout_url": f"https://checkout.stripe.com/pay/session-{payment_id}",  # TODO: real URL
            "order_id": order_id
        }

    except Exception as e:
        logger.error(f"Error creando Stripe session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stripe/webhook", tags=["webhooks"])
async def stripe_webhook(request: Request, x_stripe_signature: Optional[str] = None):
    """
    Webhook de Stripe para confirmar pagos.

    Eventos: payment_intent.succeeded, payment_intent.payment_failed
    """

    try:
        body = await request.body()
        payload = json.loads(body)

        # TODO: Verificar signature real con Stripe secret
        # event = stripe.Webhook.construct_event(
        #     body, x_stripe_signature, endpoint_secret
        # )

        event_type = payload.get("type")

        if event_type == "payment_intent.succeeded":
            payment_intent_id = payload["data"]["object"]["id"]
            order_id = payload["data"]["object"]["metadata"].get("order_id")
            amount_received = payload["data"]["object"]["amount_received"] / 100  # Convert from cents

            logger.info(f"Stripe pago confirmado: {payment_intent_id} para orden {order_id}, monto ${amount_received}")

            # TODO: Actualizar orden status a 'paid'
            # order = get_order(order_id)
            # order.payment_status = 'confirmed'
            # order.save()

            # Marcar en mock DB
            if payment_intent_id in _PAYMENT_INTENTS_DB:
                _PAYMENT_INTENTS_DB[payment_intent_id]["status"] = "succeeded"

            return {"status": "processed", "payment_id": payment_intent_id}

        elif event_type == "payment_intent.payment_failed":
            payment_intent_id = payload["data"]["object"]["id"]
            order_id = payload["data"]["object"]["metadata"].get("order_id")

            logger.error(f"Stripe pago falló: {payment_intent_id} para orden {order_id}")

            # TODO: Enviar email a usuario "Pago rechazado, intenta de nuevo"
            # send_email_payment_failed(order_id)

            if payment_intent_id in _PAYMENT_INTENTS_DB:
                _PAYMENT_INTENTS_DB[payment_intent_id]["status"] = "failed"

            return {"status": "processed", "payment_id": payment_intent_id}

        # Ignorar otros eventos
        return {"status": "received"}

    except Exception as e:
        logger.error(f"Error procesando Stripe webhook: {str(e)}")
        return {"status": "error", "detail": str(e)}


@router.post("/bank-transfer/confirm", tags=["bank"])
async def confirm_bank_transfer(order_id: str, amount_usd: float, tx_hash: Optional[str] = None):
    """
    Confirmación manual de transferencia bancaria.

    Admin verifica en banco, ejecuta este endpoint.
    """

    try:
        logger.info(f"Confirmando transferencia bancaria para orden {order_id}, monto ${amount_usd}")

        # TODO: Actualizar orden status
        # order = get_order(order_id)
        # order.payment_status = 'confirmed'
        # order.payment_method_tx = tx_hash
        # order.save()

        # Mock
        payment_id = f"bank_{order_id}"
        _PAYMENT_INTENTS_DB[payment_id] = {
            "id": payment_id,
            "order_id": order_id,
            "amount_usd": amount_usd,
            "status": "succeeded",
            "tx_hash": tx_hash,
            "confirmed_at": datetime.utcnow().isoformat(),
        }

        return {"status": "confirmed", "order_id": order_id, "amount": amount_usd}

    except Exception as e:
        logger.error(f"Error confirmando transferencia: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment/{payment_id}", tags=["status"])
async def get_payment_status(payment_id: str):
    """Estado del pago."""

    if payment_id not in _PAYMENT_INTENTS_DB:
        raise HTTPException(status_code=404, detail="Payment not found")

    return _PAYMENT_INTENTS_DB[payment_id]
