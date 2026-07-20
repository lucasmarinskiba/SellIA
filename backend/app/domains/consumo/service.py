"""
Consumo Service

Implements Cost Attribution, Quality Gate, Plan Recommendation,
Onboarding Guide, and Predictive Churn Shield.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from app.core.logger import get_logger
from app.domains.consumo.models import AICallLog, OnboardingProgress, ChurnRiskSignal, QualityGateConfig
from app.domains.users.models import User
from app.domains.subscriptions.models import Subscription, SubscriptionPlan, UsageTracking
from app.domains.agents.models import AgentConfig
from app.domains.channels.models import ChannelConnection, Conversation
from app.domains.businesses.models import Business

logger = get_logger(__name__)


# ===== COST ATTRIBUTION =====

async def get_cost_attribution_summary(
    db: AsyncSession,
    user_id: Optional[uuid.UUID] = None,
    business_id: Optional[uuid.UUID] = None,
    days: int = 30,
) -> Dict[str, Any]:
    """Return aggregated AI cost data."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = select(AICallLog).where(AICallLog.created_at >= since)
    if user_id:
        query = query.where(AICallLog.user_id == user_id)
    if business_id:
        query = query.where(AICallLog.business_id == business_id)

    result = await db.execute(query)
    logs = result.scalars().all()

    total_calls = len(logs)
    total_cost = sum(l.cost_usd for l in logs)
    total_input = sum(l.tokens_input for l in logs)
    total_output = sum(l.tokens_output for l in logs)
    latencies = [l.latency_ms for l in logs if l.latency_ms]
    cache_hits = sum(1 for l in logs if l.cache_hit)

    # Group by provider
    by_provider = {}
    by_model = {}
    by_task = {}
    for l in logs:
        by_provider[l.provider] = by_provider.get(l.provider, 0) + l.cost_usd
        by_model[l.model] = by_model.get(l.model, 0) + l.cost_usd
        by_task[l.task_type] = by_task.get(l.task_type, 0) + l.cost_usd

    return {
        "total_calls": total_calls,
        "total_cost_usd": round(total_cost, 4),
        "total_tokens_input": total_input,
        "total_tokens_output": total_output,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "cache_hit_rate": round(cache_hits / total_calls * 100, 1) if total_calls else 0,
        "by_provider": [{"name": k, "cost_usd": round(v, 4)} for k, v in by_provider.items()],
        "by_model": [{"name": k, "cost_usd": round(v, 4)} for k, v in by_model.items()],
        "by_task_type": [{"name": k, "cost_usd": round(v, 4)} for k, v in by_task.items()],
        "period_days": days,
    }


