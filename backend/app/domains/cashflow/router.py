"""Cash-flow forecasting API — /api/v1/businesses/{business_id}/cashflow/*"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.cashflow.schemas import CashFlowForecastOut, CashFlowRequest
from app.domains.cashflow.service import CashFlowService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/cashflow", tags=["Cash Flow"])


@router.post("/forecast", response_model=CashFlowForecastOut)
async def forecast_cashflow(
    business_id: UUID,
    body: CashFlowRequest = CashFlowRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        cf = await CashFlowService(db).forecast(
            business_id,
            horizon_days=body.horizon_days,
            payment_delay_days=body.payment_delay_days,
            cogs_pct=body.cogs_pct,
            opex_daily=body.opex_daily,
            tax_rate=body.tax_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))

    return CashFlowForecastOut(
        business_id=cf.business_id,
        start_date=cf.start_date,
        horizon_days=cf.horizon_days,
        beginning_balance=cf.beginning_balance,
        end_balance=cf.end_balance,
        min_balance=cf.min_balance,
        max_balance=cf.max_balance,
        min_balance_date=cf.min_balance_date,
        runway_days=cf.runway_days,
        assumptions={
            "payment_delay_days": cf.assumptions.avg_payment_delay_days,
            "cogs_pct": float(cf.assumptions.cogs_pct_revenue),
            "opex_daily": float(cf.assumptions.opex_daily),
            "tax_rate": float(cf.assumptions.tax_rate),
        },
        computed_at=cf.computed_at,
        points=[
            {
                "date": p.date,
                "revenue_forecast": p.revenue_forecast,
                "cogs_forecast": p.cogs_forecast,
                "opex": p.opex,
                "tax_provision": p.tax_provision,
                "inflow_from_prior_sales": p.inflow_from_prior_sales,
                "operating_cash_flow": p.operating_cash_flow,
                "net_cash_flow": p.net_cash_flow,
                "cumulative_balance": p.cumulative_balance,
                "confidence_q10": p.confidence_q10,
                "confidence_q90": p.confidence_q90,
            }
            for p in cf.points
        ],
    )
