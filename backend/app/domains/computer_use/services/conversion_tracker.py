"""Conversion Tracker — Track sales + payments + generate checkout links.

Pipeline:
1. Sale cerrada → crear payment intent en Stripe
2. Enviar checkout link al cliente
3. Monitorear pago
4. Guardar resultado en BD
5. Feedback loop para optimización
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.computer_use.integrations import (
    StripeConnector,
    get_stripe_connector,
)
from app.domains.computer_use.services.audit_log_service import AuditLogEntry, AuditLogService
from app.domains.computer_use.services.webhook_receiver import IncomingMessage
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConversionTracker:
    """Rastrear conversiones y procesar pagos automáticamente."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditLogService(db)

        # Stripe connector
        self.stripe_connector = (
            get_stripe_connector(api_key=settings.STRIPE_SECRET_KEY)
            if hasattr(settings, 'STRIPE_SECRET_KEY') else None
        )

    async def process_sale_to_payment(
        self,
        user_id: str,
        customer_id: str,
        customer_email: str,
        customer_name: str,
        product_info: Dict[str, Any],
        amount_cents: int,
        success_url: str = "https://yoursite.com/success",
        cancel_url: str = "https://yoursite.com/cancel",
    ) -> Tuple[bool, Optional[str]]:
        """
        Crea checkout session en Stripe → envía link al cliente.

        Retorna: (success, checkout_url)
        """
        if not self.stripe_connector:
            logger.warning("Stripe connector not configured")
            return False, None

        try:
            # Crear checkout session
            success, checkout_url = await self.stripe_connector.create_checkout_session(
                customer_email=customer_email,
                product_name=product_info.get("name", "Product"),
                amount_cents=amount_cents,
                success_url=success_url,
                cancel_url=cancel_url,
                customer_name=customer_name,
            )

            if not success:
                logger.error(f"Failed to create checkout session for {customer_id}")
                return False, None

            # Log conversion attempt
            log_entry = AuditLogEntry(
                user_id=user_id,
                platform="stripe",
                action_type="payment_checkout_created",
            )

            log_entry.with_input(f"${amount_cents / 100} checkout for {customer_email}")
            log_entry.with_output(checkout_url)
            log_entry.with_agent("stripe_connector")
            log_entry.with_confidence(1.0)
            log_entry.success()

            log_entry.with_metadata({
                "customer_id": customer_id,
                "customer_email": customer_email,
                "product_id": product_info.get("id"),
                "amount": amount_cents / 100,
            })

            await self.audit_service.log(log_entry)

            logger.info(f"Checkout session created: {customer_id} | ${amount_cents / 100}")

            return True, checkout_url

        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            await self._log_error(
                user_id=user_id,
                action="payment_checkout_failed",
                error_msg=str(e),
                customer_id=customer_id,
            )
            return False, None

    async def verify_payment_status(self, session_id: str) -> Dict[str, Any]:
        """Verifica status de pago en Stripe."""
        if not self.stripe_connector:
            return {}

        try:
            return await self.stripe_connector.get_payment_status(session_id)
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            return {}

    async def handle_payment_webhook(
        self,
        user_id: str,
        event_type: str,  # checkout.session.completed, payment_intent.succeeded
        event_data: Dict[str, Any],
    ) -> None:
        """Maneja webhooks de Stripe."""
        try:
            log_entry = AuditLogEntry(
                user_id=user_id,
                platform="stripe",
                action_type=f"webhook_{event_type}",
            )

            log_entry.with_input(str(event_data))

            if event_type == "checkout.session.completed":
                # Venta cerrada → registrar
                customer_email = event_data.get("customer_email")
                amount_total = event_data.get("amount_total", 0) / 100

                log_entry.with_output(f"Payment confirmed: ${amount_total}")
                log_entry.with_confidence(1.0)
                log_entry.success()

                log_entry.with_metadata({
                    "customer_email": customer_email,
                    "amount": amount_total,
                    "session_id": event_data.get("id"),
                })

                logger.info(f"Payment confirmed: {customer_email} | ${amount_total}")

            elif event_type == "charge.failed":
                # Pago falló
                log_entry.with_output("Payment failed")
                log_entry.failed(f"Charge failed: {event_data.get('failure_message')}")

            await self.audit_service.log(log_entry)

        except Exception as e:
            logger.error(f"Error handling payment webhook: {e}")

    async def _log_error(
        self,
        user_id: str,
        action: str,
        error_msg: str,
        customer_id: Optional[str] = None,
    ) -> None:
        """Log error to audit trail."""
        try:
            log_entry = AuditLogEntry(
                user_id=user_id,
                platform="payment",
                action_type=action,
            )

            log_entry.with_input(f"customer_id: {customer_id}")
            log_entry.failed(error_msg)

            await self.audit_service.log(log_entry)

        except Exception as e:
            logger.error(f"Error logging error: {e}")


def get_conversion_tracker(db: AsyncSession) -> ConversionTracker:
    return ConversionTracker(db)