async def get_user_margins(db: AsyncSession, days: int = 30) -> List[Dict[str, Any]]:
    """For admin: margin analysis per user (cost vs revenue)."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            User.id,
            User.email,
            SubscriptionPlan.name,
            SubscriptionPlan.price_monthly,
            func.coalesce(func.sum(AICallLog.cost_usd), 0.0),
        )
        .join(Subscription, Subscription.user_id == User.id)
        .join(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
        .outerjoin(AICallLog, and_(AICallLog.user_id == User.id, AICallLog.created_at >= since))
        .where(Subscription.status == "active")
        .group_by(User.id, User.email, SubscriptionPlan.name, SubscriptionPlan.price_monthly)
    )

    margins = []
    for row in result.all():
        user_id, email, plan_name, plan_price, ai_cost = row
        plan_price = float(plan_price or 0)
        ai_cost = float(ai_cost or 0)
        margin = plan_price - ai_cost
        margin_pct = round(margin / plan_price * 100, 1) if plan_price else 0
        risk = "danger" if margin_pct < 20 else ("warning" if margin_pct < 50 else "healthy")
        margins.append({
            "user_id": user_id,
            "email": email,
            "plan_name": plan_name,
            "plan_price_usd": plan_price,
            "ai_cost_usd": round(ai_cost, 4),
            "margin_usd": round(margin, 4),
            "margin_percent": margin_pct,
            "risk_level": risk,
        })
    return margins


async def log_ai_call(
    db: AsyncSession,
    user_id: uuid.UUID,
    business_id: Optional[uuid.UUID],
    provider: str,
    model: str,
    task_type: str,
    tokens_input: int,
    tokens_output: int,
    cost_usd: float,
    latency_ms: Optional[float] = None,
    cache_hit: bool = False,
    was_batched: bool = False,
    metadata: Optional[Dict] = None,
):
    """Record a single AI API call with cost."""
    log = AICallLog(
        user_id=user_id,
        business_id=business_id,
        provider=provider,
        model=model,
        task_type=task_type,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        cache_hit=cache_hit,
        was_batched=was_batched,
        extra_data=metadata or {},
    )
    db.add(log)
    await db.commit()


# ===== QUALITY GATE =====

async def get_or_create_quality_gate_config(db: AsyncSession, user_id: uuid.UUID) -> QualityGateConfig:
    result = await db.execute(
        select(QualityGateConfig).where(QualityGateConfig.user_id == user_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        config = QualityGateConfig(user_id=user_id)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


async def update_quality_gate_config(
    db: AsyncSession, user_id: uuid.UUID, data: Dict[str, Any]
) -> QualityGateConfig:
    config = await get_or_create_quality_gate_config(db, user_id)
    for field, value in data.items():
        if value is not None and hasattr(config, field):
            setattr(config, field, value)
    await db.commit()
    await db.refresh(config)
    return config


# ===== PLAN RECOMMENDATION =====

async def get_plan_recommendation(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
    """Analyze usage and suggest keep/upgrade/downgrade."""
    from sqlalchemy import select

    # Get active subscription
    sub_result = await db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.user_id == user_id, Subscription.status == "active")
    )
    row = sub_result.first()
    if not row:
        return {"recommendation": "no_active_subscription", "reason": "No hay suscripción activa"}

    sub, plan = row
    plan_limits = plan.limits or {}
    ai_limit = plan_limits.get("ai_messages_monthly", 0)

    # Get 30-day usage
    since = datetime.now(timezone.utc) - timedelta(days=30)
    usage_result = await db.execute(
        select(func.sum(UsageTracking.quantity)).where(
            UsageTracking.user_id == user_id,
            UsageTracking.metric_type == "ai_messages_monthly",
            UsageTracking.created_at >= since,
        )
    )
    used = usage_result.scalar() or 0

    usage_pct = round(used / ai_limit * 100, 1) if ai_limit else 0

    # Simple logic
    if usage_pct < 30:
        rec = "downgrade"
        reason = f"Usás solo el {usage_pct}% de tu plan. Podés ahorrar bajando de plan."
    elif usage_pct > 85:
        rec = "upgrade"
        reason = f"Usás el {usage_pct}% de tu plan. Subir de plan evita cortes."
    else:
        rec = "keep"
        reason = f"Usás el {usage_pct}% de tu plan. Estás bien dimensionado."

    return {
        "current_plan": plan.name,
        "current_plan_price": float(plan.price_monthly or 0),
        "current_limit": ai_limit,
        "usage_percent": usage_pct,
        "recommendation": rec,
        "suggested_plan": None,  # Could query other plans
        "suggested_plan_price": None,
        "reason": reason,
        "estimated_savings_or_extra_cost": None,
    }


# ===== ONBOARDING =====

async def get_or_create_onboarding_progress(db: AsyncSession, user_id: uuid.UUID) -> OnboardingProgress:
    result = await db.execute(
        select(OnboardingProgress).where(OnboardingProgress.user_id == user_id)
    )
    prog = result.scalar_one_or_none()
    if not prog:
        prog = OnboardingProgress(user_id=user_id)
        db.add(prog)
        await db.commit()
        await db.refresh(prog)
    return prog


async def refresh_onboarding_progress(db: AsyncSession, user_id: uuid.UUID) -> OnboardingProgress:
    """Check actual DB state and update onboarding progress."""
    prog = await get_or_create_onboarding_progress(db, user_id)

    # Check business
    biz_result = await db.execute(
        select(func.count(Business.id)).where(Business.owner_id == user_id)
    )
    prog.business_created = (biz_result.scalar() or 0) > 0

    # Check channels
    ch_result = await db.execute(
        select(func.count(ChannelConnection.id)).where(ChannelConnection.user_id == user_id)
    )
    prog.channel_connected = (ch_result.scalar() or 0) > 0

    # Check agents
    ag_result = await db.execute(
        select(func.count(AgentConfig.id)).where(AgentConfig.user_id == user_id)
    )
    prog.agent_configured = (ag_result.scalar() or 0) > 0

    # Check conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    )
    prog.first_conversation = (conv_result.scalar() or 0) > 0

    # Calculate progress
    steps = [prog.account_created, prog.business_created, prog.channel_connected,
             prog.agent_configured, prog.first_conversation, prog.catalog_added, prog.automation_created]
    prog.progress_percent = int(sum(steps) / len(steps) * 100)

    # Determine current step
    if not prog.business_created:
        prog.current_step = "business_created"
    elif not prog.channel_connected:
        prog.current_step = "channel_connected"
    elif not prog.agent_configured:
        prog.current_step = "agent_configured"
    elif not prog.first_conversation:
        prog.current_step = "first_conversation"
    elif not prog.catalog_added:
        prog.current_step = "catalog_added"
    elif not prog.automation_created:
        prog.current_step = "automation_created"
    else:
        prog.current_step = "completed"

    await db.commit()
    await db.refresh(prog)
    return prog


async def generate_onboarding_help(db: AsyncSession, user_id: uuid.UUID, current_step: str, context: Optional[str]) -> Dict[str, Any]:
    """Generate contextual help for the current onboarding step."""
    step_guides = {
        "business_created": {
            "message": "Primero necesitás crear un negocio. Esto nos permite organizar tus canales, catálogo y agentes.",
            "action": "Ir a Negocios → Nuevo Negocio",
            "resources": ["/dashboard/negocios", "https://docs.sellia.com/crear-negocio"],
        },
        "channel_connected": {
            "message": "Conectá WhatsApp, Instagram o Telegram para que tu agente pueda recibir mensajes reales.",
            "action": "Ir a Canales → Conectar",
            "resources": ["/dashboard/canales", "https://docs.sellia.com/conectar-whatsapp"],
        },
        "agent_configured": {
            "message": "Configurá tu agente con su personalidad, tono y objetivo de venta.",
            "action": "Ir a Agentes → Configurar",
            "resources": ["/dashboard/agentes", "https://docs.sellia.com/configurar-agente"],
        },
        "first_conversation": {
            "message": "¡Excelente! Ahora probá tu agente enviándote un mensaje de prueba.",
            "action": "Ir a Conversaciones → Nueva Prueba",
            "resources": ["/dashboard/conversaciones", "https://docs.sellia.com/probar-agente"],
        },
        "catalog_added": {
            "message": "Agregá productos a tu catálogo para que el agente pueda venderlos.",
            "action": "Ir a Catálogo → Nuevo Producto",
            "resources": ["/dashboard/catalogo", "https://docs.sellia.com/catalogo"],
        },
        "automation_created": {
            "message": "Creá tu primera automatización para responder cuando no estés.",
            "action": "Ir a Automatizaciones → Nueva",
            "resources": ["/dashboard/automatizaciones", "https://docs.sellia.com/automatizaciones"],
        },
        "completed": {
            "message": "¡Felicitaciones! Tenés todo configurado. Revisá el panel de analytics para ver resultados.",
            "action": "Ir a Analytics",
            "resources": ["/dashboard/analytics", "https://docs.sellia.com/analytics"],
        },
    }

    guide = step_guides.get(current_step, step_guides["business_created"])

    # Update intervention count
    prog = await get_or_create_onboarding_progress(db, user_id)
    prog.ai_interventions_count += 1
    prog.help_requested_at = datetime.now(timezone.utc)
    prog.help_context = context
    await db.commit()

    return {
        "message": guide["message"],
        "suggested_action": guide["action"],
        "resources": guide["resources"],
    }


# ===== PREDICTIVE CHURN SHIELD =====

async def run_churn_analysis(db: AsyncSession) -> List[ChurnRiskSignal]:
    """Analyze all active users for churn risk signals. Runs daily via Celery."""
    from sqlalchemy import select

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)

    # Get all active subscriptions
    result = await db.execute(
        select(User, Subscription, SubscriptionPlan)
        .join(Subscription, Subscription.user_id == User.id)
        .join(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
        .where(Subscription.status == "active")
    )
    rows = result.all()

    signals_created = []
    for user, sub, plan in rows:
        signals = []
        score = 0.0

        # Signal 1: Agent inactive
        agent_result = await db.execute(
            select(AgentConfig).where(
                AgentConfig.user_id == user.id,
                AgentConfig.is_active == True,
            )
        )
        has_active_agent = agent_result.scalar_one_or_none() is not None
        if not has_active_agent:
            signals.append({"type": "agent_inactive", "value": True, "weight": 0.30})
            score += 0.30

        # Signal 2: Zero conversations in 7 days
        conv_result = await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.user_id == user.id,
                Conversation.created_at >= since,
            )
        )
        conv_count = conv_result.scalar() or 0
        if conv_count == 0:
            signals.append({"type": "zero_conversations_7d", "value": True, "weight": 0.25})
            score += 0.25

        # Signal 3: Zero leads/messages
        msg_result = await db.execute(
            select(func.count(UsageTracking.id)).where(
                UsageTracking.user_id == user.id,
                UsageTracking.created_at >= since,
            )
        )
        msg_count = msg_result.scalar() or 0
        if msg_count == 0:
            signals.append({"type": "zero_usage_7d", "value": True, "weight": 0.20})
            score += 0.20

        # Signal 4: Billing due soon (within 7 days)
        if sub.current_period_end and sub.current_period_end <= now + timedelta(days=7):
            signals.append({"type": "billing_due_soon", "value": True, "weight": 0.15})
            score += 0.15

        # Signal 5: No channel connected
        ch_result = await db.execute(
            select(func.count(ChannelConnection.id)).where(
                ChannelConnection.user_id == user.id,
                ChannelConnection.is_active == True,
            )
        )
        ch_count = ch_result.scalar() or 0
        if ch_count == 0:
            signals.append({"type": "no_channels", "value": True, "weight": 0.10})
            score += 0.10

        if score >= 0.40:
            level = "critical" if score >= 0.70 else ("high" if score >= 0.55 else "medium")
            risk = ChurnRiskSignal(
                user_id=user.id,
                business_id=sub.business_id,
                risk_score=round(score, 2),
                risk_level=level,
                signals=signals,
                action_taken=None,
            )
            db.add(risk)
            signals_created.append(risk)
            logger.info(f"Churn risk detected for user {user.id}: score={score}, level={level}")

    await db.commit()
    return signals_created


async def get_pending_churn_signals(db: AsyncSession, limit: int = 50) -> List[ChurnRiskSignal]:
    """Get unresolved churn signals for admin action."""
    result = await db.execute(
        select(ChurnRiskSignal)
        .where(ChurnRiskSignal.resolved == False)
        .order_by(desc(ChurnRiskSignal.risk_score))
        .limit(limit)
    )
    return result.scalars().all()



# ===== CONSUMO ADVANCED ANALYTICS =====

async def get_usage_heatmap(db: AsyncSession, user_id: uuid.UUID, days: int = 30) -> List[Dict[str, Any]]:
    """Return AI usage heatmap by hour of day and day of week."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(AICallLog).where(
            AICallLog.user_id == user_id,
            AICallLog.created_at >= since,
        )
    )
    logs = result.scalars().all()

    # Initialize heatmap matrix (7 days x 24 hours)
    heatmap = {}
    for log in logs:
        dt = log.created_at.astimezone(timezone.utc)
        day = dt.strftime("%A")  # Monday, Tuesday, etc.
        hour = dt.hour
        key = f"{day}_{hour}"
        if key not in heatmap:
            heatmap[key] = {"day": day, "hour": hour, "calls": 0, "cost": 0.0}
        heatmap[key]["calls"] += 1
        heatmap[key]["cost"] += log.cost_usd

    return list(heatmap.values())


