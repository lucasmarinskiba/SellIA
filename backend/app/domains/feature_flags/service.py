"""
Feature Flags Service

Lightweight feature flag system for gradual rollouts,
plan-gating, and instant kill-switches.
"""

import hashlib
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import get_logger

logger = get_logger(__name__)

# In-memory cache for feature flags to avoid DB hits on every request
_flag_cache = {}
_cache_ttl = 60  # seconds
_last_fetch = 0


class FeatureFlagService:
    """Check if a feature is enabled for a given user/plan."""

    @staticmethod
    async def is_enabled(
        db: AsyncSession,
        flag_name: str,
        user_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        default: bool = False,
    ) -> bool:
        """
        Check if a feature flag is enabled.

        Logic:
        1. If flag doesn't exist → return default
        2. If flag is_active=False → return False (global kill-switch)
        3. If plan_id not in enabled_plans → return False
        4. If rollout_percentage < 100 → hash user_id and check
        5. If user in allowlist → return True
        """
        from app.domains.feature_flags.models import FeatureFlag

        result = await db.execute(
            select(FeatureFlag).where(FeatureFlag.name == flag_name)
        )
        flag = result.scalar_one_or_none()

        if not flag:
            return default

        if not flag.is_active:
            return False

        if flag.enabled_plans and plan_id and plan_id not in flag.enabled_plans:
            return False

        if flag.user_id_allowlist and user_id:
            if user_id in flag.user_id_allowlist:
                return True

        if flag.rollout_percentage >= 100:
            return True

        if user_id:
            # Deterministic rollout based on user ID hash
            hash_val = int(hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest(), 16)
            user_bucket = hash_val % 100
            return user_bucket < flag.rollout_percentage

        return flag.rollout_percentage >= 50  # Default for anonymous

    @staticmethod
    async def get_all_flags(db: AsyncSession) -> List[dict]:
        """Return all feature flags (for admin UI)."""
        from app.domains.feature_flags.models import FeatureFlag
        result = await db.execute(select(FeatureFlag))
        flags = result.scalars().all()
        return [
            {
                "name": f.name,
                "description": f.description,
                "enabled_plans": f.enabled_plans,
                "rollout_percentage": f.rollout_percentage,
                "is_active": f.is_active,
            }
            for f in flags
        ]


# Convenience function
async def flag_enabled(
    db: AsyncSession,
    flag_name: str,
    user_id: Optional[str] = None,
    plan_id: Optional[str] = None,
    default: bool = False,
) -> bool:
    return await FeatureFlagService.is_enabled(db, flag_name, user_id, plan_id, default)
