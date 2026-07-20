"""Finance API Router."""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.finance.schemas import (
    SalesInvoiceCreate, SalesInvoiceResponse,
    PaymentReminderResponse, AccountsReceivableSnapshotResponse,
    TaxConfigResponse,
    FinanceAutopilotStatusResponse,
    TaxReportResponse,
    CashFlowForecastResponse,
    DunningPipelineResponse,
    FinanceDashboardResponse,
)
from app.domains.finance.services import FinanceService
from app.domains.finance.autopilot import FinanceAutopilotEngine

router = APIRouter(prefix="/{business_id}/finance", tags=["Finance"])


@router.post("/invoices", response_model=SalesInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    business_id: UUID,
    inv_in: SalesInvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return await service.create_invoice(business_id=business_id, **inv_in.model_dump())


@router.get("/invoices", response_model=list[SalesInvoiceResponse])
async def list_invoices(
    business_id: UUID,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return await service.get_invoices(business_id, status)


@router.get("/reminders/pending", response_model=list[PaymentReminderResponse])
async def list_pending_reminders(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return await service.get_pending_reminders(business_id)


@router.post("/ar-snapshot", response_model=AccountsReceivableSnapshotResponse, status_code=status.HTTP_201_CREATED)
async def generate_ar_snapshot(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return await service.generate_ar_snapshot(business_id)


@router.get("/tax-config", response_model=TaxConfigResponse | None)
async def get_tax_config(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return await service.get_tax_config(business_id)


# ---------------------------------------------------------------------------
# Finance Autopilot
# ---------------------------------------------------------------------------

@router.get("/autopilot/status", response_model=FinanceAutopilotStatusResponse)
async def get_finance_autopilot_status(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = FinanceAutopilotEngine(db)
    config = await engine.get_or_create_config(business_id)
    return FinanceAutopilotStatusResponse(
        business_id=business_id,
        is_active=config.is_active,
        is_paused=config.is_paused,
        paused_reason=config.paused_reason,
        auto_deliver_invoices=config.auto_deliver_invoices,
        auto_run_dunning=config.auto_run_dunning,
        auto_reconcile_payments=config.auto_reconcile_payments,
        auto_generate_tax_reports=config.auto_generate_tax_reports,
        dunning_channel=config.dunning_channel,
        max_dunning_level=config.max_dunning_level,
    )


@router.post("/autopilot/toggle")
async def toggle_finance_autopilot(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = FinanceAutopilotEngine(db)
    config = await engine.get_or_create_config(business_id)
    config.is_active = not config.is_active
    await db.commit()
    await db.refresh(config)
    return {
        'is_active': config.is_active,
        'message': 'Autopilot financiero activado' if config.is_active else 'Autopilot financiero desactivado',
    }


@router.post("/autopilot/trigger-delivery")
async def trigger_invoice_delivery(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    result = await service.trigger_auto_delivery(business_id)
    return result


@router.post("/autopilot/trigger-dunning")
async def trigger_dunning_sequence(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    result = await service.trigger_dunning(business_id)
    return result


@router.get("/autopilot/dashboard", response_model=FinanceDashboardResponse)
async def get_finance_dashboard(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = FinanceAutopilotEngine(db)
    data = await engine.get_finance_dashboard(business_id)
    return FinanceDashboardResponse(**data)


@router.get("/autopilot/cash-flow", response_model=CashFlowForecastResponse)
async def get_cash_flow_forecast(
    business_id: UUID,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = FinanceAutopilotEngine(db)
    data = await engine.forecast_cash_flow(business_id, days=days)
    return CashFlowForecastResponse(**data)


@router.get("/autopilot/tax-report", response_model=TaxReportResponse)
async def get_tax_report(
    business_id: UUID,
    month: int = Query(datetime.now(timezone.utc).month, ge=1, le=12),
    year: int = Query(datetime.now(timezone.utc).year, ge=2020, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = FinanceAutopilotEngine(db)
    data = await engine.generate_tax_report(business_id, month=month, year=year)
    return TaxReportResponse(**data)


@router.get("/autopilot/dunning-pipeline", response_model=DunningPipelineResponse)
async def get_dunning_pipeline(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = FinanceAutopilotEngine(db)
    data = await engine.get_dunning_pipeline(business_id)
    return DunningPipelineResponse(**data)
