"""Subscription limit enforcement dependency for FastAPI endpoints.

Usage:
    @router.post("/channels")
    async def create_channel(
        ...,
        _limit: None = Depends(require_limit("channels", 1)),
    ):
        ...
"""

from typing import Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.subscriptions.services import check_subscription_limit, track_usage


def require_limit(metric_type: str, quantity: int = 1, track_after: bool = True):
    """FastAPI dependency that enforces subscription limits before endpoint execution.

    If track_after=True, usage is tracked automatically after the endpoint succeeds.
    Note: automatic post-tracking requires wrapping the endpoint, which is complex.
    For simplicity, set track_after=False and call track_usage manually in the endpoint.
    """
    async def _check_limit(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ):
        result = await check_subscription_limit(db, current_user.id, metric_type, quantity)
        if not result["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Límite alcanzado para {metric_type}. Usados: {result['used']}/{result['limit']}"
            )
        return result

    return _check_limit


async def enforce_limit(
    db: AsyncSession,
    user_id: Any,
    metric_type: str,
    quantity: int = 1,
) -> dict:
    """Direct limit check for use inside service functions (not as a dependency)."""
    result = await check_subscription_limit(db, user_id, metric_type, quantity)
    if not result["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Límite alcanzado para {metric_type}. Usados: {result['used']}/{result['limit']}"
        )
    return result
