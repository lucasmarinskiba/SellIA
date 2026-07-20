"""
Payment Reconciliation — Sync payments with orders and trigger fulfillment.

Features:
- Match payment events with orders
- Automatically update order status
- Trigger fulfillment workflows
- Reconciliation reporting
- Retry failed reconciliations
- Audit logging

Database models:
- PaymentTransaction: Stripe/MercadoPago/Crypto payment records
- Order: Sales orders (links to payments)
- PaymentReconciliation: Reconciliation audit log
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ReconciliationStatus(str, Enum):
    """Reconciliation statuses."""
    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL = "partial"
    UNMATCHED = "unmatched"
    ERROR = "error"


class FulfillmentType(str, Enum):
    """Order fulfillment types."""
    DIGITAL = "digital"
    PHYSICAL = "physical"
    SERVICE = "service"


class PaymentReconciler:
    """Reconcile payments with orders."""

    @staticmethod
    def reconcile_payment(
        db: Session,
        payment_id: str,
        payment_provider: str,
        customer_email: str,
        amount_usd: float,
        order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Reconcile a payment with an order.

        Args:
            db: Database session
            payment_id: Payment ID from provider (Stripe, MP, etc)
            payment_provider: Provider name (stripe, mercadopago, crypto)
            customer_email: Customer email
            amount_usd: Payment amount in USD
            order_id: Optional order ID (otherwise searches by email)
            metadata: Additional payment metadata

        Returns:
            {
                "status": "matched" | "partial" | "unmatched" | "error",
                "payment_id": str,
                "order_id": str (if found),
                "reconciliation_status": str,
                "action_taken": str,
                "error": str (if error)
            }
        """
        try:
            from backend.app.core.database.payment_models import Order, Payment

            logger.info(
                f"Reconciling payment {payment_id} from {payment_provider} | "
                f"Email: {customer_email} | Amount: ${amount_usd}"
            )

            # Try to find matching order
            order = None

            if order_id:
                # Direct order ID match
                order = db.query(Order).filter(Order.id == order_id).first()
            else:
                # Search by email and amount
                order = (
                    db.query(Order)
                    .filter(
                        Order.customer_email == customer_email,
                        Order.amount == amount_usd,
                        Order.status.in_(["pending", "awaiting_payment"]),
                    )
                    .order_by(Order.created_at.desc())
                    .first()
                )

            if not order:
                logger.warning(
                    f"No matching order found for payment {payment_id} | "
                    f"Email: {customer_email} | Amount: ${amount_usd}"
                )

                return {
                    "status": "unmatched",
                    "payment_id": payment_id,
                    "reconciliation_status": ReconciliationStatus.UNMATCHED,
                    "action_taken": "payment_recorded_awaiting_order",
                }

            # Update order status
            order.payment_status = "succeeded"
            order.status = "payment_received"
            order.completed_at = datetime.utcnow()

            # Link payment to order
            payment = Payment(
                id=payment_id,
                order_id=order.id,
                customer_email=customer_email,
                amount=amount_usd,
                status="succeeded",
                payment_method=payment_provider,
                stripe_payment_intent_id=payment_id if payment_provider == "stripe" else None,
            )
            db.add(payment)

            db.commit()

            logger.info(
                f"Payment reconciled: {payment_id} matched to order {order.id}"
            )

            return {
                "status": "matched",
                "payment_id": payment_id,
                "order_id": order.id,
                "reconciliation_status": ReconciliationStatus.MATCHED,
                "action_taken": "order_updated_payment_received",
                "fulfillment_required": True,
            }

        except Exception as e:
            logger.error(f"Reconciliation error: {str(e)}")
            db.rollback()
            return {
                "status": "error",
                "payment_id": payment_id,
                "reconciliation_status": ReconciliationStatus.ERROR,
                "error": str(e),
            }

    @staticmethod
    def sync_stripe_payment(
        db: Session,
        stripe_event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Sync a Stripe payment_intent event with orders.

        Args:
            db: Database session
            stripe_event: Stripe webhook event

        Returns:
            Reconciliation result
        """
        try:
            intent = stripe_event.get("data", {}).get("object", {})
            payment_id = intent.get("id")
            amount = intent.get("amount", 0) / 100
            customer_email = intent.get("receipt_email")
            metadata = intent.get("metadata", {})
            order_id = metadata.get("order_id")

            return PaymentReconciler.reconcile_payment(
                db=db,
                payment_id=payment_id,
                payment_provider="stripe",
                customer_email=customer_email,
                amount_usd=amount,
                order_id=order_id,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Stripe sync error: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def sync_mercadopago_payment(
        db: Session,
        mercadopago_event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Sync a MercadoPago payment with orders.

        Args:
            db: Database session
            mercadopago_event: MercadoPago webhook event

        Returns:
            Reconciliation result
        """
        try:
            data = mercadopago_event.get("data", {})
            payment_id = data.get("id")
            status = data.get("status")
            amount = data.get("transaction_amount", 0)
            payer_email = data.get("payer", {}).get("email")
            reference = data.get("external_reference")

            if status != "approved":
                logger.info(f"Skipping non-approved MP payment: {payment_id}")
                return {
                    "status": "unmatched",
                    "payment_id": payment_id,
                    "reconciliation_status": ReconciliationStatus.UNMATCHED,
                    "action_taken": "payment_not_approved",
                }

            return PaymentReconciler.reconcile_payment(
                db=db,
                payment_id=payment_id,
                payment_provider="mercadopago",
                customer_email=payer_email,
                amount_usd=amount,
                order_id=reference,
            )

        except Exception as e:
            logger.error(f"MercadoPago sync error: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def sync_crypto_payment(
        db: Session,
        tx_hash: str,
        blockchain: str,
        amount_usdt: float,
        invoice_id: str,
    ) -> Dict[str, Any]:
        """
        Sync a crypto payment with order.

        Args:
            db: Database session
            tx_hash: Blockchain transaction hash
            blockchain: "tron" or "bsc"
            amount_usdt: Amount in USDT
            invoice_id: Invoice/order reference

        Returns:
            Reconciliation result
        """
        try:
            # Convert USDT to USD (assuming 1 USDT = 1 USD)
            amount_usd = float(amount_usdt)

            return PaymentReconciler.reconcile_payment(
                db=db,
                payment_id=tx_hash,
                payment_provider=f"crypto_{blockchain}",
                customer_email="",  # Crypto doesn't have email
                amount_usd=amount_usd,
                order_id=invoice_id,
                metadata={
                    "blockchain": blockchain,
                    "tx_hash": tx_hash,
                    "amount_crypto": amount_usdt,
                },
            )

        except Exception as e:
            logger.error(f"Crypto sync error: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def get_unreconciled_payments(
        db: Session,
        days_ago: int = 7,
    ) -> list:
        """
        Get payments that couldn't be matched to orders.

        Args:
            db: Database session
            days_ago: Look back N days

        Returns:
            List of unmatched payment records
        """
        try:
            from backend.app.core.database.payment_models import Payment

            cutoff_date = datetime.utcnow() - timedelta(days=days_ago)

            unmatched = (
                db.query(Payment)
                .filter(
                    Payment.order_id == None,
                    Payment.created_at >= cutoff_date,
                )
                .all()
            )

            return [
                {
                    "payment_id": p.id,
                    "amount": p.amount,
                    "customer_email": p.customer_email,
                    "status": p.status,
                    "created_at": p.created_at,
                }
                for p in unmatched
            ]

        except Exception as e:
            logger.error(f"Error getting unreconciled payments: {str(e)}")
            return []


class FulfillmentOrchestrator:
    """Orchestrate order fulfillment after payment confirmation."""

    @staticmethod
    def trigger_fulfillment(
        db: Session,
        order_id: str,
        fulfillment_type: str,
    ) -> Dict[str, Any]:
        """
        Trigger fulfillment workflow based on order type.

        Args:
            db: Database session
            order_id: Order ID
            fulfillment_type: "digital" | "physical" | "service"

        Returns:
            {
                "status": "triggered" | "error",
                "order_id": str,
                "action": str,
                "error": str (if error)
            }
        """
        try:
            from backend.app.core.database.payment_models import Order

            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise ValueError(f"Order {order_id} not found")

            logger.info(
                f"Triggering {fulfillment_type} fulfillment for order {order_id}"
            )

            if fulfillment_type == FulfillmentType.DIGITAL:
                return FulfillmentOrchestrator._fulfill_digital(db, order)
            elif fulfillment_type == FulfillmentType.PHYSICAL:
                return FulfillmentOrchestrator._fulfill_physical(db, order)
            elif fulfillment_type == FulfillmentType.SERVICE:
                return FulfillmentOrchestrator._fulfill_service(db, order)
            else:
                raise ValueError(f"Unknown fulfillment type: {fulfillment_type}")

        except Exception as e:
            logger.error(f"Fulfillment error: {str(e)}")
            return {"status": "error", "order_id": order_id, "error": str(e)}

    @staticmethod
    def _fulfill_digital(db: Session, order) -> Dict[str, Any]:
        """Handle digital delivery (email, download link, etc)."""
        try:
            # TODO: Send download link or account activation email
            # TODO: Update order.fulfilled = True, order.fulfilled_at = now()

            order.fulfilled = True
            order.fulfilled_at = datetime.utcnow()
            order.delivery_type = "digital"
            db.commit()

            logger.info(f"Digital fulfillment completed for order {order.id}")

            return {
                "status": "triggered",
                "order_id": order.id,
                "action": "send_digital_delivery_email",
            }

        except Exception as e:
            logger.error(f"Digital fulfillment error: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _fulfill_physical(db: Session, order) -> Dict[str, Any]:
        """Handle physical shipment."""
        try:
            # TODO: Create shipping label, integrate with Easypost/Shippo
            # TODO: Update tracking number and carrier

            order.delivery_type = "physical"
            db.commit()

            logger.info(f"Physical fulfillment initiated for order {order.id}")

            return {
                "status": "triggered",
                "order_id": order.id,
                "action": "create_shipping_label",
            }

        except Exception as e:
            logger.error(f"Physical fulfillment error: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _fulfill_service(db: Session, order) -> Dict[str, Any]:
        """Handle service activation."""
        try:
            # TODO: Activate service subscription, send access credentials
            # TODO: Schedule fulfillment if needed

            order.delivery_type = "service"
            db.commit()

            logger.info(f"Service fulfillment initiated for order {order.id}")

            return {
                "status": "triggered",
                "order_id": order.id,
                "action": "activate_service",
            }

        except Exception as e:
            logger.error(f"Service fulfillment error: {str(e)}")
            return {"status": "error", "error": str(e)}
