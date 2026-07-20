"""Finance Autopilot Engine.

Automated invoice delivery, dunning/collections, cash flow forecasting,
and tax reports for SellIA businesses.
"""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.finance.models import (
    SalesInvoice,
    PaymentReminder,
    AccountsReceivableSnapshot,
    TaxConfig,
    FinanceAutopilotConfig,
)
from app.domains.orders.models import Order, PaymentStatus
from app.domains.crm.models import Deal, LeadStage
from app.domains.channels.models import Conversation
from app.core.logger import get_logger

logger = get_logger(__name__)

DUNNING_MESSAGES = {
    1: {
        'whatsapp': 'Hola! Recordatorio amable: tu factura #{invoice_number} por ${amount} vence el {due_date}. Podés pagar aquí: {payment_link}',
        'email': 'Hola {customer_name},\n\nRecordatorio amable: tu factura #{invoice_number} por ${amount} vence el {due_date}.\n\nPodés pagar aquí: {payment_link}\n\nGracias!',
    },
    2: {
        'whatsapp': 'Tu factura #{invoice_number} por ${amount} venció hace 3 días. Por favor regularizá tu pago aquí: {payment_link}',
        'email': 'Hola {customer_name},\n\nTu factura #{invoice_number} por ${amount} venció hace 3 días.\n\nPor favor regularizá tu pago: {payment_link}\n\nSaludos.',
    },
    3: {
        'whatsapp': 'Urgente: Factura #{invoice_number} vencida 7 días (${amount}). Te ofrecemos un plan de pagos. Contactanos o pagá aquí: {payment_link}',
        'email': 'Hola {customer_name},\n\nUrgente: tu factura #{invoice_number} por ${amount} está vencida 7 días.\n\nTe ofrecemos un plan de pagos. Contactanos o pagá aquí: {payment_link}\n\nSaludos.',
    },
    4: {
        'whatsapp': 'Último aviso antes de suspensión: Factura #{invoice_number} por ${amount} vencida 14 días. Pagá inmediatamente: {payment_link}',
        'email': 'Hola {customer_name},\n\nÚltimo aviso: tu factura #{invoice_number} por ${amount} está vencida 14 días.\n\nSin pago inmediato, procederemos a suspender el servicio.\n\nPagá aquí: {payment_link}\n\nSellIA Cobranzas.',
    },
}


class FinanceAutopilotEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_config(self, business_id: uuid.UUID) -> FinanceAutopilotConfig:
        result = await self.db.execute(
            select(FinanceAutopilotConfig).where(FinanceAutopilotConfig.business_id == business_id)
        )
        config = result.scalar_one_or_none()
        if not config:
            config = FinanceAutopilotConfig(business_id=business_id)
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
            logger.info(f'Created default FinanceAutopilotConfig for business {business_id}')
        return config

    async def auto_deliver_invoices(self, business_id: uuid.UUID) -> dict[str, Any]:
        config = await self.get_or_create_config(business_id)
        if not config.is_active or config.is_paused or not config.auto_deliver_invoices:
            return {'delivered': 0, 'reason': 'Autopilot de finanzas inactivo o pausado'}

        result = await self.db.execute(
            select(SalesInvoice).where(
                SalesInvoice.business_id == business_id,
                SalesInvoice.status.in_(['draft', 'sent']),
            )
        )
        invoices = result.scalars().all()

        delivered = 0
        for inv in invoices:
            extra = dict(inv.extra_data) if inv.extra_data else {}
            if extra.get('delivered_at'):
                continue

            try:
                await self._deliver_invoice(inv)
                extra['delivered_at'] = datetime.now(timezone.utc).isoformat()
                extra['delivery_method'] = 'autopilot'
                inv.extra_data = extra
                if inv.status == 'draft':
                    inv.status = 'sent'
                delivered += 1
            except Exception as e:
                logger.error(f'Failed to deliver invoice {inv.id}: {e}')

        await self.db.commit()
        logger.info(f'Auto-delivered {delivered} invoices for business {business_id}')
        return {'delivered': delivered}

    async def _deliver_invoice(self, invoice: SalesInvoice) -> None:
        from app.domains.channels.services import send_outbound_message

        conversation_id = invoice.conversation_id
        if not conversation_id:
            logger.warning(f'Invoice {invoice.id} has no conversation_id, skipping delivery')
            return

        content = (
            f'Te enviamos tu factura #{invoice.invoice_number} por '
            f'${float(invoice.total_amount):,.2f}. Vencimiento: {invoice.due_date.strftime("%d/%m/%Y")}.'
        )
        await send_outbound_message(self.db, conversation_id, content, content_type='text')

    async def run_dunning_sequence(self, business_id: uuid.UUID) -> dict[str, Any]:
        config = await self.get_or_create_config(business_id)
        if not config.is_active or config.is_paused or not config.auto_run_dunning:
            return {'reminders_sent': 0, 'reason': 'Autopilot de cobranza inactivo o pausado'}

        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(SalesInvoice).where(
                SalesInvoice.business_id == business_id,
                SalesInvoice.status.in_(['sent', 'overdue']),
                SalesInvoice.due_date < now,
                SalesInvoice.paid_at.is_(None),
            )
        )
        overdue_invoices = result.scalars().all()

        reminders_sent = 0
        for inv in overdue_invoices:
            days_overdue = (now - inv.due_date).days
            level = self._determine_dunning_level(days_overdue)
            if level is None or level > config.max_dunning_level:
                continue

            can_send = await self._can_send_dunning(inv, level)
            if not can_send:
                continue

            try:
                message = await self.generate_dunning_message(inv, level, config.dunning_channel)
                await self._send_dunning_message(inv, message, config.dunning_channel)

                reminder = PaymentReminder(
                    business_id=business_id,
                    order_id=inv.order_id or uuid.uuid4(),
                    invoice_id=inv.id,
                    conversation_id=inv.conversation_id,
                    reminder_level=level,
                    status='sent',
                    scheduled_at=now,
                    sent_at=now,
                    message_content=message,
                    channel_platform=config.dunning_channel,
                )
                self.db.add(reminder)
                reminders_sent += 1
            except Exception as e:
                logger.error(f'Failed to send dunning for invoice {inv.id}: {e}')

        await self.db.commit()
        logger.info(f'Dunning sequence: {reminders_sent} reminders sent for business {business_id}')
        return {'reminders_sent': reminders_sent}

    def _determine_dunning_level(self, days_overdue: int) -> Optional[int]:
        if days_overdue >= 14:
            return 4
        if days_overdue >= 7:
            return 3
        if days_overdue >= 3:
            return 2
        if days_overdue >= 1:
            return 1
        return None

    async def _can_send_dunning(self, invoice: SalesInvoice, level: int) -> bool:
        from app.domains.outreach.service import FatigueScoringService

        if not invoice.conversation_id:
            return False

        fatigue = FatigueScoringService(self.db)
        check = await fatigue.can_contact_now(
            invoice.business_id,
            invoice.conversation_id,
            channel='whatsapp',
            message_type='dunning',
        )
        if not check['can_contact']:
            logger.info(f'Fatigue check failed for invoice {invoice.id}: {check["reason"]}')
            return False

        last_reminder = await self.db.execute(
            select(PaymentReminder).where(
                PaymentReminder.invoice_id == invoice.id,
            ).order_by(desc(PaymentReminder.sent_at)).limit(1)
        )
        last = last_reminder.scalar_one_or_none()
        if last and last.reminder_level >= level:
            return False

        return True

    async def generate_dunning_message(self, invoice: SalesInvoice, level: int, channel: str = 'whatsapp') -> str:
        templates = DUNNING_MESSAGES.get(level, DUNNING_MESSAGES[1])
        template = templates.get(channel, templates['whatsapp'])

        payment_link = invoice.extra_data.get('payment_link', 'https://sellia.ai/pagar') if invoice.extra_data else 'https://sellia.ai/pagar'
        customer_name = invoice.customer_name or 'Cliente'

        return template.format(
            invoice_number=invoice.invoice_number,
            amount=f'{float(invoice.total_amount):,.2f}',
            due_date=invoice.due_date.strftime('%d/%m/%Y'),
            payment_link=payment_link,
            customer_name=customer_name,
        )

    async def _send_dunning_message(self, invoice: SalesInvoice, message: str, channel: str) -> None:
        from app.domains.channels.services import send_outbound_message
        from app.domains.outreach.service import FatigueScoringService

        if not invoice.conversation_id:
            logger.warning(f'Invoice {invoice.id} has no conversation for dunning')
            return

        await send_outbound_message(self.db, invoice.conversation_id, message, content_type='text')

        fatigue = FatigueScoringService(self.db)
        await fatigue.record_contact(
            business_id=invoice.business_id,
            conversation_id=invoice.conversation_id,
            channel=channel,
            message_type='dunning',
            message_content=message,
            ai_generated=False,
        )

    async def auto_reconcile_payments(self, business_id: uuid.UUID) -> dict[str, Any]:
        config = await self.get_or_create_config(business_id)
        if not config.is_active or config.is_paused or not config.auto_reconcile_payments:
            return {'reconciled': 0, 'reason': 'Autopilot de conciliación inactivo o pausado'}

        result = await self.db.execute(
            select(Order).where(
                Order.business_id == business_id,
                Order.payment_status == PaymentStatus.COMPLETED,
            )
        )
        paid_orders = result.scalars().all()

        reconciled = 0
        for order in paid_orders:
            inv_result = await self.db.execute(
                select(SalesInvoice).where(
                    SalesInvoice.order_id == order.id,
                    SalesInvoice.status != 'paid',
                )
            )
            invoice = inv_result.scalar_one_or_none()
            if not invoice:
                continue

            invoice.status = 'paid'
            invoice.paid_at = order.paid_at or datetime.now(timezone.utc)
            invoice.paid_amount = order.total_amount
            reconciled += 1

        await self.db.commit()
        logger.info(f'Auto-reconciled {reconciled} payments for business {business_id}')
        return {'reconciled': reconciled}

    async def generate_tax_report(self, business_id: uuid.UUID, month: int, year: int) -> dict[str, Any]:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        result = await self.db.execute(
            select(SalesInvoice).where(
                SalesInvoice.business_id == business_id,
                SalesInvoice.created_at >= start,
                SalesInvoice.created_at < end,
                SalesInvoice.status == 'paid',
            )
        )
        invoices = result.scalars().all()

        total_invoiced = Decimal('0')
        total_tax = Decimal('0')
        total_net = Decimal('0')

        for inv in invoices:
            total_invoiced += inv.total_amount
            total_tax += inv.tax_amount
            total_net += inv.amount

        tax_config = await self.db.execute(
            select(TaxConfig).where(TaxConfig.business_id == business_id)
        )
        config = tax_config.scalar_one_or_none()
        tax_rate = config.tax_rate if config else Decimal('21.0')

        iva_debito = total_tax
        iva_credito = Decimal('0')

        saldo = iva_debito - iva_credito

        return {
            'period': f'{year}-{month:02d}',
            'total_invoiced': total_invoiced,
            'total_net': total_net,
            'iva_debito': iva_debito,
            'iva_credito': iva_credito,
            'saldo': saldo,
            'tax_rate': tax_rate,
            'invoice_count': len(invoices),
            'currency': 'ARS',
        }

    async def forecast_cash_flow(self, business_id: uuid.UUID, days: int = 30) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days)

        invoices_result = await self.db.execute(
            select(SalesInvoice).where(
                SalesInvoice.business_id == business_id,
                SalesInvoice.status.in_(['sent', 'overdue']),
                SalesInvoice.paid_at.is_(None),
            )
        )
        pending_invoices = invoices_result.scalars().all()

        total_receivables = sum(inv.total_amount for inv in pending_invoices)

        deals_result = await self.db.execute(
            select(Deal).where(
                Deal.business_id == business_id,
                Deal.is_active == True,
                Deal.stage.notin_([LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST]),
                Deal.expected_close_date >= now,
                Deal.expected_close_date <= end,
            )
        )
        pipeline_deals = deals_result.scalars().all()

        pipeline_weighted = sum(
            (deal.value or Decimal('0')) * Decimal(deal.probability) / Decimal('100')
            for deal in pipeline_deals
        )

        daily_projection = []
        collection_rate = Decimal('0.75')
        expected_daily = (total_receivables * collection_rate) / Decimal(str(days))
        pipeline_daily = pipeline_weighted / Decimal(str(days))

        for i in range(days):
            day = now + timedelta(days=i)
            projected_inflow = expected_daily + pipeline_daily
            confidence_low = projected_inflow * Decimal('0.6')
            confidence_high = projected_inflow * Decimal('1.4')

            daily_projection.append({
                'date': day.strftime('%Y-%m-%d'),
                'projected_inflow': float(projected_inflow.quantize(Decimal('0.01'))),
                'confidence_low': float(confidence_low.quantize(Decimal('0.01'))),
                'confidence_high': float(confidence_high.quantize(Decimal('0.01'))),
            })

        return {
            'days': days,
            'total_receivables': total_receivables,
            'pipeline_weighted': pipeline_weighted,
            'daily_projection': daily_projection,
            'currency': 'ARS',
        }

    async def get_finance_dashboard(self, business_id: uuid.UUID) -> dict[str, Any]:
        now = datetime.now(timezone.utc)

        outstanding_result = await self.db.execute(
            select(
                func.count(SalesInvoice.id),
                func.sum(SalesInvoice.total_amount - SalesInvoice.paid_amount),
            ).where(
                SalesInvoice.business_id == business_id,
                SalesInvoice.status.in_(['sent', 'overdue']),
            )
        )
        invoice_count, total_receivables = outstanding_result.one() or (0, Decimal('0'))

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

        dunning_result = await self.db.execute(
            select(func.count(PaymentReminder.id)).where(
                PaymentReminder.business_id == business_id,
                PaymentReminder.status == 'sent',
                PaymentReminder.sent_at >= now - timedelta(days=30),
            )
        )
        dunning_active = dunning_result.scalar() or 0

        forecast = await self.forecast_cash_flow(business_id, days=30)

        current_month = now.month
        current_year = now.year
        tax_report = await self.generate_tax_report(business_id, current_month, current_year)

        config = await self.get_or_create_config(business_id)

        collection_rate = Decimal('0')
        if total_receivables and total_receivables > 0:
            paid_result = await self.db.execute(
                select(func.sum(SalesInvoice.total_amount)).where(
                    SalesInvoice.business_id == business_id,
                    SalesInvoice.status == 'paid',
                    SalesInvoice.paid_at >= now - timedelta(days=30),
                )
            )
            paid_30d = paid_result.scalar() or Decimal('0')
            total_billed_result = await self.db.execute(
                select(func.sum(SalesInvoice.total_amount)).where(
                    SalesInvoice.business_id == business_id,
                    SalesInvoice.created_at >= now - timedelta(days=30),
                )
            )
            total_billed_30d = total_billed_result.scalar() or Decimal('0')
            if total_billed_30d > 0:
                collection_rate = (paid_30d / total_billed_30d) * Decimal('100')

        return {
            'business_id': str(business_id),
            'total_receivables': total_receivables or Decimal('0'),
            'overdue_amount': total_overdue or Decimal('0'),
            'invoice_count': invoice_count or 0,
            'overdue_count': overdue_count or 0,
            'dunning_active': dunning_active,
            'forecast_summary': forecast['daily_projection'][0] if forecast['daily_projection'] else None,
            'tax_status': {
                'period': tax_report['period'],
                'saldo': tax_report['saldo'],
                'invoice_count': tax_report['invoice_count'],
            },
            'collection_rate': collection_rate,
            'autopilot_active': config.is_active and not config.is_paused,
            'currency': 'ARS',
        }

    async def get_dunning_pipeline(self, business_id: uuid.UUID) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(SalesInvoice).where(
                SalesInvoice.business_id == business_id,
                SalesInvoice.status.in_(['sent', 'overdue']),
                SalesInvoice.due_date < now,
                SalesInvoice.paid_at.is_(None),
            )
        )
        overdue_invoices = result.scalars().all()

        pipeline = {
            'level_1': {'label': 'Amable (Día 1)', 'count': 0, 'amount': Decimal('0')},
            'level_2': {'label': 'Firme (Día 3)', 'count': 0, 'amount': Decimal('0')},
            'level_3': {'label': 'Urgente (Día 7)', 'count': 0, 'amount': Decimal('0')},
            'level_4': {'label': 'Final (Día 14)', 'count': 0, 'amount': Decimal('0')},
        }

        for inv in overdue_invoices:
            days_overdue = (now - inv.due_date).days
            level = self._determine_dunning_level(days_overdue)
            if level:
                key = f'level_{level}'
                pipeline[key]['count'] += 1
                pipeline[key]['amount'] += inv.total_amount

        return {
            k: {
                'label': v['label'],
                'count': v['count'],
                'amount': float(v['amount'].quantize(Decimal('0.01'))),
            }
            for k, v in pipeline.items()
        }
