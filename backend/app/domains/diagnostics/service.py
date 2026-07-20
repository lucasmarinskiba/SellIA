"""
Auto-Diagnosis Service

Runs automated checks for common user problems and returns
actionable recommendations.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.logger import get_logger
from app.domains.diagnostics.models import DiagnosticRun
from app.domains.channels.models import ChannelConnection
from app.domains.channels.models import Conversation, Message
from app.domains.subscriptions.models import Subscription, UsageTracking
from app.domains.agents.models import AgentConfig

logger = get_logger(__name__)


async def run_diagnostic(
    db: AsyncSession,
    user_id: uuid.UUID,
    diagnostic_type: str,
) -> DiagnosticRun:
    """Run an automated diagnostic and return findings."""
    run = DiagnosticRun(
        user_id=user_id,
        diagnostic_type=diagnostic_type,
        status="running",
        findings=[],
        recommendations=[],
        severity="info",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    try:
        if diagnostic_type == "agent_offline":
            await _diag_agent_offline(db, user_id, run)
        elif diagnostic_type == "no_leads":
            await _diag_no_leads(db, user_id, run)
        elif diagnostic_type == "billing_issue":
            await _diag_billing(db, user_id, run)
        elif diagnostic_type == "channel_disconnect":
            await _diag_channels(db, user_id, run)
        elif diagnostic_type == "slow_ai":
            await _diag_slow_ai(db, user_id, run)
        else:
            run.findings.append({"message": f"Tipo de diagnóstico '{diagnostic_type}' no implementado"})
            run.severity = "info"

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(run)

    except Exception as exc:
        run.status = "failed"
        run.findings.append({"message": f"Error en diagnóstico: {str(exc)}"})
        run.severity = "critical"
        run.completed_at = datetime.now(timezone.utc)
        await db.commit()
        logger.exception(f"Diagnostic {diagnostic_type} failed for user {user_id}")

    return run


async def _diag_agent_offline(db: AsyncSession, user_id: uuid.UUID, run: DiagnosticRun):
    agents = await db.execute(
        select(AgentConfig).where(AgentConfig.user_id == user_id)
    )
    agents = agents.scalars().all()

    if not agents:
        run.findings.append({"check": "agents_exist", "status": "fail", "message": "No tenés agentes configurados"})
        run.recommendations.append({"action": "Crear un agente en /agents/new", "type": "create_agent"})
        run.severity = "critical"
        return

    for agent in agents:
        status = "ok" if agent.is_active else "fail"
        run.findings.append({
            "check": f"agent_{agent.id}",
            "status": status,
            "message": f"Agente '{agent.name}' está {'activo' if agent.is_active else 'inactivo'}",
        })
        if not agent.is_active:
            run.recommendations.append({
                "action": f"Activar el agente '{agent.name}'",
                "type": "toggle_agent",
                "agent_id": str(agent.id),
            })
            run.severity = "warning"

    # Check if channels are connected
    channels = await db.execute(
        select(ChannelConnection).where(ChannelConnection.user_id == user_id)
    )
    channels = channels.scalars().all()
    if not channels:
        run.findings.append({"check": "channels", "status": "fail", "message": "No hay canales conectados (WhatsApp, Instagram, etc.)"})
        run.recommendations.append({"action": "Conectar un canal en /channels", "type": "connect_channel"})
        run.severity = "critical"


async def _diag_no_leads(db: AsyncSession, user_id: uuid.UUID, run: DiagnosticRun):
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(days=7)
    convs = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id,
            Conversation.created_at >= since,
        )
    )
    count = convs.scalar() or 0

    run.findings.append({"check": "conversations_7d", "status": "ok" if count > 0 else "warning", "value": count})

    if count == 0:
        run.recommendations.append({"action": "Verificar que tus canales estén conectados y el agente activo", "type": "check_channels"})
        run.recommendations.append({"action": "Revisar la configuración de webhooks en Meta/Instagram", "type": "check_webhooks"})
        run.severity = "warning"


async def _diag_billing(db: AsyncSession, user_id: uuid.UUID, run: DiagnosticRun):
    sub = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        )
    )
    sub = sub.scalar_one_or_none()

    if not sub:
        run.findings.append({"check": "subscription", "status": "fail", "message": "No hay suscripción activa"})
        run.recommendations.append({"action": "Suscribirse a un plan en /subscriptions", "type": "subscribe"})
        run.severity = "critical"
        return

    run.findings.append({"check": "subscription", "status": "ok", "message": f"Plan activo: {sub.plan_id}"})

    # Check usage
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(days=30)
    usage = await db.execute(
        select(func.sum(UsageTracking.ai_messages_used)).where(
            UsageTracking.user_id == user_id,
            UsageTracking.created_at >= since,
        )
    )
    used = usage.scalar() or 0
    run.findings.append({"check": "usage_30d", "status": "ok", "value": int(used)})


async def _diag_channels(db: AsyncSession, user_id: uuid.UUID, run: DiagnosticRun):
    channels = await db.execute(
        select(ChannelConnection).where(ChannelConnection.user_id == user_id)
    )
    channels = channels.scalars().all()

    for ch in channels:
        status = "ok" if ch.is_active else "fail"
        run.findings.append({
            "check": f"channel_{ch.channel_type}",
            "status": status,
            "message": f"Canal {ch.channel_type}: {'conectado' if ch.is_active else 'desconectado'}",
        })
        if not ch.is_active:
            run.recommendations.append({
                "action": f"Reconectar {ch.channel_type}",
                "type": "reconnect_channel",
                "channel_id": str(ch.id),
            })
            run.severity = "warning"


async def _diag_slow_ai(db: AsyncSession, user_id: uuid.UUID, run: DiagnosticRun):
    run.findings.append({"check": "ai_latency", "status": "info", "message": "Revisar latencia de respuestas AI"})
    run.recommendations.append({"action": "Activar Semantic Cache en /settings/ai para reducir latencia", "type": "enable_cache"})
    run.recommendations.append({"action": "Verificar que Ollama local esté corriendo (si está configurado)", "type": "check_ollama"})
