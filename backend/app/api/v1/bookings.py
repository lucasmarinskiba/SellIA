"""Booking events + real booking-rate metric.

Closes the "tasa de agenda alta" gap: instead of the mocked dashboard numbers
found in sales_funnel.py, this computes a real rate from DB rows —
qualified leads (LeadQualification.status == "qualified") vs. bookings
recorded via a token-secured inbound webhook any scheduling tool can call
(Calendly's native webhook, or a Zapier/Make bridge).

The webhook token is a deterministic HMAC of the business_id + SECRET_KEY
(no extra credential storage needed) — the business owner fetches it once via
GET /bookings/webhook-token and pastes the resulting URL into their scheduling
tool's webhook config.
"""

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.channels.models import BookingEvent, Conversation
from app.domains.agents.lead_qualifier.models import LeadQualification

router = APIRouter(prefix="/bookings", tags=["bookings"])

settings = get_settings()


def _webhook_token(business_id: UUID) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(), str(business_id).encode(), hashlib.sha256
    ).hexdigest()[:32]


@router.get("/webhook-token")
async def get_webhook_token(
    business_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
):
    """Returns the URL a business pastes into Calendly/cal.com's webhook config."""
    token = _webhook_token(business_id)
    return {
        "webhook_url": f"/api/v1/bookings/webhook/{business_id}?token={token}",
        "token": token,
    }


@router.post("/webhook/{business_id}", status_code=status.HTTP_202_ACCEPTED)
async def receive_booking_webhook(
    business_id: UUID,
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Generic inbound booking webhook (Calendly 'invitee.created' shape or similar)."""
    expected = _webhook_token(business_id)
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Token de webhook inválido")

    payload: dict[str, Any] = await request.json()

    # Accept both a flat shape and Calendly's nested payload.get("payload") shape.
    data = payload.get("payload", payload)
    invitee = data.get("invitee", data)

    invitee_email = invitee.get("email") or data.get("email")
    invitee_phone = invitee.get("text_reminder_number") or data.get("phone")
    external_booking_id = data.get("uri") or data.get("event") or payload.get("event")
    scheduled_at_raw = data.get("start_time") or data.get("scheduled_at")

    scheduled_at = None
    if scheduled_at_raw:
        try:
            scheduled_at = datetime.fromisoformat(str(scheduled_at_raw).replace("Z", "+00:00"))
        except Exception:
            scheduled_at = None

    conversation_id = None
    if invitee_email or invitee_phone:
        query = select(Conversation).where(Conversation.business_id == business_id)
        if invitee_email:
            query = query.where(Conversation.lead_email == invitee_email)
        elif invitee_phone:
            query = query.where(Conversation.lead_phone == invitee_phone)
        result = await db.execute(query.limit(1))
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation_id = conversation.id

    booking = BookingEvent(
        business_id=business_id,
        conversation_id=conversation_id,
        source="calendly",
        external_booking_id=str(external_booking_id) if external_booking_id else None,
        invitee_email=invitee_email,
        invitee_phone=invitee_phone,
        scheduled_at=scheduled_at,
        status="scheduled",
    )
    db.add(booking)
    await db.commit()

    return {"status": "recorded", "booking_id": str(booking.id)}


@router.get("/metrics")
async def booking_metrics(
    business_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Real booking-rate metric computed from DB rows (no mocked numbers)."""
    qualified_result = await db.execute(
        select(func.count(LeadQualification.id)).where(
            LeadQualification.business_id == business_id,
            LeadQualification.status == "qualified",
        )
    )
    qualified_leads = qualified_result.scalar() or 0

    bookings_result = await db.execute(
        select(func.count(BookingEvent.id)).where(
            BookingEvent.business_id == business_id,
            BookingEvent.status == "scheduled",
        )
    )
    bookings = bookings_result.scalar() or 0

    booking_rate = round((bookings / qualified_leads) * 100, 1) if qualified_leads else 0.0

    return {
        "business_id": str(business_id),
        "qualified_leads": qualified_leads,
        "bookings": bookings,
        "booking_rate_pct": booking_rate,
    }
