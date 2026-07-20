"""
Subscription Integrity Validator

Valida que el usuario tenga acceso a las features de su plan.
Genera logs de uso para evidencia ante disputas.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.domains.subscriptions.models import Subscription, SubscriptionPlan
from app.domains.security.models import SubscriptionAccessLog
from app.core.logger import get_logger

logger = get_logger(__name__)


async def validate_subscription_access(
    db: AsyncSession,
    user_id: uuid.UUID,
    feature_name: str,
) -> tuple[bool, Optional[str]]:
    """
    Valida si el usuario puede acceder a una feature.

    Returns:
        (allowed, reason)
    """
    # Get active subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_(["active", "trialing"]),
        )
    )
    sub = result.scalar_one_or_none()

    if not sub:
        return False, "No tienes una suscripción activa"

    # Get plan features
    plan = sub.plan
    if not plan:
        return False, "Plan no encontrado"

    features = plan.features or []
    limits = plan.limits or {}

    # Check if feature is in plan
    if feature_name not in features:
        # Some features are available to all paid plans
        if feature_name in ["basic_agent"] and plan.slug != "free":
            pass
        else:
            return False, f"La feature '{feature_name}' no está incluida en tu plan {plan.name}"

    # Check if subscription period is active
    if sub.current_period_end and sub.current_period_end < datetime.now(timezone.utc):
        return False, "Tu suscripción expiró. Renová para continuar."

    if sub.cancel_at_period_end and sub.current_period_end:
        days_remaining = (sub.current_period_end - datetime.now(timezone.utc)).days
        if days_remaining <= 0:
            return False, "Tu suscripción fue cancelada y ya venció."

    return True, None


async def log_feature_access(
    db: AsyncSession,
    user_id: uuid.UUID,
    feature_name: str,
    endpoint: str,
    response_status: int,
    response_size: int = 0,
    duration_ms: int = 0,
    success: bool = True,
) -> SubscriptionAccessLog:
    """Loguea el acceso a una feature para evidencia."""
    log = SubscriptionAccessLog(
        user_id=user_id,
        feature_name=feature_name,
        endpoint=endpoint,
        response_status=response_status,
        response_size=response_size,
        duration_ms=duration_ms,
        success=success,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def generate_usage_report(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: int = 30,
) -> Dict[str, Any]:
    """Genera un reporte de uso para disputas de pago."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            SubscriptionAccessLog.feature_name,
            func.count(),
            func.sum(SubscriptionAccessLog.duration_ms),
        )
        .where(
            SubscriptionAccessLog.user_id == user_id,
            SubscriptionAccessLog.created_at >= since,
            SubscriptionAccessLog.success == True,
        )
        .group_by(SubscriptionAccessLog.feature_name)
    )

    features_usage = [
        {"feature": fname, "requests": count, "total_duration_ms": total_dur or 0}
        for fname, count, total_dur in result.all()
    ]

    total_requests = sum(f["requests"] for f in features_usage)

    return {
        "user_id": str(user_id),
        "period_days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_requests": total_requests,
        "features_usage": features_usage,
    }
