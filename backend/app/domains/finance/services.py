"""Finance Services — Invoicing, Payment Reminders, AR."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.domains.finance.models import SalesInvoice, PaymentReminder, AccountsReceivableSnapshot, TaxConfig
from app.domains.finance.autopilot import FinanceAutopilotEngine
from app.domains.orders.models import Order
from app.core.logger import get_logger

logger = get_logger(__name__)


class FinanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invoice(self, business_id: UUID, **kwargs) -> SalesInvoice:
        inv = SalesInvoice(business_id=business_id, **kwargs)
        self.db.add(inv)
        await self.db.commit()
        await self.db.refresh(inv)
        return inv

    async def get_invoices(self, business_id: UUID, status: str | None = None):
        q = select(SalesInvoice).where(
            SalesInvoice.business_id == business_id,
        )
        if status:
            q = q.where(SalesInvoice.status == status)
        q = q.order_by(SalesInvoice.created_at.desc())
        result = await self.db.execute(q)
        return result.scalars().all()

    async def create_payment_reminder(self, business_id: UUID, order_id: UUID, **kwargs) -> PaymentReminder:
        reminder = PaymentReminder(business_id=business_id, order_id=order_id, **kwargs)
        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder

    async def get_pending_reminders(self, business_id: UUID):
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(PaymentReminder).where(
                PaymentReminder.business_id == business_id,
                PaymentReminder.status == 'pending',
                PaymentReminder.scheduled_at <= now,
            )
        )
        return result.scalars().all()

    async def generate_ar_snapshot(self, business_id: UUID) -> AccountsReceivableSnapshot:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(
                func.count(SalesInvoice.id),
                func.sum(SalesInvoice.total_amount - SalesInvoice.paid_amount),
            ).where(
                SalesInvoice.business_id == business_id,
                SalesInvoice.status.in_(['sent', 'overdue']),
            )
        )
        invoice_count, total_outstanding = result.one() or (0, Decimal('0'))

        overdue_result = await self.db.execute(
            select(
                func.count(SalesInvoice.id),
                func.sum(SalesInvoice.total_amount - SalesInvoice.paid_amount),
            ).where(
                SalesInvoice.business_id == business_id,
                SalesInvoice.status == 'overdue',
            )
        )
        overdue_count, total_overdue = overdue_result.one() or (0, Decimal('0'))

        snap = AccountsReceivableSnapshot(
            business_id=business_id,
            snapshot_date=now,
            total_outstanding=total_outstanding or Decimal('0'),
            total_overdue=total_overdue or Decimal('0'),
            invoice_count=invoice_count or 0,
            overdue_count=overdue_count or 0,
        )
        self.db.add(snap)
        await self.db.commit()
        return snap

    async def get_tax_config(self, business_id: UUID) -> TaxConfig | None:
        result = await self.db.execute(
            select(TaxConfig).where(TaxConfig.business_id == business_id)
        )
        return result.scalar_one_or_none()

    async def trigger_auto_delivery(self, business_id: UUID) -> dict:
        engine = FinanceAutopilotEngine(self.db)
        return await engine.auto_deliver_invoices(business_id)

    async def trigger_dunning(self, business_id: UUID) -> dict:
        engine = FinanceAutopilotEngine(self.db)
        return await engine.run_dunning_sequence(business_id)
