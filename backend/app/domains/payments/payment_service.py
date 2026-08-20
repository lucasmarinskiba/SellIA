"""Payment service layer."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, Dict, List, Any
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.domains.payments.payment_models import (
    Transaction, Refund, Settlement, PaymentReconciliation, PaymentMetrics,
    TransactionStatus, RefundStatus, PaymentMethod
)
from app.core.payments.mercadopago_processor import MercadoPagoProcessor

logger = logging.getLogger(__name__)


class PaymentService:
    """Payment operations."""

    @staticmethod
    def create_transaction(
        business_id: UUID,
        amount: Decimal,
        currency: str,
        method: str,
        customer_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        description: Optional[str] = None,
        reference_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        db: Session = None
    ) -> dict:
        """Create payment transaction."""
        if not db:
            raise ValueError("Database session required")

        transaction = Transaction(
            business_id=business_id,
            amount=amount,
            currency=currency,
            method=method,
            customer_id=customer_id,
            order_id=order_id,
            location_id=location_id,
            description=description,
            reference_id=reference_id,
            transaction_metadata=metadata or {},
            status=TransactionStatus.PENDING
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(f"Transaction created: {transaction.id} | Amount: {amount} {currency}")

        return {
            "transaction_id": str(transaction.id),
            "status": transaction.status,
            "amount": float(amount),
            "currency": currency,
        }

    @staticmethod
    def create_mercadopago_checkout(
        business_id: UUID,
        customer_email: str,
        customer_name: str,
        items: List[Dict],
        amount: Decimal,
        currency: str = "USD",
        order_id: Optional[UUID] = None,
        db: Session = None
    ) -> dict:
        """Create MercadoPago checkout preference."""
        if not db:
            raise ValueError("Database session required")

        # Create transaction record
        transaction = Transaction(
            business_id=business_id,
            amount=amount,
            currency=currency,
            method=PaymentMethod.MERCADOPAGO,
            order_id=order_id,
            status=TransactionStatus.PROCESSING,
            metadata={"items": items}
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Create MercadoPago preference
        mp_result = MercadoPagoProcessor.create_checkout_preference(
            external_reference=str(transaction.id),
            customer_email=customer_email,
            customer_name=customer_name,
            items=items,
            currency_code=currency
        )

        if mp_result.get("status") == "error":
            transaction.status = TransactionStatus.FAILED
            db.commit()
            return {"status": "error", "error": mp_result.get("error")}

        # Update transaction with MercadoPago data
        transaction.mercadopago_preference_id = mp_result.get("preference_id")
        db.commit()

        logger.info(f"MercadoPago checkout created: {mp_result.get('preference_id')}")

        return {
            "status": "checkout_created",
            "transaction_id": str(transaction.id),
            "preference_id": mp_result.get("preference_id"),
            "checkout_url": mp_result.get("checkout_url"),
        }

    @staticmethod
    def process_mercadopago_webhook(
        business_id: UUID,
        event_data: Dict,
        db: Session = None
    ) -> dict:
        """Process MercadoPago webhook notification."""
        if not db:
            raise ValueError("Database session required")

        event_type = event_data.get("type")
        data = event_data.get("data", {})
        payment_id = data.get("id")

        logger.info(f"Processing MercadoPago webhook: {event_type} | Payment: {payment_id}")

        if event_type == "payment":
            return PaymentService._handle_payment_webhook(business_id, data, db)
        elif event_type == "merchant_order":
            return PaymentService._handle_merchant_order_webhook(business_id, data, db)

        return {"status": "acknowledged"}

    @staticmethod
    def _handle_payment_webhook(business_id: UUID, data: Dict, db: Session) -> dict:
        """Handle payment webhook."""
        payment_id = data.get("id")
        status = data.get("status")
        amount = data.get("transaction_amount", 0)
        external_reference = data.get("external_reference")

        # Find transaction by external reference
        transaction = db.query(Transaction).filter(
            Transaction.id == UUID(external_reference) if external_reference else None
        ).first()

        if not transaction:
            logger.warning(f"Transaction not found for payment {payment_id}")
            return {"status": "error", "error": "Transaction not found"}

        # Update transaction
        transaction.mercadopago_payment_id = payment_id
        transaction.mercadopago_status = status
        transaction.webhook_notification_received = True
        transaction.webhook_notification_date = datetime.now(timezone.utc)

        # Update status based on payment status
        if status == "approved":
            transaction.status = TransactionStatus.APPROVED
            transaction.approved_at = datetime.now(timezone.utc)
        elif status in ("rejected", "failed"):
            transaction.status = TransactionStatus.REJECTED
        elif status == "pending":
            transaction.status = TransactionStatus.PENDING

        db.commit()

        logger.info(f"Transaction {transaction.id} updated to status: {transaction.status}")

        return {
            "status": "processed",
            "transaction_id": str(transaction.id),
            "payment_status": status,
        }

    @staticmethod
    def _handle_merchant_order_webhook(business_id: UUID, data: Dict, db: Session) -> dict:
        """Handle merchant order webhook."""
        order_id = data.get("id")
        external_reference = data.get("external_reference")

        logger.info(f"Merchant order webhook: {order_id} | Reference: {external_reference}")

        return {"status": "processed", "order_id": order_id}

    @staticmethod
    def create_refund(
        transaction_id: UUID,
        business_id: UUID,
        amount: Decimal,
        reason: str,
        db: Session = None
    ) -> dict:
        """Create refund request."""
        if not db:
            raise ValueError("Database session required")

        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.business_id == business_id
        ).first()

        if not transaction:
            return {"status": "error", "error": "Transaction not found"}

        if transaction.status != TransactionStatus.APPROVED:
            return {"status": "error", "error": "Can only refund approved transactions"}

        # Create refund record
        refund = Refund(
            transaction_id=transaction_id,
            business_id=business_id,
            amount=amount,
            reason=reason,
            status=RefundStatus.REQUESTED
        )

        db.add(refund)

        # Process refund via MercadoPago if available
        if transaction.mercadopago_payment_id:
            mp_result = MercadoPagoProcessor.refund_payment(
                transaction.mercadopago_payment_id,
                float(amount)
            )

            if mp_result.get("status") == "refunded":
                refund.mercadopago_refund_id = mp_result.get("refund_id")
                refund.status = RefundStatus.APPROVED
                refund.processed_at = datetime.now(timezone.utc)

                # Update transaction status
                if amount == transaction.amount:
                    transaction.status = TransactionStatus.REFUNDED
                else:
                    transaction.status = TransactionStatus.PARTIAL_REFUND

        db.commit()

        logger.info(f"Refund created: {refund.id} | Transaction: {transaction_id}")

        return {
            "refund_id": str(refund.id),
            "status": refund.status,
            "amount": float(amount),
        }

    @staticmethod
    def reconcile_transaction(
        order_id: UUID,
        transaction_id: Optional[UUID],
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Reconcile order with payment transaction."""
        if not db:
            raise ValueError("Database session required")

        # Find matching transaction if not provided
        if not transaction_id:
            # Try to match by order_id
            transaction = db.query(Transaction).filter(
                Transaction.order_id == order_id,
                Transaction.business_id == business_id,
                Transaction.status == TransactionStatus.APPROVED
            ).first()

            if not transaction:
                return {"status": "error", "error": "No matching transaction found"}

            transaction_id = transaction.id

        # Create reconciliation record
        reconciliation = PaymentReconciliation(
            business_id=business_id,
            order_id=order_id,
            transaction_id=transaction_id,
            status="matched",
            matched=True,
            match_confidence=100,
            match_reason="manual"
        )

        db.add(reconciliation)
        db.commit()

        logger.info(f"Order {order_id} reconciled with transaction {transaction_id}")

        return {
            "reconciliation_id": str(reconciliation.id),
            "status": "matched",
            "order_id": str(order_id),
            "transaction_id": str(transaction_id),
        }

    @staticmethod
    def get_transactions(
        business_id: UUID,
        status: Optional[str] = None,
        location_id: Optional[UUID] = None,
        limit: int = 50,
        db: Session = None
    ) -> List[dict]:
        """Get transactions."""
        if not db:
            raise ValueError("Database session required")

        query = db.query(Transaction).filter(
            Transaction.business_id == business_id
        )

        if status:
            query = query.filter(Transaction.status == status)

        if location_id:
            query = query.filter(Transaction.location_id == location_id)

        transactions = query.order_by(desc(Transaction.created_at)).limit(limit).all()

        return [
            {
                "transaction_id": str(t.id),
                "amount": float(t.amount),
                "currency": t.currency,
                "method": t.method,
                "status": t.status,
                "order_id": str(t.order_id) if t.order_id else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "approved_at": t.approved_at.isoformat() if t.approved_at else None,
            }
            for t in transactions
        ]

    @staticmethod
    def get_settlement_metrics(
        business_id: UUID,
        period_days: int = 30,
        db: Session = None
    ) -> dict:
        """Get settlement metrics for period."""
        if not db:
            raise ValueError("Database session required")

        start_date = datetime.now(timezone.utc) - timedelta(days=period_days)

        transactions = db.query(Transaction).filter(
            Transaction.business_id == business_id,
            Transaction.status == TransactionStatus.APPROVED,
            Transaction.created_at >= start_date
        ).all()

        total_amount = sum(t.amount for t in transactions)
        total_fees = sum(t.gateway_fee or 0 for t in transactions)
        net_amount = total_amount - total_fees

        refunds = db.query(Refund).filter(
            Refund.business_id == business_id,
            Refund.status == RefundStatus.COMPLETED,
            Refund.created_at >= start_date
        ).all()

        total_refunded = sum(r.amount for r in refunds)
        net_after_refunds = net_amount - total_refunded

        return {
            "period_days": period_days,
            "total_transactions": len(transactions),
            "total_amount": float(total_amount),
            "total_fees": float(total_fees),
            "net_amount": float(net_amount),
            "total_refunded": float(total_refunded),
            "net_after_refunds": float(net_after_refunds),
            "success_rate": (len([t for t in transactions if t.status == TransactionStatus.APPROVED]) / len(transactions) * 100) if transactions else 0,
        }

    @staticmethod
    def get_payment_metrics(
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Get payment metrics."""
        if not db:
            raise ValueError("Database session required")

        metrics = db.query(PaymentMetrics).filter(
            PaymentMetrics.business_id == business_id
        ).first()

        if not metrics:
            return {"message": "No metrics found"}

        return {
            "total_transactions": metrics.total_transactions,
            "total_revenue": float(metrics.total_revenue),
            "avg_transaction_value": float(metrics.avg_transaction_value),
            "success_rate": metrics.success_rate,
            "failed_transactions": metrics.failed_transactions,
            "refund_rate": metrics.refund_rate,
            "total_fees": float(metrics.total_fees),
            "total_settled": float(metrics.total_settled),
            "pending_settlement": float(metrics.pending_settlement),
            "transactions_7d": metrics.transactions_7d,
            "revenue_7d": float(metrics.revenue_7d),
        }
