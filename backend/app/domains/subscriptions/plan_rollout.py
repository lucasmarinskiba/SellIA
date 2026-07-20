"""
Plan-Based Rollout

Despliega mejoras del sistema a clientes según su plan de suscripción.
Enterprise recibe todo inmediatamente, Free solo bugfixes críticos.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.feedback.models import SystemImprovement, FeatureFlag
from app.domains.subscriptions.models import Subscription, SubscriptionPlan
from app.core.logger import get_logger

logger = get_logger(__name__)

# Días de retraso por plan
PLAN_ROLLOUT_DELAYS = {
    "free": 30,      # Free recibe solo bugfixes críticos, resto después de 30 días
    "starter": 14,
    "pro": 7,
    "enterprise": 0, # Inmediato
}

# Planes que pueden recibir cada tipo de mejora
PLAN_MINIMUM_FOR_TYPE = {
    "bugfix": "free",
    "security": "free",
    "performance": "starter",
    "feature_small": "starter",
    "feature_medium": "pro",
    "feature_large": "enterprise",
    "custom": "enterprise",
}


async def get_eligible_improvements(
    db: AsyncSession,
    plan_slug: str,
) -> List[SystemImprovement]:
    """
    Obtiene mejoras disponibles para un plan específico.

    Considera:
    - minimum_plan de la mejora
    - Días de retraso del plan
    - Estado deployed de la mejora
    """
    delay_days = PLAN_ROLLOUT_DELAYS.get(plan_slug, 30)

    # Get improvements that have been deployed long enough
    min_deploy_date = datetime.now(timezone.utc) - timedelta(days=delay_days)

    result = await db.execute(
        select(SystemImprovement).where(
            SystemImprovement.status == "deployed",
            SystemImprovement.deployed_at <= min_deploy_date,
        ).order_by(SystemImprovement.deployed_at.desc())
    )

    improvements = result.scalars().all()

    # Filter by plan hierarchy
    plan_hierarchy = ["free", "starter", "pro", "enterprise"]
    user_plan_index = plan_hierarchy.index(plan_slug) if plan_slug in plan_hierarchy else -1

    eligible = []
    for imp in improvements:
        imp_plan_index = plan_hierarchy.index(imp.target_plan) if imp.target_plan in plan_hierarchy else 999
        if user_plan_index >= imp_plan_index:
            eligible.append(imp)

    return eligible


async def get_new_features_for_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_slug: str,
    since: Optional[datetime] = None,
) -> List[SystemImprovement]:
    """
    Obtiene features nuevas disponibles para un usuario desde su último login.
    """
    if not since:
        since = datetime.now(timezone.utc) - timedelta(days=30)

    eligible = await get_eligible_improvements(db, plan_slug)

    # Filter by deployment date
    return [imp for imp in eligible if imp.deployed_at and imp.deployed_at > since]


async def check_feature_availability(
    db: AsyncSession,
    feature_name: str,
    user_id: uuid.UUID,
    plan_slug: str,
) -> bool:
    """Verifica si una feature específica está disponible para un usuario."""
    from app.core.intelligence.feature_flags import can_use_feature
    return await can_use_feature(db, feature_name, plan_slug, user_id)


async def generate_changelog_for_plan(
    db: AsyncSession,
    plan_slug: str,
    limit: int = 20,
) -> List[SystemImprovement]:
    """Genera changelog filtrado por plan."""
    eligible = await get_eligible_improvements(db, plan_slug)
    return eligible[:limit]


async def notify_plan_users_of_update(
    db: AsyncSession,
    improvement: SystemImprovement,
) -> int:
    """
    Notifica a usuarios de un plan sobre una nueva mejora disponible.

    Returns:
        Número de notificaciones enviadas.
    """
    from app.domains.users.models import User

    result = await db.execute(
        select(User).where(
            User.is_active == True,
            User.is_superuser == False,
        )
    )
    users = result.scalars().all()

    notified = 0
    for user in users:
        # Check user's plan
        if user.subscription and user.subscription.plan:
            user_plan = user.subscription.plan.slug
            eligible = await get_eligible_improvements(db, user_plan)
            if improvement in eligible:
                # TODO: Send email/push notification
                logger.info(f"Would notify user {user.id} about improvement {improvement.id}")
                notified += 1

    return notified
