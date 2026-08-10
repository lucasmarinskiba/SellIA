"""Stripe payment processing and webhooks."""

import logging
from typing import Optional, Dict, Any
from enum import Enum
import hmac
import hashlib
import json

logger = logging.getLogger(__name__)


class StripeEventType(str, Enum):
    """Stripe webhook event types."""
    PAYMENT_SUCCEEDED = "payment_intent.succeeded"
    PAYMENT_FAILED = "payment_intent.payment_failed"
    INVOICE_PAID = "invoice.paid"
    INVOICE_PAYMENT_FAILED = "invoice.payment_action_required"
    CHARGE_DISPUTE_CREATED = "charge.dispute.created"
    CUSTOMER_CREATED = "customer.created"


class StripeService:
    """Stripe payment service integration."""

    def __init__(self, api_key: str, webhook_secret: str):
        """
        Initialize Stripe service.

        Args:
            api_key: Stripe API key
            webhook_secret: Webhook signing secret
        """
        self.api_key = api_key
        self.webhook_secret = webhook_secret

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header value

        Returns:
            True if signature is valid
        """
        try:
            # Extract timestamp and signatures from header
            parts = signature.split(",")
            timestamp = None
            stripe_signature = None

            for part in parts:
                key, value = part.split("=")
                if key == "t":
                    timestamp = value
                elif key == "v1":
                    stripe_signature = value

            if not timestamp or not stripe_signature:
                return False

            # Compute expected signature
            signed_content = f"{timestamp}.{payload}"
            expected_sig = hmac.new(
                self.webhook_secret.encode(),
                signed_content.encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(stripe_signature, expected_sig)

        except Exception as e:
            logger.error(f"Webhook verification failed: {e}")
            return False

    async def handle_payment_succeeded(
        self, event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle payment_intent.succeeded event."""
        try:
            payment_intent = event_data.get("object", {})
            customer_id = payment_intent.get("customer")
            amount = payment_intent.get("amount") / 100  # Stripe uses cents
            currency = payment_intent.get("currency", "usd").upper()

            logger.info(
                f"Payment succeeded: ${amount} {currency} from customer {customer_id}"
            )

            return {
                "event_type": StripeEventType.PAYMENT_SUCCEEDED,
                "customer_id": customer_id,
                "amount": amount,
                "currency": currency,
                "status": "completed",
                "action": "activate_subscription",  # Auto-activate subscription
            }

        except Exception as e:
            logger.error(f"Payment success handler failed: {e}")
            return None

    async def handle_payment_failed(
        self, event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle payment failure."""
        try:
            payment_intent = event_data.get("object", {})
            customer_id = payment_intent.get("customer")
            error = payment_intent.get("last_payment_error", {}).get("message", "Unknown error")

            logger.warning(f"Payment failed for customer {customer_id}: {error}")

            return {
                "event_type": StripeEventType.PAYMENT_FAILED,
                "customer_id": customer_id,
                "error": error,
                "status": "failed",
                "action": "retry_payment",  # Retry logic
            }

        except Exception as e:
            logger.error(f"Payment failure handler failed: {e}")
            return None

    async def handle_invoice_paid(
        self, event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle invoice.paid event."""
        try:
            invoice = event_data.get("object", {})
            customer_id = invoice.get("customer")
            amount = invoice.get("amount_paid") / 100
            period_start = invoice.get("period_start")
            period_end = invoice.get("period_end")

            logger.info(f"Invoice paid: ${amount} from customer {customer_id}")

            return {
                "event_type": StripeEventType.INVOICE_PAID,
                "customer_id": customer_id,
                "amount": amount,
                "period_start": period_start,
                "period_end": period_end,
                "status": "paid",
            }

        except Exception as e:
            logger.error(f"Invoice paid handler failed: {e}")
            return None

    async def create_customer(
        self, email: str, name: str, company: str
    ) -> Optional[str]:
        """Create Stripe customer."""
        try:
            # In production, call Stripe API
            logger.info(f"Stripe customer created: {name} ({email})")
            return f"cus_{datetime.now().timestamp()}"

        except Exception as e:
            logger.error(f"Customer creation failed: {e}")
            return None

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        annual_price: float,
    ) -> Optional[str]:
        """Create subscription."""
        try:
            # In production, call Stripe API
            logger.info(
                f"Subscription created: {customer_id} - ${annual_price}/year"
            )
            return f"sub_{datetime.now().timestamp()}"

        except Exception as e:
            logger.error(f"Subscription creation failed: {e}")
            return None


from datetime import datetime
