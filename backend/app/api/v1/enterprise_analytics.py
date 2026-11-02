"""Sales dashboard for the signed-in owner, from the database.

Replaces the random-number engine that used to answer here. The numbers come from
``app.domains.analytics.sales_dashboard``; only the owner can read their own dashboard.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, resolve_business_id
from app.domains.analytics.sales_dashboard import TimeRange, assert_owner, build_sales_dashboard
from app.domains.users.models import User

router = APIRouter(tags=["analytics"])


@router.get("/analytics/dashboard/{user_id}")
async def get_sales_dashboard(
    user_id: str,
    time_range: TimeRange = Query("month", description="today, week, month, quarter or year"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The caller's own sales dashboard. Another account's id is refused."""
    assert_owner(user_id, current_user)

    business_id = await resolve_business_id(db, current_user)
    data = await build_sales_dashboard(db, business_id, time_range)
    return {"user_id": str(current_user.id), **data}
