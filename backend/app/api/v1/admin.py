"""
Admin Router

Cross-domain admin endpoints for platform management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.consumo.models import ChurnRiskSignal
from app.domains.consumo import service as consumo_service
from app.domains.nps.models import FeedbackNPSResponse
from app.domains.referrals.models import ReferralCode

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")
    return current_user


# ===== CHURN SIGNALS =====

@router.get("/churn-signals")
async def get_admin_churn_signals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Admin-only: list ALL ChurnRiskSignal records with pagination."""
    offset = (page - 1) * page_size

    result = await db.execute(
        select(ChurnRiskSignal)
        .order_by(desc(ChurnRiskSignal.created_at))
        .offset(offset)
        .limit(page_size)
    )
    signals = result.scalars().all()

    count_result = await db.execute(select(func.count(ChurnRiskSignal.id)))
    total = count_result.scalar() or 0

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "business_id": s.business_id,
                "risk_score": s.risk_score,
                "risk_level": s.risk_level,
                "signals": s.signals,
                "action_taken": s.action_taken,
                "action_result": s.action_result,
                "resolved": s.resolved,
                "resolved_at": s.resolved_at,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in signals
        ],
    }


# ===== MARGINS =====

@router.get("/margins")
async def get_admin_margins(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    days: int = Query(30, ge=1, le=90),
):
    """Admin-only: margin analysis per user (plan price vs AI cost)."""
    return await consumo_service.get_user_margins(db, days=days)


# ===== NPS STATS =====

@router.get("/nps-stats")
async def get_admin_nps_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
):
    """Admin-only: aggregated NPS statistics."""
    total_result = await db.execute(select(func.count(FeedbackNPSResponse.id)))
    total = total_result.scalar() or 0

    promoters_result = await db.execute(
        select(func.count(FeedbackNPSResponse.id)).where(FeedbackNPSResponse.score >= 9)
    )
    promoters = promoters_result.scalar() or 0

    passives_result = await db.execute(
        select(func.count(FeedbackNPSResponse.id)).where(FeedbackNPSResponse.score.between(7, 8))
    )
    passives = passives_result.scalar() or 0

    detractors_result = await db.execute(
        select(func.count(FeedbackNPSResponse.id)).where(FeedbackNPSResponse.score <= 6)
    )
    detractors = detractors_result.scalar() or 0

    nps_score = round(((promoters - detractors) / total) * 100, 1) if total else 0
    avg_result = await db.execute(select(func.avg(FeedbackNPSResponse.score)))
    avg_score = round(avg_result.scalar() or 0, 1)

    return {
        "total_responses": total,
        "promoters": promoters,
        "passives": passives,
        "detractors": detractors,
        "nps_score": nps_score,
        "average_score": avg_score,
    }


# ===== REFERRAL STATS =====

@router.get("/referral-stats")
async def get_admin_referral_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    top_n: int = Query(10, ge=1, le=100),
):
    """Admin-only: global referral statistics."""
    total_codes_result = await db.execute(select(func.count(ReferralCode.id)))
    total_codes = total_codes_result.scalar() or 0

    total_clicks_result = await db.execute(select(func.coalesce(func.sum(ReferralCode.total_clicks), 0)))
    total_clicks = total_clicks_result.scalar() or 0

    total_signups_result = await db.execute(select(func.coalesce(func.sum(ReferralCode.total_signups), 0)))
    total_signups = total_signups_result.scalar() or 0

    total_conversions_result = await db.execute(select(func.coalesce(func.sum(ReferralCode.total_conversions), 0)))
    total_conversions = total_conversions_result.scalar() or 0

    top_referrers_result = await db.execute(
        select(
            ReferralCode.code,
            ReferralCode.total_clicks,
            ReferralCode.total_signups,
            ReferralCode.total_conversions,
            ReferralCode.total_revenue_generated,
            User.email,
        )
        .join(User, User.id == ReferralCode.user_id)
        .order_by(desc(ReferralCode.total_conversions))
        .limit(top_n)
    )
    top_referrers = [
        {
            "code": row.code,
            "user_email": row.email,
            "total_clicks": row.total_clicks,
            "total_signups": row.total_signups,
            "total_conversions": row.total_conversions,
            "total_revenue_generated": float(row.total_revenue_generated or 0),
        }
        for row in top_referrers_result.all()
    ]

    return {
        "total_codes": total_codes,
        "total_clicks": total_clicks,
        "total_signups": total_signups,
        "total_conversions": total_conversions,
        "top_referrers": top_referrers,
    }