async def get_monthly_comparison(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
    """Compare current month vs previous month."""
    now = datetime.now(timezone.utc)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

    async def get_month_stats(start: datetime, end: datetime):
        result = await db.execute(
            select(AICallLog).where(
                AICallLog.user_id == user_id,
                AICallLog.created_at >= start,
                AICallLog.created_at < end,
            )
        )
        logs = result.scalars().all()
        return {
            "calls": len(logs),
            "cost": round(sum(l.cost_usd for l in logs), 4),
            "tokens_input": sum(l.tokens_input for l in logs),
            "tokens_output": sum(l.tokens_output for l in logs),
            "avg_latency": round(sum(l.latency_ms for l in logs if l.latency_ms) / max(len([l for l in logs if l.latency_ms]), 1), 2),
        }

    current = await get_month_stats(current_month_start, now)
    previous = await get_month_stats(prev_month_start, current_month_start)

    def pct_change(curr, prev):
        if prev == 0:
            return 100 if curr > 0 else 0
        return round((curr - prev) / prev * 100, 1)

    return {
        "current_month": current,
        "previous_month": previous,
        "changes": {
            "calls": pct_change(current["calls"], previous["calls"]),
            "cost": pct_change(current["cost"], previous["cost"]),
            "tokens_input": pct_change(current["tokens_input"], previous["tokens_input"]),
        },
        "trend": "up" if current["cost"] > previous["cost"] else "down" if current["cost"] < previous["cost"] else "stable",
    }


async def get_cost_per_lead(db: AsyncSession, user_id: uuid.UUID, days: int = 30) -> Dict[str, Any]:
    """Calculate AI cost per lead and per conversation."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Get AI costs
    cost_result = await db.execute(
        select(func.coalesce(func.sum(AICallLog.cost_usd), 0.0)).where(
            AICallLog.user_id == user_id,
            AICallLog.created_at >= since,
        )
    )
    total_cost = float(cost_result.scalar() or 0)

    # Get leads (conversations)
    conv_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id,
            Conversation.created_at >= since,
        )
    )
    total_conversations = conv_result.scalar() or 0

    # Get messages
    from app.domains.channels.models import Message
    msg_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.user_id == user_id,
            Message.created_at >= since,
        )
    )
    total_messages = msg_result.scalar() or 0

    return {
        "total_cost": round(total_cost, 4),
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "cost_per_conversation": round(total_cost / max(total_conversations, 1), 4),
        "cost_per_message": round(total_cost / max(total_messages, 1), 4),
        "period_days": days,
    }
