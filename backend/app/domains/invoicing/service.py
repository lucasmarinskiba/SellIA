"""Invoicing services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.invoicing.models import Invoice, InvoiceTemplate, Payment

logger = get_logger(__name__)


class InvoicingService:
    """Manage invoices and payments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invoice(
        self,
        business_id: uuid.UUID,
        customer_id: Optional[uuid.UUID],
        amount_aed: Decimal,
        tax_aed: Decimal,
        due_date: datetime,
        items: Optional[list] = None,
        notes: Optional[str] = None,
    ) -> Invoice:
        """Create invoice."""
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        total_aed = amount_aed + tax_aed

        invoice = Invoice(
            business_id=business_id,
            customer_id=customer_id,
            invoice_number=invoice_number,
            amount_aed=amount_aed,
            tax_aed=tax_aed,
            total_aed=total_aed,
            due_date=due_date,
            items=items or [],
            notes=notes,
        )
        self.db.add(invoice)
        await self.db.commit()
        logger.info(f"Invoice created: {invoice_number}, {total_aed} AED")
        return invoice

    async def get_invoice(self, invoice_id: uuid.UUID) -> Invoice:
        """Fetch invoice."""
        invoice = (
            await self.db.execute(select(Invoice).where(Invoice.id == invoice_id))
        ).scalar_one_or_none()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        return invoice

    async def list_invoices(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[Invoice]:
        """List invoices."""
        query = select(Invoice).where(Invoice.business_id == business_id)
        if status:
            query = query.where(Invoice.status == status)
        query = query.order_by(desc(Invoice.created_at)).limit(limit)
        invoices = (await self.db.execute(query)).scalars().all()
        return invoices

    async def update_invoice(
        self,
        invoice_id: uuid.UUID,
        status: Optional[str] = None,
        due_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Invoice:
        """Update invoice."""
        invoice = await self.get_invoice(invoice_id)
        if status:
            invoice.status = status
        if due_date:
            invoice.due_date = due_date
        if notes:
            invoice.notes = notes
        await self.db.commit()
        return invoice

    async def send_invoice(self, invoice_id: uuid.UUID) -> Invoice:
        """Mark invoice as sent."""
        invoice = await self.get_invoice(invoice_id)
        invoice.status = "sent"
        invoice.sent_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.info(f"Invoice {invoice.invoice_number} sent")
        return invoice

    async def mark_viewed(self, invoice_id: uuid.UUID) -> Invoice:
        """Mark invoice as viewed."""
        invoice = await self.get_invoice(invoice_id)
        invoice.viewed_at = datetime.now(timezone.utc)
        await self.db.commit()
        return invoice

    async def invoice_stats(self, business_id: uuid.UUID) -> dict:
        """Get invoice statistics."""
        invoices = (
            await self.db.execute(
                select(Invoice).where(Invoice.business_id == business_id)
            )
        ).scalars().all()

        total_revenue = sum(inv.total_aed for inv in invoices)
        paid_revenue = sum(inv.total_aed for inv in invoices if inv.status == "paid")
        pending_revenue = sum(inv.total_aed for inv in invoices if inv.status in ("draft", "sent", "viewed"))
        overdue = sum(1 for inv in invoices if inv.status == "overdue")

        # Avg payment days
        paid_invoices = [inv for inv in invoices if inv.paid_at and inv.created_at]
        avg_payment_days = 0.0
        if paid_invoices:
            days = [
                (inv.paid_at - inv.created_at).days
                for inv in paid_invoices
                if inv.paid_at and inv.created_at
            ]
            avg_payment_days = sum(days) / len(days) if days else 0.0

        return {
            "total_invoices": len(invoices),
            "total_revenue_aed": float(total_revenue),
            "paid_revenue_aed": float(paid_revenue),
            "pending_revenue_aed": float(pending_revenue),
            "overdue_count": overdue,
            "avg_payment_days": avg_payment_days,
        }


class PaymentService:
    """Record and manage payments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_payment(
        self,
        invoice_id: uuid.UUID,
        amount_aed: Decimal,
        method: str,
        reference: Optional[str] = None,
    ) -> Payment:
        """Record payment for invoice."""
        invoice = (
            await self.db.execute(select(Invoice).where(Invoice.id == invoice_id))
        ).scalar_one_or_none()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        payment = Payment(
            invoice_id=invoice_id,
            business_id=invoice.business_id,
            amount_aed=amount_aed,
            method=method,
            reference=reference,
            status="completed",
        )
        self.db.add(payment)

        # Mark invoice as paid
        invoice.status = "paid"
        invoice.paid_at = datetime.now(timezone.utc)
        invoice.payment_method = method

        await self.db.commit()
        logger.info(f"Payment recorded for {invoice.invoice_number}: {amount_aed} AED")
        return payment

    async def get_payment(self, payment_id: uuid.UUID) -> Payment:
        """Fetch payment."""
        payment = (
            await self.db.execute(select(Payment).where(Payment.id == payment_id))
        ).scalar_one_or_none()
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        return payment

    async def list_payments(
        self,
        business_id: uuid.UUID,
        limit: int = 100,
    ) -> list[Payment]:
        """List payments."""
        payments = (
            await self.db.execute(
                select(Payment).where(Payment.business_id == business_id)
                .order_by(desc(Payment.paid_at)).limit(limit)
            )
        ).scalars().all()
        return payments


class InvoiceTemplateService:
    """Manage invoice templates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(
        self,
        business_id: uuid.UUID,
        name: str,
        template_html: str,
        is_default: bool = False,
    ) -> InvoiceTemplate:
        """Create invoice template."""
        template = InvoiceTemplate(
            business_id=business_id,
            name=name,
            template_html=template_html,
            is_default=is_default,
        )
        self.db.add(template)
        await self.db.commit()
        return template

    async def list_templates(self, business_id: uuid.UUID) -> list[InvoiceTemplate]:
        """List templates."""
        templates = (
            await self.db.execute(
                select(InvoiceTemplate).where(
                    and_(
                        InvoiceTemplate.business_id == business_id,
                        InvoiceTemplate.is_active,
                    )
                )
            )
        ).scalars().all()
        return templates

    async def get_template(self, template_id: uuid.UUID) -> InvoiceTemplate:
        """Fetch template."""
        template = (
            await self.db.execute(
                select(InvoiceTemplate).where(InvoiceTemplate.id == template_id)
            )
        ).scalar_one_or_none()
        if not template:
            raise ValueError(f"Template {template_id} not found")
        return template
