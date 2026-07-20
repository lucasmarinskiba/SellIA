"""
Stripe integration real — Pagos seguros, webhooks, invoicing.

Env vars required:
- STRIPE_SECRET_KEY
- STRIPE_PUBLISHABLE_KEY
- STRIPE_WEBHOOK_SECRET
"""

import os
import logging
import stripe
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_dummy")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_dummy")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

stripe.api_key = STRIPE_SECRET_KEY


class StripePaymentProcessor:
    """Procesa pagos con Stripe."""

    @staticmethod
    def create_payment_intent(
        customer_email: str,
        amount_usd: float,
        product_name: str,
        order_id: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crea payment intent para checkout.

        Retorna: client_secret para frontend + session info.
        """

        try:
            amount_cents = int(amount_usd * 100)

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                receipt_email=customer_email,
                description=description or f"Purchase: {product_name}",
                metadata={
                    "order_id": order_id,
                    "product_name": product_name,
                },
            )

            logger.info(f"Payment intent created: {intent.id} for order {order_id} (${amount_usd})")

            return {
                "status": "intent_created",
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": amount_usd,
                "currency": "usd",
            }

        except stripe.error.CardError as e:
            logger.error(f"Card error: {e.user_message}")
            return {"status": "error", "message": e.user_message}
        except stripe.error.RateLimitError:
            logger.error("Stripe rate limit exceeded")
            return {"status": "error", "message": "Service temporarily unavailable"}
        except stripe.error.AuthenticationError:
            logger.error("Stripe authentication error")
            return {"status": "error", "message": "Payment service authentication failed"}
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def create_checkout_session(
        customer_email: str,
        product_name: str,
        amount_usd: float,
        order_id: str,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, Any]:
        """
        Crea Stripe Checkout session (hosted checkout).

        Retorna: session_id para redirect.
        """

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": int(amount_usd * 100),
                            "product_data": {
                                "name": product_name,
                            },
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                customer_email=customer_email,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "order_id": order_id,
                    "product_name": product_name,
                },
            )

            logger.info(f"Checkout session created: {session.id} for {order_id}")

            return {
                "status": "session_created",
                "session_id": session.id,
                "checkout_url": session.url,
                "order_id": order_id,
            }

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def retrieve_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """Obtiene estado payment intent."""

        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,  # Convert cents to USD
                "currency": intent.currency,
                "customer_email": intent.receipt_email,
            }

        except Exception as e:
            logger.error(f"Error retrieving payment intent: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def refund_payment(payment_intent_id: str, amount_usd: Optional[float] = None) -> Dict[str, Any]:
        """Reembolsa pago (total o parcial)."""

        try:
            refund_data = {"payment_intent": payment_intent_id}
            if amount_usd:
                refund_data["amount"] = int(amount_usd * 100)

            refund = stripe.Refund.create(**refund_data)

            logger.info(f"Refund created: {refund.id}")

            return {
                "status": "refunded",
                "refund_id": refund.id,
                "payment_intent_id": payment_intent_id,
                "amount_refunded": refund.amount / 100,
            }

        except Exception as e:
            logger.error(f"Error refunding payment: {str(e)}")
            return {"status": "error", "message": str(e)}


class StripeWebhookHandler:
    """Maneja webhooks Stripe."""

    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> bool:
        """Verifica firma webhook."""

        try:
            stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
            return True
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return False
        except Exception as e:
            logger.error(f"Webhook verification error: {str(e)}")
            return False

    @staticmethod
    def handle_webhook(event: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja evento webhook."""

        event_type = event.get("type")

        if event_type == "payment_intent.succeeded":
            return StripeWebhookHandler._handle_payment_succeeded(event)
        elif event_type == "payment_intent.payment_failed":
            return StripeWebhookHandler._handle_payment_failed(event)
        elif event_type == "charge.refunded":
            return StripeWebhookHandler._handle_refund(event)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")
            return {"status": "acknowledged", "event_type": event_type}

    @staticmethod
    def _handle_payment_succeeded(event: Dict[str, Any]) -> Dict[str, Any]:
        """Payment intent succeeded."""

        payment_intent = event["data"]["object"]
        order_id = payment_intent.get("metadata", {}).get("order_id")
        amount = payment_intent.get("amount", 0) / 100

        logger.info(f"Payment succeeded: {payment_intent.id} for order {order_id} (${amount})")

        # TODO: Update order status en DB, enviar factura, trigger fulfillment
        # db.orders.update_one(
        #     {"order_id": order_id},
        #     {"$set": {"payment_status": "confirmed", "confirmed_at": datetime.utcnow()}}
        # )

        return {
            "status": "processed",
            "event": "payment_succeeded",
            "order_id": order_id,
            "amount": amount,
        }

    @staticmethod
    def _handle_payment_failed(event: Dict[str, Any]) -> Dict[str, Any]:
        """Payment intent failed."""

        payment_intent = event["data"]["object"]
        order_id = payment_intent.get("metadata", {}).get("order_id")

        logger.error(f"Payment failed: {payment_intent.id} for order {order_id}")

        # TODO: Notificar usuario, guardar en DB, enviar email "payment failed"

        return {
            "status": "processed",
            "event": "payment_failed",
            "order_id": order_id,
        }

    @staticmethod
    def _handle_refund(event: Dict[str, Any]) -> Dict[str, Any]:
        """Charge refunded."""

        refund = event["data"]["object"]
        payment_intent_id = refund.get("payment_intent")
        amount = refund.get("amount", 0) / 100

        logger.info(f"Refund processed: {refund.id} (${amount})")

        # TODO: Update order status, notify customer

        return {
            "status": "processed",
            "event": "refund_processed",
            "amount": amount,
        }
