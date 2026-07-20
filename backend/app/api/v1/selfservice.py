"""
Self-Service API — Safe tools for the AI chatbot.

The chatbot can call these endpoints to perform actions on behalf
of the user (regenerate API keys, pause subscription, etc.)
without requiring full admin access.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.core.security import get_password_hash
from app.domains.users.models import User
from app.domains.users.schemas import UserResponse
from app.domains.subscriptions.models import Subscription

router = APIRouter(prefix="/selfservice", tags=["selfservice"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Return current user info (for chatbot context)."""
    return current_user


@router.post("/regenerate-api-key")
async def regenerate_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Regenerate the user's API key."""
    import secrets
    new_key = secrets.token_urlsafe(32)
    current_user.api_key = get_password_hash(new_key)
    await db.commit()
    return {"api_key": new_key, "message": "API key regenerada exitosamente"}


@router.post("/pause-subscription")
async def pause_subscription(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Pause the active subscription at end of period."""
    from sqlalchemy import select
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active",
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="No hay suscripción activa")
    sub.status = "paused"
    await db.commit()
    return {"message": "Suscripción pausada. Se mantendrá activa hasta el final del período actual."}


@router.get("/usage-summary")
async def usage_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return a summary of current usage for the chatbot."""
    from sqlalchemy import select, func
    from datetime import datetime, timezone, timedelta
    from app.domains.subscriptions.models import UsageTracking, Subscription, SubscriptionPlan

    since = datetime.now(timezone.utc) - timedelta(days=30)
    usage_result = await db.execute(
        select(func.sum(UsageTracking.ai_messages_used)).where(
            UsageTracking.user_id == current_user.id,
            UsageTracking.created_at >= since,
        )
    )
    ai_messages = usage_result.scalar() or 0

    sub_result = await db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.user_id == current_user.id, Subscription.status == "active")
    )
    row = sub_result.first()
    plan_name = row[1].name if row else "Sin plan"
    plan_limit = row[1].ai_message_limit if row else 0

    return {
        "plan": plan_name,
        "ai_messages_used": int(ai_messages),
        "ai_messages_limit": plan_limit,
        "percentage_used": round(ai_messages / plan_limit * 100, 1) if plan_limit else 0,
    }


@router.get("/diagnostic-types")
async def list_diagnostic_types():
    """List available automated diagnostic types."""
    return {
        "types": [
            {"id": "agent_offline", "name": "Mi agente no responde", "description": "Verifica que el agente esté activo y los canales conectados"},
            {"id": "no_leads", "name": "No llegan leads", "description": "Revisa conversaciones recientes y conectividad de canales"},
            {"id": "billing_issue", "name": "Problema de facturación", "description": "Verifica suscripción activa y uso del plan"},
            {"id": "channel_disconnect", "name": "Canal desconectado", "description": "Revisa el estado de WhatsApp, Instagram, etc."},
            {"id": "slow_ai", "name": "Respuestas AI lentas", "description": "Sugiere optimizaciones para reducir latencia"},
        ]
    }
