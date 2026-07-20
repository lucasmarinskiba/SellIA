"""
Smart Ticket Auto-Resolution

Automatically closes tickets that were resolved by AI without
human intervention, reducing support backlog.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.logger import get_logger
from app.domains.support.models import SupportTicket, TicketStatus
from app.domains.support.ai_responder import generate_ai_response

logger = get_logger(__name__)

# Simple gratitude / closure keywords in Spanish and English
_CLOSURE_KEYWORDS = [
    "gracias", "thank", "thanks", "perfecto", "perfect", "excelente", "great",
    "resuelto", "solved", "solucionado", "fixed", "ok", "oki", "listo", "done",
    "cerrar", "close", "cierren", "no necesito más", "that's all",
]


async def auto_resolve_tickets(db: AsyncSession):
    """
    Periodic task (Celery Beat) that auto-closes resolved tickets.
    Should run every 6 hours.
    """
    now = datetime.now(timezone.utc)

    # 1. Close tickets where AI responded with high confidence and user said "thanks"
    result = await db.execute(
        select(SupportTicket).where(
            SupportTicket.status == TicketStatus.OPEN,
            SupportTicket.ai_response_confidence >= 0.85,
            SupportTicket.last_customer_reply_at <= now - timedelta(hours=24),
        )
    )
    old_ai_resolved = result.scalars().all()

    for ticket in old_ai_resolved:
        ticket.status = TicketStatus.CLOSED
        ticket.resolved_at = now
        ticket.resolution_notes = "Auto-cerrado: respuesta AI aceptada sin réplica del usuario en 24h"
        logger.info(f"Auto-closed ticket {ticket.id} (AI resolved, no user reply)")

    # 2. Close tickets where last customer message contains closure keywords
    # (and AI already responded)
    result = await db.execute(
        select(SupportTicket).where(
            SupportTicket.status == TicketStatus.OPEN,
            SupportTicket.ai_response_at.isnot(None),
            SupportTicket.last_customer_reply_at.isnot(None),
        )
    )
    all_open = result.scalars().all()

    for ticket in all_open:
        last_reply = ticket.last_customer_reply or ""
        lower_reply = last_reply.lower()
        if any(kw in lower_reply for kw in _CLOSURE_KEYWORDS):
            ticket.status = TicketStatus.CLOSED
            ticket.resolved_at = now
            ticket.resolution_notes = "Auto-cerrado: usuario confirmó resolución"
            logger.info(f"Auto-closed ticket {ticket.id} (user confirmed resolution)")

    await db.commit()


async def get_auto_resolution_stats(db: AsyncSession, days: int = 30) -> dict:
    """Return metrics on auto-resolved tickets."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    from sqlalchemy import func

    total = await db.execute(
        select(func.count(SupportTicket.id)).where(
            SupportTicket.created_at >= since,
        )
    )
    auto_closed = await db.execute(
        select(func.count(SupportTicket.id)).where(
            SupportTicket.created_at >= since,
            SupportTicket.resolution_notes.contains("Auto-cerrado"),
        )
    )
    total_val = total.scalar() or 0
    auto_val = auto_closed.scalar() or 0

    return {
        "total_tickets": total_val,
        "auto_resolved": auto_val,
        "auto_resolution_rate": round(auto_val / total_val * 100, 1) if total_val else 0,
        "period_days": days,
    }
