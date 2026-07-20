"""
MercadoPago Payment Processor — Latin America payment integration.

Features:
- Mercado Pago Checkout Pro (hosted checkout)
- Direct payment links
- Webhook handling for payment notifications
- Installment payment support
- Refund processing
- Multi-currency support (ARS, BRL, CLP, COL, MXN, PEN, UYU, USD)

Env vars:
- MERCADOPAGO_ACCESS_TOKEN: API access token
- MERCADOPAGO_PUBLIC_KEY: Frontend public key
- MERCADOPAGO_WEBHOOK_SECRET: Webhook signing secret
- MERCADOPAGO_NOTIFICATION_URL: Webhook notification URL
"""

import os
import logging
import requests
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# MercadoPago API
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "TEST_TOKEN")
MERCADOPAGO_PUBLIC_KEY = os.getenv("MERCADOPAGO_PUBLIC_KEY", "TEST_KEY")
MERCADOPAGO_WEBHOOK_SECRET = os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "TEST_SECRET")
MERCADOPAGO_NOTIFICATION_URL = os.getenv(
    "MERCADOPAGO_NOTIFICATION_URL",
    "https://api.example.com/webhooks/mercadopago"
)

MERCADOPAGO_API_BASE = "https://api.mercadopago.com/v1"
MERCADOPAGO_CHECKOUT_BASE = "https://www.mercadopago.com.ar/checkout/pay"


class CurrencyCode(str, Enum):
    """Supported currencies in MercadoPago."""
    ARS = "ARS"  # Argentine Peso
    BRL = "BRL"  # Brazilian Real
    CLP = "CLP"  # Chilean Peso
    COP = "COP"  # Colombian Peso
    MXN = "MXN"  # Mexican Peso
    PEN = "PEN"  # Peruvian Sol
    UYU = "UYU"  # Uruguayan Peso
    USD = "USD"  # US Dollar


