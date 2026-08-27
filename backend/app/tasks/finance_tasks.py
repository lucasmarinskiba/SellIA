"""Finance Celery Tasks.

Autopilot financiero: facturación, cobranza, conciliación y reporting.
"""

import asyncio
from celery import shared_task
from datetime import datetime, timezone

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.businesses.models import Business
from app.domains.finance.autopilot import FinanceAutopilotEngine
from sqlalchemy import select

logger = get_logger(__name__)


def _async_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(name="app.tasks.finance_tasks.auto_deliver_invoices")
def auto_deliver_invoices():
    """Daily at 8 AM: deliver all pending invoices."""
    async def _run():
        async with AsyncSessionLocal() as db:
            engine = FinanceAutopilotEngine(db)
            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            total_delivered = 0
            for business in businesses:
                try:
                    res = await engine.auto_deliver_invoices(business.id)
                    total_delivered += res.get('delivered', 0)
                except Exception as e:
                    logger.error(f'Failed auto-deliver for business {business.id}: {e}')

            logger.info(f'Finance auto-deliver: {total_delivered} invoices delivered')
            return {'delivered': total_delivered}

    return _async_run(_run())


@shared_task(name="app.tasks.finance_tasks.dunning_sequence")
def dunning_sequence():
    """Daily at 9 AM: run dunning for overdue invoices."""
    async def _run():
        async with AsyncSessionLocal() as db:
            engine = FinanceAutopilotEngine(db)
            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            total_reminders = 0
            for business in businesses:
                try:
                    res = await engine.run_dunning_sequence(business.id)
                    total_reminders += res.get('reminders_sent', 0)
                except Exception as e:
                    logger.error(f'Failed dunning for business {business.id}: {e}')

            logger.info(f'Finance dunning: {total_reminders} reminders sent')
            return {'reminders_sent': total_reminders}

    return _async_run(_run())


@shared_task(name="app.tasks.finance_tasks.cash_flow_forecast")
def cash_flow_forecast():
    """Daily at 6 AM: generate cash flow forecast."""
    async def _run():
        async with AsyncSessionLocal() as db:
            engine = FinanceAutopilotEngine(db)
            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            forecasts = 0
            for business in businesses:
                try:
                    await engine.forecast_cash_flow(business.id, days=30)
                    forecasts += 1
                except Exception as e:
                    logger.error(f'Failed cash flow forecast for business {business.id}: {e}')

            logger.info(f'Finance cash flow: {forecasts} forecasts generated')
            return {'forecasts': forecasts}

    return _async_run(_run())


@shared_task(name="app.tasks.finance_tasks.ledger_bank_reconciliation")
def ledger_bank_reconciliation():
    """Every 3 hours: auto-match imported bank movements to ledger entries."""
    async def _run():
        from app.domains.ledger.reconciliation import ReconciliationService

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Business).where(Business.is_active == True))
            businesses = result.scalars().all()
            matched = 0
            for business in businesses:
                try:
                    res = await ReconciliationService(db).run_reconciliation(business.id)
                    matched += res.get("auto_matched", 0) + res.get("rule_categorized", 0)
                except Exception as e:
                    logger.error(f"Ledger reconcile failed for business {business.id}: {e}")
            logger.info(f"Ledger bank reconciliation: {matched} movements resolved")
            return {"resolved": matched}

    return _async_run(_run())


@shared_task(name="app.tasks.finance_tasks.ledger_month_close")
def ledger_month_close():
    """Monthly (1st, 03:00): soft-close the prior calendar month for every business."""
    async def _run():
        from datetime import timedelta

        from app.domains.ledger.reports import LedgerReports
        from app.domains.ledger.service import LedgerService

        first_of_this_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        prior = first_of_this_month - timedelta(days=1)
        period_name = prior.strftime("%Y-%m")

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Business).where(Business.is_active == True))
            businesses = result.scalars().all()
            closed = 0
            for business in businesses:
                try:
                    await LedgerService(db).ensure_setup(business.id)
                    await LedgerReports(db).close_period(business.id, period_name, lock=False)
                    closed += 1
                except Exception as e:
                    logger.warning(f"Month close skipped for business {business.id}: {e}")
            logger.info(f"Ledger month close ({period_name}): {closed} businesses closed")
            return {"period": period_name, "closed": closed}

    return _async_run(_run())


@shared_task(name="app.tasks.finance_tasks.auto_reconcile_payments")
def auto_reconcile_payments():
    """Every 2 hours: reconcile payments with invoices."""
    async def _run():
        async with AsyncSessionLocal() as db:
            engine = FinanceAutopilotEngine(db)
            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            total_reconciled = 0
            for business in businesses:
                try:
                    res = await engine.auto_reconcile_payments(business.id)
                    total_reconciled += res.get('reconciled', 0)
                except Exception as e:
                    logger.error(f'Failed reconcile for business {business.id}: {e}')

            logger.info(f'Finance reconcile: {total_reconciled} payments reconciled')
            return {'reconciled': total_reconciled}

    return _async_run(_run())
