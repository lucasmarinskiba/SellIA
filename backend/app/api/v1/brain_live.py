"""Brain Live — real aggregate data for the SellIA Brain ops dashboard.

Every endpoint here reads from actual database tables (leads, computer-use
audit log). Nothing here fabricates numbers: an empty result means no
activity has happened yet, not a fake fallback.

This is a public ops/command-center dashboard (no per-visitor auth), so
these endpoints intentionally read across all records rather than scoping
to a single signed-in user like the per-user /audit-logs endpoints do.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal as LeadsSessionLocal
from app.db.models import Lead as LeadModel
from app.core.database import get_db

router = APIRouter(tags=["brain-live"])


async def _query_audit_logs(**filters):
    """Best-effort query of the computer-use audit log table.

    This table has a dangling FK to a "user" table that doesn't exist in
    this codebase's schema, so on some deployments the table itself may
    not exist yet. Returns [] instead of 500ing in that case — an empty
    audit trail is a true state, a crashed dashboard is not.
    """
    try:
        from app.core.database import AsyncSessionLocal as AuditSessionLocal
        from app.domains.computer_use.models_audit_log import ComputerUseAuditLog

        async with AuditSessionLocal() as db:
            query = select(ComputerUseAuditLog).order_by(desc(ComputerUseAuditLog.created_at))
            if filters.get("status"):
                query = query.where(ComputerUseAuditLog.status == filters["status"])
            if filters.get("platforms"):
                query = query.where(ComputerUseAuditLog.platform.in_(filters["platforms"]))
            query = query.limit(filters.get("limit", 50))
            result = await db.execute(query)
            return result.scalars().all(), None
    except Exception as e:
        return [], str(e)


# ── Source → Squad mapping (real leads, grouped by real acquisition channel) ──
SQUAD_MAP = {
    "linkedin": "sdr",
    "cold-email": "sdr",
    "referral": "sdr",
    "website": "ads",
    "manual": "cs",
}
SQUAD_LABELS = {
    "sdr": {"name": "SDR · Outbound", "color": "#06B6D4"},
    "ads": {"name": "Ads · Growth", "color": "#8B5CF6"},
    "cs": {"name": "Customer Success", "color": "#10B981"},
}


def _squad_for(source: Optional[str]) -> str:
    return SQUAD_MAP.get((source or "").lower(), "ads")


_PLATFORM_LABELS = {
    "whatsapp": "WhatsApp", "email": "Email", "instagram": "Instagram",
    "mercadolibre": "MercadoLibre", "amazon": "Amazon", "beacons": "Beacons",
    "linkedin": "LinkedIn", "telegram": "Telegram", "webchat": "Web",
    "messenger": "Messenger", "facebook_ads": "Facebook Ads", "meta_ads": "Meta Ads",
    "google_ads": "Google Ads", "shopify": "Shopify", "tiktok": "TikTok",
    "tiktok_ads": "TikTok Ads", "tiktok_shop": "TikTok Shop", "twitter": "Twitter/X",
    "threads": "Threads", "hotmart": "Hotmart",
}

# app.domains.computer_use.models_audit_log's platform strings -> squad the
# frontend already knows how to badge (see SQUAD_MAP/SQUAD_LABELS above).
_CU_PLATFORM_TO_SQUAD = {"whatsapp": "sdr", "instagram": "sdr", "website": "ads"}


async def _real_user_notifications(user, limit: int) -> list[dict]:
    """Aggregate real events across every source that actually exists for
    THIS user's account: AI agent/automation actions, inbound customer
    messages from any connected channel (WhatsApp, Instagram, MercadoLibre,
    Amazon, Hotmart, ...), pending Computer Use approvals, and deals won.
    Each source is best-effort -- one broken query must never blank the
    whole bell, same isolation rule as the rest of this file.
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.ai_activity.models import AIActionLog
    from app.domains.channels.models import Conversation, Message, MessageDirection, ChannelConnection
    from app.domains.businesses.models import Business
    from app.domains.crm.models import Deal, LeadStage

    notifications: list[dict] = []

    async with AsyncSessionLocal() as db:
        biz_result = await db.execute(select(Business.id).where(Business.user_id == user.id))
        business_ids = [b for (b,) in biz_result.all()] if biz_result else []

        # 1) Real AI agent/automation/brain actions (app.domains.ai_activity)
        try:
            result = await db.execute(
                select(AIActionLog)
                .where(AIActionLog.user_id == user.id)
                .order_by(desc(AIActionLog.created_at))
                .limit(limit)
            )
            for row in result.scalars().all():
                kind = "alert" if row.status == "failed" else "action"
                notifications.append({
                    "id": f"ai-{row.id}",
                    "ts": row.created_at.isoformat(),
                    "kind": kind,
                    "title": row.summary[:120],
                    "body": f"{row.actor_type} · {row.action}" + (" · falló" if row.status == "failed" else ""),
                    "agent": "cua" if row.actor_type == "brain" else row.actor_type,
                    "read": False,
                })
        except Exception:
            pass

        # 2) Real inbound customer messages across every connected channel
        if business_ids:
            try:
                result = await db.execute(
                    select(Message, Conversation, ChannelConnection)
                    .join(Conversation, Message.conversation_id == Conversation.id)
                    .outerjoin(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
                    .where(Conversation.business_id.in_(business_ids))
                    .where(Message.direction == MessageDirection.INBOUND)
                    .order_by(desc(Message.created_at))
                    .limit(limit)
                )
                for msg, conv, channel in result.all():
                    platform = channel.platform.value if channel and channel.platform else "webchat"
                    label = _PLATFORM_LABELS.get(platform, platform.title())
                    notifications.append({
                        "id": f"msg-{msg.id}",
                        "ts": msg.created_at.isoformat(),
                        "kind": "info",
                        "title": f"Mensaje de {conv.lead_name or 'un cliente'} · {label}",
                        "body": (msg.content or "")[:140],
                        "agent": _CU_PLATFORM_TO_SQUAD.get(platform, "sdr"),
                        "read": False,
                    })
            except Exception:
                pass

            # 3) Real deals won
            try:
                result = await db.execute(
                    select(Deal)
                    .where(Deal.business_id.in_(business_ids))
                    .where(Deal.stage == LeadStage.CLOSED_WON)
                    .order_by(desc(Deal.updated_at))
                    .limit(limit)
                )
                for deal in result.scalars().all():
                    value = f"${deal.value:,.0f} {deal.currency}" if deal.value else "sin valor cargado"
                    notifications.append({
                        "id": f"deal-{deal.id}",
                        "ts": deal.updated_at.isoformat(),
                        "kind": "win",
                        "title": f"Deal cerrado · {deal.title}",
                        "body": f"{deal.contact_name or 'Cliente'} · {value}",
                        "agent": "cs",
                        "read": False,
                    })
            except Exception:
                pass

    # 4) Real pending Computer Use approvals (already user-scoped)
    try:
        cu_logs, _err = await _query_audit_logs(status="pending_approval", limit=limit)
        for log in cu_logs:
            if str(getattr(log, "user_id", "")) != str(user.id):
                continue
            platform = getattr(log, "platform", None) or "website"
            label = _PLATFORM_LABELS.get(platform, platform.title())
            notifications.append({
                "id": f"cu-{log.id}",
                "ts": log.created_at.isoformat(),
                "kind": "approval",
                "title": f"Aprobación pendiente · {label}",
                "body": getattr(log, "action_type", None) or "Acción de Computer Use requiere revisión",
                "agent": _CU_PLATFORM_TO_SQUAD.get(platform, "cua"),
                "read": False,
            })
    except Exception:
        pass

    notifications.sort(key=lambda n: n["ts"], reverse=True)
    return notifications[:limit]


async def _public_lead_notifications(limit: int) -> list[dict]:
    """Fallback for anonymous/demo visitors: the original global, unscoped
    feed derived from lead activity. Kept as-is for the public ops dashboard
    (see module docstring) -- a real per-user account gets _real_user_notifications
    instead, which is what actually answers "what has SellIA done for ME"."""
    async with LeadsSessionLocal() as db:
        result = await db.execute(
            select(LeadModel)
            .where(LeadModel.deleted_at.is_(None))
            .order_by(desc(LeadModel.updated_at))
            .limit(limit)
        )
        leads = result.scalars().all()

    notifications = []
    for lead in leads:
        is_new = lead.created_at == lead.updated_at
        if lead.status == "won":
            kind, title = "win", f"Deal cerrado · {lead.company or lead.name}"
            body = f"Valor estimado ${lead.budget:,.0f}" if lead.budget else "Deal ganado"
        elif lead.status == "qualified":
            kind, title = "action", f"Lead calificado · {lead.name}"
            body = f"Score {lead.score:.0f} · {lead.company or 'sin empresa'}"
        elif is_new:
            kind, title = "info", f"Nuevo prospecto · {lead.name}"
            body = f"Fuente: {lead.source or 'desconocida'}"
        else:
            kind, title = "action", f"Actualización · {lead.name}"
            body = f"Estado: {lead.status}"

        notifications.append({
            "id": f"lead-{lead.id}-{int(lead.updated_at.timestamp())}",
            "ts": lead.updated_at.isoformat(),
            "kind": kind,
            "title": title,
            "body": body,
            "agent": _squad_for(lead.source),
            "read": False,
        })

    return notifications


@router.get("/notifications")
async def get_notifications(
    request: Request,
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Real notifications. A signed-in caller (Bearer token) gets a feed
    aggregated across everything that's actually happened on their own
    account: AI agent/automation actions, inbound messages from customers
    on any connected channel (WhatsApp, Instagram, MercadoLibre, Amazon,
    Hotmart, ...), pending approvals, deals won. An anonymous caller (the
    public ops dashboard) gets the original global lead-activity feed.
    """
    from app.api.v1.brain import _optional_user
    user = await _optional_user(request, db)
    if user is not None:
        notifications = await _real_user_notifications(user, limit)
    else:
        notifications = await _public_lead_notifications(limit)

    return {"notifications": notifications}


@router.get("/squads")
async def get_squads():
    """Real squad performance, aggregated from actual lead counts/scores by source."""
    async with LeadsSessionLocal() as db:
        result = await db.execute(
            select(
                LeadModel.source,
                func.count(LeadModel.id).label("total"),
                func.avg(LeadModel.score).label("avg_score"),
                func.sum(func.coalesce(LeadModel.budget, 0)).label("pipeline_value"),
            )
            .where(LeadModel.deleted_at.is_(None))
            .group_by(LeadModel.source)
        )
        rows = result.all()

        won_result = await db.execute(
            select(LeadModel.source, func.count(LeadModel.id))
            .where(LeadModel.deleted_at.is_(None), LeadModel.status == "won")
            .group_by(LeadModel.source)
        )
        won_by_source = dict(won_result.all())

    squads: dict[str, dict] = {}
    for source, total, avg_score, pipeline_value in rows:
        squad_key = _squad_for(source)
        bucket = squads.setdefault(squad_key, {
            "id": squad_key,
            "name": SQUAD_LABELS[squad_key]["name"],
            "color": SQUAD_LABELS[squad_key]["color"],
            "leads": 0,
            "won": 0,
            "avg_score": 0.0,
            "pipeline_value": 0.0,
        })
        bucket["leads"] += total or 0
        bucket["won"] += won_by_source.get(source, 0)
        bucket["pipeline_value"] += float(pipeline_value or 0)
        bucket["avg_score"] = round(float(avg_score or 0), 1)

    for bucket in squads.values():
        bucket["conversion_rate"] = round(
            (bucket["won"] / bucket["leads"] * 100) if bucket["leads"] else 0, 1
        )

    return {"squads": list(squads.values())}


@router.get("/kpis")
async def get_kpis():
    """Real, honestly-computable KPIs from the leads table.

    No ROI/ad-spend figure is included — nothing in this codebase tracks
    marketing spend, so a "ROI" number would have to be invented. Everything
    below is a direct aggregate of real lead rows.
    """
    async with LeadsSessionLocal() as db:
        total_result = await db.execute(
            select(func.count(LeadModel.id)).where(LeadModel.deleted_at.is_(None))
        )
        total = total_result.scalar() or 0

        won_result = await db.execute(
            select(func.count(LeadModel.id)).where(
                LeadModel.deleted_at.is_(None), LeadModel.status == "won"
            )
        )
        won = won_result.scalar() or 0

        active_result = await db.execute(
            select(func.count(LeadModel.id)).where(
                LeadModel.deleted_at.is_(None),
                LeadModel.status.notin_(["won", "lost"]),
            )
        )
        active = active_result.scalar() or 0

        pipeline_result = await db.execute(
            select(func.sum(func.coalesce(LeadModel.budget, 0))).where(
                LeadModel.deleted_at.is_(None),
                LeadModel.status.notin_(["won", "lost"]),
            )
        )
        pipeline_value = float(pipeline_result.scalar() or 0)

        avg_score_result = await db.execute(
            select(func.avg(LeadModel.score)).where(LeadModel.deleted_at.is_(None))
        )
        avg_score = float(avg_score_result.scalar() or 0)

    return {
        "total_leads": total,
        "won_leads": won,
        "active_leads": active,
        "conversion_rate": round((won / total * 100) if total else 0, 1),
        "pipeline_value": pipeline_value,
        "avg_lead_score": round(avg_score, 1),
    }


@router.get("/pipeline-summary")
async def get_pipeline_summary():
    """Real pipeline totals by status, for the sales pipeline widget."""
    async with LeadsSessionLocal() as db:
        result = await db.execute(
            select(
                LeadModel.status,
                func.count(LeadModel.id),
                func.sum(func.coalesce(LeadModel.budget, 0)),
            )
            .where(LeadModel.deleted_at.is_(None))
            .group_by(LeadModel.status)
        )
        rows = result.all()

    return {
        "by_status": [
            {"status": status, "count": count, "value": float(value or 0)}
            for status, count, value in rows
        ]
    }


def _serialize_audit_log(log) -> dict:
    return {
        "id": log.id,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "platform": log.platform,
        "action_type": log.action_type,
        "agent_name": log.agent_name,
        "strategy_name": log.strategy_name,
        "confidence_score": log.confidence_score,
        "status": log.status,
        "requires_approval": log.requires_approval,
        "input_data": log.input_data,
        "output_data": log.output_data,
        "error_message": log.error_message,
    }


@router.get("/audit-log")
async def get_audit_log(limit: int = Query(default=50, ge=1, le=200)):
    """Real agent audit trail, platform-wide (not scoped to one signed-in user)."""
    logs, error = await _query_audit_logs(limit=limit)
    return {"logs": [_serialize_audit_log(l) for l in logs], "unavailable": error is not None}


@router.get("/audit-log/pending")
async def get_pending_approvals():
    """Real actions awaiting human approval, platform-wide."""
    logs, error = await _query_audit_logs(status="pending_approval", limit=100)
    return {"logs": [_serialize_audit_log(l) for l in logs], "unavailable": error is not None}


class ApprovalDecision(BaseModel):
    reason: Optional[str] = None


@router.post("/audit-log/{log_id}/approve")
async def approve_action(log_id: str):
    try:
        from app.core.database import AsyncSessionLocal as AuditSessionLocal
        from app.domains.computer_use.services.audit_log_service import get_audit_log_service

        async with AuditSessionLocal() as db:
            service = get_audit_log_service(db)
            log = await service.get_by_id(log_id)
            if not log:
                raise HTTPException(status_code=404, detail="Audit log not found")
            updated = await service.approve(log_id, "brain-dashboard")
            return _serialize_audit_log(updated)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit-log/{log_id}/reject")
async def reject_action(log_id: str, decision: ApprovalDecision):
    try:
        from app.core.database import AsyncSessionLocal as AuditSessionLocal
        from app.domains.computer_use.services.audit_log_service import get_audit_log_service

        async with AuditSessionLocal() as db:
            service = get_audit_log_service(db)
            log = await service.get_by_id(log_id)
            if not log:
                raise HTTPException(status_code=404, detail="Audit log not found")
            updated = await service.reject(log_id, "brain-dashboard", decision.reason)
            return _serialize_audit_log(updated)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


HANDOFF_PLATFORMS = ["slack", "whatsapp", "email"]


@router.get("/handoff-log")
async def get_handoff_log(limit: int = Query(default=50, ge=1, le=200)):
    """Real agent-to-human handoff events (Slack/WhatsApp/email escalations)."""
    logs, error = await _query_audit_logs(platforms=HANDOFF_PLATFORMS, limit=limit)
    return {"logs": [_serialize_audit_log(l) for l in logs], "unavailable": error is not None}
