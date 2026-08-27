"""Payment service layer.

NOTE: rewritten to async — `app.core.database.get_db` yields an AsyncSession,
not a sync `Session`. The previous version called `db.query(...)` and
`db.commit()` without `await`, which raises `AttributeError` /
silently drops commits against an AsyncSession. Every DB call here now
goes through `select()` + `await db.execute()` / `await db.commit()`.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, Dict, List, Any
from decimal import Decimal

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.payments.payment_models import (
    Transaction, Refund, Settlement, PaymentReconciliation, PaymentMetrics,
    TransactionStatus, RefundStatus, PaymentMethod
)
from app.core.payments.mercadopago_processor import MercadoPagoProcessor

logger = logging.getLogger(__name__)

# Backend's own public URL, used so MercadoPago calls back the
# business-scoped webhook (/api/v1/businesses/{business_id}/webhooks/mercadopago)
# instead of the generic global one.
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "https://sellia-production.up.railway.app")


class PaymentService:
    """Payment operations."""

    @staticmethod
    async def create_transaction(
        business_id: UUID,
        amount: Decimal,
        currency: str,
        method: str,
        customer_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        description: Optional[str] = None,
        reference_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        db: AsyncSession = None
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
            conversation_id=conversation_id,
            description=description,
            reference_id=reference_id,
            transaction_metadata=metadata or {},
            status=TransactionStatus.PENDING
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        logger.info(f"Transaction created: {transaction.id} | Amount: {amount} {currency}")

        return {
            "transaction_id": str(transaction.id),
            "status": transaction.status,
            "amount": float(amount),
            "currency": currency,
        }

    @staticmethod
    async def create_mercadopago_checkout(
        business_id: UUID,
        customer_email: str,
        customer_name: str,
        items: List[Dict],
        amount: Decimal,
        currency: str = "USD",
        order_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        db: AsyncSession = None
    ) -> dict:
        """Create MercadoPago checkout preference.

        `items` is a list of {name, quantity, unit_price} — used both for the
        MercadoPago preference and stored as transaction_metadata for audit.
        """
        if not db:
            raise ValueError("Database session required")

        # Create transaction record
        transaction = Transaction(
            business_id=business_id,
            amount=amount,
            currency=currency,
            method=PaymentMethod.MERCADOPAGO,
            order_id=order_id,
            conversation_id=conversation_id,
            status=TransactionStatus.PROCESSING,
            transaction_metadata={"items": items},
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        # Create MercadoPago preference — notification_url points at the
        # business-scoped webhook so the payment status flows back to the
        # right conversation/business instead of a generic global endpoint.
        notification_url = f"{BACKEND_PUBLIC_URL}/api/v1/businesses/{business_id}/webhooks/mercadopago"
        # MercadoPagoProcessor uses the blocking `requests` lib — push it off
        # the event loop so one checkout call doesn't stall every other
        # request the server is handling concurrently.
        mp_result = await asyncio.to_thread(
            MercadoPagoProcessor.create_checkout_preference,
            external_reference=str(transaction.id),
            customer_email=customer_email,
            customer_name=customer_name,
            items=items,
            currency_code=currency,
            notification_url=notification_url,
        )

        if mp_result.get("status") == "error":
            transaction.status = TransactionStatus.FAILED
            await db.commit()
            return {"status": "error", "error": mp_result.get("error")}

        # Update transaction with MercadoPago data
        transaction.mercadopago_preference_id = mp_result.get("preference_id")
        await db.commit()

        logger.info(f"MercadoPago checkout created: {mp_result.get('preference_id')}")

        return {
            "status": "checkout_created",
            "transaction_id": str(transaction.id),
            "preference_id": mp_result.get("preference_id"),
            "checkout_url": mp_result.get("checkout_url"),
        }

    @staticmethod
    async def process_mercadopago_webhook(
        business_id: UUID,
        event_data: Dict,
        db: AsyncSession = None
    ) -> dict:
        """Process MercadoPago webhook notification."""
        if not db:
            raise ValueError("Database session required")

        event_type = event_data.get("type")
        data = event_data.get("data", {})
        payment_id = data.get("id")

        logger.info(f"Processing MercadoPago webhook: {event_type} | Payment: {payment_id}")

        if event_type == "payment":
            return await PaymentService._handle_payment_webhook(business_id, data, db)
        elif event_type == "merchant_order":
            return await PaymentService._handle_merchant_order_webhook(business_id, data, db)

        return {"status": "acknowledged"}

    @staticmethod
    async def _handle_payment_webhook(business_id: UUID, data: Dict, db: AsyncSession) -> dict:
        """Handle payment webhook."""
        payment_id = data.get("id")
        status = data.get("status")
        external_reference = data.get("external_reference")

        if not external_reference:
            logger.warning(f"Payment webhook missing external_reference (payment {payment_id})")
            return {"status": "error", "error": "Missing external_reference"}

        try:
            transaction_uuid = UUID(external_reference)
        except (ValueError, TypeError):
            logger.warning(f"Payment webhook external_reference is not a UUID: {external_reference}")
            return {"status": "error", "error": "Invalid external_reference"}

        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_uuid)
        )
        transaction = result.scalar_one_or_none()

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

        await db.commit()

        logger.info(f"Transaction {transaction.id} updated to status: {transaction.status}")

        return {
            "status": "processed",
            "transaction_id": str(transaction.id),
            "conversation_id": str(transaction.conversation_id) if transaction.conversation_id else None,
            "payment_status": status,
        }

    @staticmethod
    async def _handle_merchant_order_webhook(business_id: UUID, data: Dict, db: AsyncSession) -> dict:
        """Handle merchant order webhook."""
        order_id = data.get("id")
        external_reference = data.get("external_reference")

        logger.info(f"Merchant order webhook: {order_id} | Reference: {external_reference}")

        return {"status": "processed", "order_id": order_id}

    @staticmethod
    async def create_refund(
        transaction_id: UUID,
        business_id: UUID,
        amount: Decimal,
        reason: str,
        db: AsyncSession = None
    ) -> dict:
        """Create refund request."""
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.business_id == business_id,
            )
        )
        transaction = result.scalar_one_or_none()

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
            mp_result = await asyncio.to_thread(
                MercadoPagoProcessor.refund_payment,
                transaction.mercadopago_payment_id,
                float(amount),
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

        await db.commit()
        await db.refresh(refund)

        logger.info(f"Refund created: {refund.id} | Transaction: {transaction_id}")

        return {
            "refund_id": str(refund.id),
            "status": refund.status,
            "amount": float(amount),
        }

    @staticmethod
    async def reconcile_transaction(
        order_id: UUID,
        transaction_id: Optional[UUID],
        business_id: UUID,
        db: AsyncSession = None
    ) -> dict:
        """Reconcile order with payment transaction."""
        if not db:
            raise ValueError("Database session required")

        # Find matching transaction if not provided
        if not transaction_id:
            result = await db.execute(
                select(Transaction).where(
                    Transaction.order_id == order_id,
                    Transaction.business_id == business_id,
                    Transaction.status == TransactionStatus.APPROVED,
                )
            )
            transaction = result.scalar_one_or_none()

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
        await db.commit()
        await db.refresh(reconciliation)

        logger.info(f"Order {order_id} reconciled with transaction {transaction_id}")

        return {
            "reconciliation_id": str(reconciliation.id),
            "status": "matched",
            "order_id": str(order_id),
            "transaction_id": str(transaction_id),
        }

    @staticmethod
    async def get_transactions(
        business_id: UUID,
        status: Optional[str] = None,
        location_id: Optional[UUID] = None,
        limit: int = 50,
        db: AsyncSession = None
    ) -> List[dict]:
        """Get transactions."""
        if not db:
            raise ValueError("Database session required")

        stmt = select(Transaction).where(Transaction.business_id == business_id)

        if status:
            stmt = stmt.where(Transaction.status == status)

        if location_id:
            stmt = stmt.where(Transaction.location_id == location_id)

        stmt = stmt.order_by(desc(Transaction.created_at)).limit(limit)

        result = await db.execute(stmt)
        transactions = result.scalars().all()

        return [
            {
                "transaction_id": str(t.id),
                "amount": float(t.amount),
                "currency": t.currency,
                "method": t.method,
                "status": t.status,
                "order_id": str(t.order_id) if t.order_id else None,
                "conversation_id": str(t.conversation_id) if t.conversation_id else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "approved_at": t.approved_at.isoformat() if t.approved_at else None,
            }
            for t in transactions
        ]

    @staticmethod
    async def get_settlement_metrics(
        business_id: UUID,
        period_days: int = 30,
        db: AsyncSession = None
    ) -> dict:
        """Get settlement metrics for period."""
        if not db:
            raise ValueError("Database session required")

        start_date = datetime.now(timezone.utc) - timedelta(days=period_days)

        result = await db.execute(
            select(Transaction).where(
                Transaction.business_id == business_id,
                Transaction.status == TransactionStatus.APPROVED,
                Transaction.created_at >= start_date,
            )
        )
        transactions = result.scalars().all()

        total_amount = sum(t.amount for t in transactions)
        total_fees = sum(t.gateway_fee or 0 for t in transactions)
        net_amount = total_amount - total_fees

        refunds_result = await db.execute(
            select(Refund).where(
                Refund.business_id == business_id,
                Refund.status == RefundStatus.COMPLETED,
                Refund.created_at >= start_date,
            )
        )
        refunds = refunds_result.scalars().all()

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
    async def get_payment_metrics(
        business_id: UUID,
        db: AsyncSession = None
    ) -> dict:
        """Get payment metrics."""
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(PaymentMetrics).where(PaymentMetrics.business_id == business_id)
        )
        metrics = result.scalar_one_or_none()

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