class PaymentStatus(str, Enum):
    """MercadoPago payment statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    AUTHORIZED = "authorized"
    IN_PROCESS = "in_process"
    IN_MEDIATION = "in_mediation"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    CHARGED_BACK = "charged_back"


class MercadoPagoProcessor:
    """MercadoPago payment processor."""

    @staticmethod
    def create_checkout_preference(
        external_reference: str,
        customer_email: str,
        customer_name: str,
        items: list,
        currency_code: str = "USD",
        notification_url: Optional[str] = None,
        installments: int = 1,
        auto_return: str = "approved",
        back_urls: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create MercadoPago Checkout Pro preference.

        Args:
            external_reference: Internal order/transaction ID
            customer_email: Customer email
            customer_name: Customer name
            items: List of items [{name, qty, unit_price}]
            currency_code: Currency (default USD)
            notification_url: Webhook URL for notifications
            installments: Max installments allowed (1-12)
            auto_return: Redirect behavior (approved, all, none)
            back_urls: Custom redirect URLs {success, failure, pending}

        Returns:
            {
                "status": "preference_created" | "error",
                "preference_id": str,
                "checkout_url": str,
                "init_point": str,
                "expires_at": datetime,
                "error": str (if error)
            }
        """
        try:
            if not items or len(items) == 0:
                raise ValueError("At least one item is required")

            if currency_code not in [c.value for c in CurrencyCode]:
                raise ValueError(f"Unsupported currency: {currency_code}")

            # Prepare preference payload
            preference = {
                "external_reference": external_reference,
                "payer": {
                    "name": customer_name,
                    "email": customer_email,
                },
                "items": items,
                "back_urls": back_urls or {
                    "success": f"{MERCADOPAGO_NOTIFICATION_URL}/success",
                    "failure": f"{MERCADOPAGO_NOTIFICATION_URL}/failure",
                    "pending": f"{MERCADOPAGO_NOTIFICATION_URL}/pending",
                },
                "auto_return": auto_return,
                "notification_url": notification_url or MERCADOPAGO_NOTIFICATION_URL,
                "installments": installments,
                "currency_id": currency_code,
            }

            # Create preference via API
            headers = {
                "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"{MERCADOPAGO_API_BASE}/checkout/preferences",
                json=preference,
                headers=headers,
                timeout=30,
            )

            if response.status_code not in (200, 201):
                logger.error(
                    f"MercadoPago error: {response.status_code} - {response.text}"
                )
                return {
                    "status": "error",
                    "error": f"API error: {response.status_code}",
                }

            data = response.json()
            preference_id = data.get("id")
            init_point = data.get("init_point")

            logger.info(
                f"MercadoPago preference created: {preference_id} | "
                f"Reference: {external_reference}"
            )

            return {
                "status": "preference_created",
                "preference_id": preference_id,
                "checkout_url": init_point,
                "init_point": init_point,
                "expires_at": datetime.utcnow(),
                "external_reference": external_reference,
            }

        except requests.RequestException as e:
            logger.error(f"MercadoPago API error: {str(e)}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.error(f"Error creating preference: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def get_payment_info(payment_id: str) -> Dict[str, Any]:
        """
        Get payment information.

        Args:
            payment_id: MercadoPago payment ID

        Returns:
            {
                "status": "retrieved" | "error",
                "payment_id": str,
                "status": str,
                "amount": float,
                "currency": str,
                "external_reference": str,
                "payer_email": str,
                "installments": int,
                "error": str (if error)
            }
        """
        try:
            headers = {
                "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
            }

            response = requests.get(
                f"{MERCADOPAGO_API_BASE}/payments/{payment_id}",
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(f"Error getting payment: {response.status_code}")
                return {"status": "error", "error": "Payment not found"}

            payment = response.json()

            return {
                "status": "retrieved",
                "payment_id": payment["id"],
                "status": payment["status"],
                "amount": payment["transaction_amount"],
                "currency": payment["currency_id"],
                "external_reference": payment.get("external_reference"),
                "payer_email": payment["payer"]["email"],
                "installments": payment["installments"],
                "created_at": payment["date_created"],
                "approved_at": payment.get("date_approved"),
            }

        except Exception as e:
            logger.error(f"Error retrieving payment: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def refund_payment(
        payment_id: str,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Refund a payment (full or partial).

        Args:
            payment_id: MercadoPago payment ID
            amount: Amount to refund (None = full refund)

        Returns:
            {
                "status": "refunded" | "error",
                "refund_id": str,
                "payment_id": str,
                "amount_refunded": float,
                "error": str (if error)
            }
        """
        try:
            headers = {
                "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }

            payload = {}
            if amount:
                payload["amount"] = amount

            response = requests.post(
                f"{MERCADOPAGO_API_BASE}/payments/{payment_id}/refunds",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code not in (200, 201):
                logger.error(
                    f"Refund error: {response.status_code} - {response.text}"
                )
                return {"status": "error", "error": "Refund failed"}

            refund = response.json()

            logger.info(f"Refund created: {refund.get('id')} | Payment: {payment_id}")

            return {
                "status": "refunded",
                "refund_id": refund.get("id"),
                "payment_id": payment_id,
                "amount_refunded": refund.get("amount", amount),
                "status": refund.get("status"),
            }

        except Exception as e:
            logger.error(f"Error refunding payment: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def create_payment_link(
        external_reference: str,
        title: str,
        description: str,
        amount: float,
        currency: str = "USD",
        expiration_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Create a payment link (alternative to Checkout Pro).

        Args:
            external_reference: Internal ID
            title: Payment title
            description: Payment description
            amount: Amount in currency
            currency: Currency code
            expiration_days: Link expiration in days

        Returns:
            {
                "status": "link_created" | "error",
                "url": str,
                "qr_code": str,
                "error": str (if error)
            }
        """
        try:
            headers = {
                "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }

            payload = {
                "title": title,
                "description": description,
                "reference_id": external_reference,
                "price": amount,
                "currency_id": currency,
                "expires_at": (
                    datetime.utcnow() + timedelta(days=expiration_days)
                ).isoformat(),
            }

            response = requests.post(
                f"{MERCADOPAGO_API_BASE}/payment_links",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code not in (200, 201):
                logger.error(f"Payment link error: {response.text}")
                return {"status": "error", "error": "Failed to create link"}

            link_data = response.json()

            return {
                "status": "link_created",
                "url": link_data.get("url"),
                "qr_code": link_data.get("qr_code"),
                "reference_id": external_reference,
            }

        except Exception as e:
            logger.error(f"Error creating payment link: {str(e)}")
            return {"status": "error", "error": str(e)}


class MercadoPagoWebhookHandler:
    """Handle MercadoPago webhook notifications."""

    @staticmethod
    def verify_signature(
        request_body: str,
        x_signature: str,
        x_request_id: str,
    ) -> bool:
        """
        Verify MercadoPago webhook signature.

        X-Signature format: ts=timestamp,v1=hash
        """
        try:
            parts = x_signature.split(",")
            timestamp = parts[0].split("=")[1]
            signature = parts[1].split("=")[1]

            # Verify signature
            data = f"id={x_request_id};{request_body};{timestamp}"
            calculated_signature = hmac.new(
                MERCADOPAGO_WEBHOOK_SECRET.encode(),
                data.encode(),
                hashlib.sha256,
            ).hexdigest()

            return signature == calculated_signature

        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}")
            return False

    @staticmethod
    def handle_webhook(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MercadoPago webhook event.

        Args:
            event_data: Webhook payload

        Returns:
            {
                "status": "processed" | "error",
                "type": str,
                "payment_id": str,
                "external_reference": str,
                "payment_status": str,
                "action_required": str
            }
        """
        try:
            event_type = event_data.get("type")
            data = event_data.get("data", {})

            logger.info(f"MercadoPago webhook: {event_type} | ID: {data.get('id')}")

            if event_type == "payment":
                return MercadoPagoWebhookHandler._handle_payment_event(data)
            elif event_type == "merchant_order":
                return MercadoPagoWebhookHandler._handle_merchant_order(data)
            else:
                logger.info(f"Unhandled event type: {event_type}")
                return {"status": "acknowledged", "type": event_type}

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _handle_payment_event(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment event from webhook."""
        payment_id = data.get("id")
        status = data.get("status")
        external_reference = data.get("external_reference")
        amount = data.get("transaction_amount", 0)

        logger.info(
            f"Payment event: {payment_id} | Status: {status} | "
            f"Reference: {external_reference} | Amount: ${amount}"
        )

        action_required = "none"
        if status == PaymentStatus.APPROVED:
            action_required = "update_order_paid"
        elif status == PaymentStatus.REJECTED:
            action_required = "notify_payment_failed"
        elif status == PaymentStatus.REFUNDED:
            action_required = "update_order_refunded"

        return {
            "status": "processed",
            "type": "payment",
            "payment_id": payment_id,
            "external_reference": external_reference,
            "payment_status": status,
            "amount": amount,
            "action_required": action_required,
        }

    @staticmethod
    def _handle_merchant_order(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle merchant order event from webhook."""
        order_id = data.get("id")
        reference = data.get("external_reference")
        payments = data.get("payments", [])

        # Check if all payments are approved
        all_approved = all(
            p.get("status") == PaymentStatus.APPROVED for p in payments
        )

        logger.info(f"Merchant order: {order_id} | Reference: {reference}")

        return {
            "status": "processed",
            "type": "merchant_order",
            "order_id": order_id,
            "external_reference": reference,
            "all_payments_approved": all_approved,
            "payments_count": len(payments),
            "action_required": "check_order_completion" if all_approved else "none",
        }
