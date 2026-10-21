"""Stripe Payment Connector — Real payment processing.

Procesa pagos, crea checkout sessions, maneja webhooks.
"""

import logging
from typing import Any

import stripe

logger = logging.getLogger(__name__)


class StripeConnector:
    """Conector real de Stripe API."""

    def __init__(self, api_key: str):
        """api_key: Stripe Secret Key"""
        stripe.api_key = api_key
        self.api_key = api_key

    async def create_checkout_session(
        self,
        customer_email: str,
        product_name: str,
        amount_cents: int,
        success_url: str,
        cancel_url: str,
        customer_name: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Crea sesión de checkout.

        amount_cents: precio en centavos (ej: $19.99 = 1999)

        Retorna: (success, checkout_url)
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": product_name,
                            },
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                client_reference_id=customer_name or customer_email,
            )

            checkout_url = session.url

            logger.info(f"Checkout session created: {session.id} | ${amount_cents / 100}")

            return True, checkout_url

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return False, None
        except Exception:
            logger.exception("Error creating checkout")
            return False, None

    async def create_payment_intent(
        self,
        amount_cents: int,
        currency: str = "usd",
        description: str = "",
        customer_email: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Crea payment intent (más flexible que checkout).

        Retorna: (success, client_secret)
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                description=description,
                receipt_email=customer_email,
            )

            client_secret = intent.client_secret

            logger.info(f"Payment intent created: {intent.id}")

            return True, client_secret

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return False, None
        except Exception:
            logger.exception("Error creating intent")
            return False, None

    async def get_payment_status(self, session_id: str) -> dict[str, Any]:
        """Obtiene status de sesión."""
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            return {
                "id": session.id,
                "status": session.payment_status,
                "customer_email": session.customer_email,
                "amount_total": session.amount_total,
                "payment_intent": session.payment_intent,
            }

        except Exception:
            logger.exception("Error getting payment status")
            return {}

    async def create_refund(
        self,
        payment_intent_id: str,
        reason: str = "requested_by_customer",
    ) -> tuple[bool, str | None]:
        """Crea refund."""
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                reason=reason,
            )

            logger.info(f"Refund created: {refund.id}")

            return True, refund.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return False, None
        except Exception:
            logger.exception("Error creating refund")
            return False, None


def get_stripe_connector(api_key: str) -> StripeConnector:
    return StripeConnector(api_key)
