"""
Feature Flags Engine

Gestiona feature flags con despliegue gradual por plan de suscripción.
"""

import uuid
import hashlib
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.feedback.models import FeatureFlag
from app.core.logger import get_logger

logger = get_logger(__name__)


async def can_use_feature(
    db: AsyncSession,
    feature_name: str,
    user_plan: str,
    user_id: Optional[uuid.UUID] = None,
) -> bool:
    """
    Verifica si un usuario puede usar una feature basada en su plan
    y el rollout percentage del feature flag.
    """
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.name == feature_name, FeatureFlag.is_active == True)
    )
    flag = result.scalar_one_or_none()
    if not flag:
        return False

    # Check plan
    if user_plan not in flag.enabled_plans:
        return False

    # Check allowlist
    if flag.user_id_allowlist and user_id and str(user_id) in flag.user_id_allowlist:
        return True

    # Check rollout percentage
    if flag.rollout_percentage >= 100:
        return True

    if user_id:
        hash_val = int(hashlib.md5(f"{feature_name}:{user_id}".encode()).hexdigest(), 16)
        user_percentile = hash_val % 100
        return user_percentile < flag.rollout_percentage

    return False


async def list_available_features(
    db: AsyncSession,
    user_plan: str,
    user_id: Optional[uuid.UUID] = None,
) -> List[FeatureFlag]:
    """Lista todas las features disponibles para un usuario."""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.is_active == True)
    )
    flags = result.scalars().all()

    available = []
    for flag in flags:
        if await can_use_feature(db, flag.name, user_plan, user_id):
            available.append(flag)

    return available


async def increment_rollout(
    db: AsyncSession,
    feature_name: str,
    increment: int = 10,
) -> bool:
    """Incrementa el rollout percentage de un feature flag."""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.name == feature_name)
    )
    flag = result.scalar_one_or_none()
    if not flag:
        return False

    flag.rollout_percentage = min(100, flag.rollout_percentage + increment)
    await db.commit()
    logger.info(f"Increased rollout for {feature_name} to {flag.rollout_percentage}%")
    return True


async def enable_for_plan(
    db: AsyncSession,
    feature_name: str,
    plan: str,
) -> bool:
    """Habilita un feature flag para un plan específico."""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.name == feature_name)
    )
    flag = result.scalar_one_or_none()
    if not flag:
        return False

    if plan not in flag.enabled_plans:
        flag.enabled_plans = flag.enabled_plans + [plan]
        await db.commit()
        logger.info(f"Enabled {feature_name} for plan {plan}")
    return True
