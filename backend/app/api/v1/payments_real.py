"""
Payments API real — Stripe + SendGrid + Database.

Endpoints:
- POST /create-checkout: Inicia checkout Stripe
- POST /webhook/stripe: Webhook confirmación Stripe
- GET /order/:id: Estado orden
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
import json

from backend.app.core.integrations.stripe_payment import StripePaymentProcessor, StripeWebhookHandler
from backend.app.core.integrations.sendgrid_email import EmailService
from backend.app.core.database.models import get_db, Order, Account
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])
logger = logging.getLogger(__name__)


class CheckoutRequest(BaseModel):
    """Request crear checkout."""

    account_id: str
    customer_email: str
    customer_name: str
    product_name: str
    amount_usd: float
    success_url: str
    cancel_url: str


@router.post("/create-checkout")
async def create_checkout(request: CheckoutRequest, db: Session = Depends(get_db)):
    """
    Crea checkout Stripe.

    Retorna: checkout_url para redirect a Stripe.
    """

    try:
        logger.info(f"Creando checkout para {request.customer_email}, ${request.amount_usd}")

        # Crear checkout Stripe
        checkout = StripePaymentProcessor.create_checkout_session(
            customer_email=request.customer_email,
            product_name=request.product_name,
            amount_usd=request.amount_usd,
            order_id=f"order_{datetime.utcnow().timestamp()}",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )

        if checkout["status"] != "session_created":
            raise HTTPException(status_code=400, detail=checkout.get("message", "Checkout failed"))

        # Guardar orden en DB
        order = Order(
            id=checkout["order_id"],
            account_id=request.account_id,
            customer_email=request.customer_email,
            customer_name=request.customer_name,
            amount_usd=request.amount_usd,
            status="pending",
        )
        db.add(order)
        db.commit()

        logger.info(f"Order creada en DB: {order.id}")

        # Enviar email con link checkout
        EmailService.send_transactional(
            to_email=request.customer_email,
            subject=f"Completa tu compra de {request.product_name}",
            html_content=f"""
            <h1>Casi listo!</h1>
            <p>Haz clic para completar tu pago de ${request.amount_usd}</p>
            <p><a href="{checkout['checkout_url']}">Completar pago →</a></p>
            <p><small>Este link expira en 24 horas.</small></p>
            """,
        )

        return {
            "status": "checkout_created",
            "order_id": checkout["order_id"],
            "checkout_url": checkout["checkout_url"],
            "amount": request.amount_usd,
        }

    except Exception as e:
        logger.error(f"Error creating checkout: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook Stripe → Confirma pago → Actualiza DB → Envía email.
    """

    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")

        # Verificar firma
        if not StripeWebhookHandler.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse event
        event = json.loads(payload)

        logger.info(f"Webhook received: {event['type']}")

        # Manejar evento
        result = StripeWebhookHandler.handle_webhook(event)

        # Si pago exitoso → Actualizar orden en DB
        if result["status"] == "processed" and result.get("event") == "payment_succeeded":
            order_id = result.get("order_id")

            # Actualizar orden
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.payment_status = "confirmed"
                order.status = "paid"
                order.completed_at = datetime.utcnow()
                db.commit()

                logger.info(f"Order {order_id} marked as paid")

                # Enviar factura
                EmailService.send_transactional(
                    to_email=order.customer_email,
                    subject=f"Factura: {order.customer_name}",
                    html_content=f"""
                    <h1>¡Gracias por tu compra!</h1>
                    <p>Factura #{order_id}</p>
                    <p>Monto: ${order.amount_usd}</p>
                    <p>Fecha: {order.completed_at}</p>
                    <p>Tu producto estará listo en breve.</p>
                    """,
                )

        return {"status": "webhook_processed"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order/{order_id}")
async def get_order(order_id: str, db: Session = Depends(get_db)):
    """Obtiene estado orden."""

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order.id,
        "customer": order.customer_name,
        "amount": order.amount_usd,
        "status": order.status,
        "payment_status": order.payment_status,
        "created_at": order.created_at.isoformat(),
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
    }
