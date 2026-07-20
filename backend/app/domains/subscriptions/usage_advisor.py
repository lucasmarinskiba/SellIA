"""
Usage Advisor — Proactive cost optimization for the end-user.

Analyzes consumption patterns and suggests optimizations to reduce
their bill and improve efficiency.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.logger import get_logger
from app.domains.subscriptions.models import UsageTracking, Subscription, SubscriptionPlan
from app.domains.conversations.models import Conversation, Message
from app.domains.users.models import User

logger = get_logger(__name__)


class UsageAdvice:
    def __init__(self, type: str, title: str, description: str, potential_savings: str, action_link: Optional[str] = None):
        self.type = type
        self.title = title
        self.description = description
        self.potential_savings = potential_savings
        self.action_link = action_link

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "potential_savings": self.potential_savings,
            "action_link": self.action_link,
        }


async def get_usage_advice(db: AsyncSession, user_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Generate personalized cost/usage advice for a user."""
    advice: List[UsageAdvice] = []

    # 1. Check if near plan limits
    subscription = await _get_active_subscription(db, user_id)
    if subscription:
        plan = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
        )
        plan = plan.scalar_one_or_none()

        if plan:
            usage = await _get_recent_usage(db, user_id, days=30)

            # Advice: near limit
            if usage["ai_messages"] > plan.ai_message_limit * 0.8:
                advice.append(UsageAdvice(
                    type="warning",
                    title="Estás cerca del límite de mensajes AI",
                    description=f"Usaste {usage['ai_messages']} de {plan.ai_message_limit} mensajes este mes. Considerá optimizar tus prompts o subir de plan.",
                    potential_savings="Evitar interrupciones",
                    action_link="/subscriptions/upgrade",
                ))

            # Advice: underutilized plan
            if usage["ai_messages"] < plan.ai_message_limit * 0.2 and plan.price > 0:
                advice.append(UsageAdvice(
                    type="suggestion",
                    title="Tu plan tiene mucho margen sin usar",
                    description=f"Usaste solo el {usage['ai_messages']/plan.ai_message_limit*100:.0f}% de tu plan. Podés bajar de plan y ahorrar.",
                    potential_savings=f"${plan.price * 0.5:.0f}/mes aprox.",
                    action_link="/subscriptions/change",
                ))

    # 2. Check conversation efficiency
    conv_stats = await _get_conversation_stats(db, user_id, days=7)
    if conv_stats["avg_ai_turns_per_conversation"] > 3:
        advice.append(UsageAdvice(
            type="optimization",
            title="Tus agentes usan muchos turnos AI por conversación",
            description="Cada conversación genera ~{:.0f} consultas al modelo. Activá 'Modo Conciso' en la configuración del agente para reducir a 1-2 turnos.".format(conv_stats["avg_ai_turns_per_conversation"]),
            potential_savings="~40% menos tokens AI",
            action_link="/agents/settings",
        ))

    # 3. Check for duplicate/inefficient content generation
    recent_generations = await _get_recent_generations(db, user_id, days=7)
    if recent_generations > 50:
        advice.append(UsageAdvice(
            type="optimization",
            title="Generás mucho contenido manualmente",
            description=f"Creaste {recent_generations} piezas de contenido esta semana. Usá el Batch Generator para crear 20 en 1 solo request y ahorrá hasta 60%.",
            potential_savings="~60% en generación de contenido",
            action_link="/content/batch",
        ))

    # 4. Semantic cache benefit estimate
    cache_hit_rate = await _get_cache_hit_rate(user_id)
    if cache_hit_rate < 0.2:
        advice.append(UsageAdvice(
            type="optimization",
            title="Activá el Cache Semántico para FAQs",
            description="Muchas preguntas de tus clientes se repiten. El cache semántico responde las similares sin llamar a la API.",
            potential_savings="~30% menos llamadas AI",
            action_link="/settings/ai",
        ))

    return [a.to_dict() for a in advice]


async def _get_active_subscription(db: AsyncSession, user_id: uuid.UUID) -> Optional[Subscription]:
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def _get_recent_usage(db: AsyncSession, user_id: uuid.UUID, days: int) -> Dict[str, int]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(func.sum(UsageTracking.ai_messages_used)).where(
            UsageTracking.user_id == user_id,
            UsageTracking.created_at >= since,
        )
    )
    total = result.scalar() or 0
    return {"ai_messages": int(total)}


async def _get_conversation_stats(db: AsyncSession, user_id: uuid.UUID, days: int) -> Dict[str, float]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id,
            Conversation.created_at >= since,
        )
    )
    conv_count = result.scalar() or 0

    result = await db.execute(
        select(func.count(Message.id)).where(
            Message.sender == "ai",
            Message.created_at >= since,
        )
    )
    ai_messages = result.scalar() or 0

    avg = ai_messages / conv_count if conv_count > 0 else 0.0
    return {"avg_ai_turns_per_conversation": avg}


async def _get_recent_generations(db: AsyncSession, user_id: uuid.UUID, days: int) -> int:
    # Placeholder: in production this would count GeneratedContent rows
    # For now, return 0 so it doesn't trigger unless real data exists
    from app.domains.automations.models import GeneratedContent
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(func.count(GeneratedContent.id)).where(
            GeneratedContent.created_at >= since,
        )
    )
    return result.scalar() or 0


async def _get_cache_hit_rate(user_id: uuid.UUID) -> float:
    """Fetch semantic cache hit rate from Redis metrics."""
    try:
        import redis.asyncio as redis
        from app.core.config import get_settings
        r = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
        hits = int(await r.get("sellia:metrics:semantic_cache:hits") or 0)
        misses = int(await r.get("sellia:metrics:semantic_cache:misses") or 0)
        await r.close()
        total = hits + misses
        return hits / total if total > 0 else 0.0
    except Exception:
        return 0.0
