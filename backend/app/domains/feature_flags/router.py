"""
Feature Flags Admin API

Manage feature flags for gradual rollouts and kill-switches.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.feature_flags import service as flag_service

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/")
async def list_flags(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all feature flags (admin)."""
    return await flag_service.FeatureFlagService.get_all_flags(db)


@router.get("/check/{flag_name}")
async def check_flag(
    flag_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Check if a feature flag is enabled for the current user."""
    plan_id = None
    # Try to get active subscription plan
    from sqlalchemy import select
    from app.domains.subscriptions.models import Subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active",
        )
    )
    sub = result.scalar_one_or_none()
    if sub:
        plan_id = str(sub.plan_id)

    enabled = await flag_service.flag_enabled(
        db, flag_name, user_id=str(current_user.id), plan_id=plan_id, default=False,
    )
    return {"flag": flag_name, "enabled": enabled}
