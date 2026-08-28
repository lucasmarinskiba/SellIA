"""Unified Financial Dashboard API — real data from ledger + invoicing +
ad_budget + cashflow, one call. Replaces the mocked KPIs in
app/api/v1/analytics_dashboard.py's /overview with figures actually
computed from posted journal entries, invoices, ad channels, and cash
projections."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.cache import cached
from app.domains.financial_dashboard.schemas import FinancialDashboardOut
from app.domains.financial_dashboard.service import FinancialDashboardService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/financial-dashboard", tags=["Financial Dashboard"])


@router.get("", response_model=FinancialDashboardOut)
@cached(ttl_seconds=900, key_prefix="financial_dashboard")
async def get_financial_dashboard(
    business_id: UUID,
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unified financial dashboard: revenue/margins (ledger), ad spend + ROAS
    (ad_budget), accounts receivable + overdue (invoicing), cash + runway
    (cashflow). Cached 15min — fans out across 4 domains.

    Sections a business hasn't set up yet (e.g. no ledger entries posted)
    return zeroed values with `data_availability` flagging what's real.
    """
    svc = FinancialDashboardService(db)
    return await svc.get_dashboard(business_id, period_days)
