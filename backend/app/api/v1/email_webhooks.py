"""
Email Webhook Handlers
- SendGrid event webhooks
- Open/click/bounce/unsubscribe tracking
- Lead scoring updates on engagement
"""
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models import WorkflowExecution, EmailLog, WebhookEvent, Lead
from app.db.database import AsyncSessionLocal
from datetime import datetime
import logging
import os
import hmac
import hashlib
import base64

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# ============================================================
# SIGNATURE VERIFICATION
# ============================================================
def verify_sendgrid_signature(request_body: bytes, signature: str, timestamp: str) -> bool:
    """Verify SendGrid webhook signature with HMAC-SHA256."""
    webhook_key = os.getenv("SENDGRID_WEBHOOK_KEY", "")
    if not webhook_key:
        logger.warning("SENDGRID_WEBHOOK_KEY not set - skipping signature verification")
        return True

    msg = timestamp.encode() + request_body
    expected_signature = base64.b64encode(
        hmac.new(webhook_key.encode(), msg, hashlib.sha256).digest()
    ).decode()

    return hmac.compare_digest(signature, expected_signature)

# ============================================================
# SENDGRID WEBHOOK HANDLER
# ============================================================
@router.post("/sendgrid")
async def handle_sendgrid_webhook(request: Request) -> dict:
    """
    Handle SendGrid webhook events.
    Payload: [{
        "email": "test@example.com",
        "event": "open|click|bounce|unsubscribe",
        "timestamp": 1234567890,
        "sg_message_id": "...",
        "sg_event_id": "...",
        "url": "https://..." (for click)
    }]
    """
    try:
        # Verify webhook signature
        signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature", "")
        timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp", "")

        body = await request.body()
        if not verify_sendgrid_signature(body, signature, timestamp):
            logger.error("Invalid SendGrid webhook signature")
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

        events = await request.json()

        async with AsyncSessionLocal() as session:
            for event in events:
                email = event.get("email")
                event_type = event.get("event")  # open, click, bounce, unsubscribe
                timestamp = event.get("timestamp", int(datetime.now().timestamp()))

                logger.info(f"SendGrid event: {email} - {event_type}")

                if event_type == "open":
                    await _handle_email_opened(session, email, timestamp)
                elif event_type == "click":
                    await _handle_email_clicked(session, email, event.get("url"), timestamp)
                elif event_type == "bounce":
                    await _handle_email_bounced(session, email, event.get("reason", "unknown"), timestamp)
                elif event_type == "unsubscribe":
                    await _handle_email_unsubscribed(session, email, timestamp)

                # Store raw event
                webhook_event = WebhookEvent(
                    provider="sendgrid",
                    event_type=event_type,
                    email=email,
                    payload=event,
                    processed=True,
                    processed_at=datetime.now()
                )
                session.add(webhook_event)

            await session.commit()

        return {"status": "ok", "events_processed": len(events)}

    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# EVENT HANDLERS
# ============================================================
async def _handle_email_opened(session: AsyncSession, email: str, timestamp: int) -> None:
    """Mark email as opened, update lead engagement score."""

    # Find workflow execution by email
    stmt = select(WorkflowExecution).where(
        WorkflowExecution.lead_email == email
    ).order_by(WorkflowExecution.created_at.desc()).limit(1)

    result = await session.execute(stmt)
    execution = result.scalar_one_or_none()

    if execution:
        execution.email_status = "opened"
        execution.opened_at = datetime.fromtimestamp(timestamp)
        execution.opened_count = (execution.opened_count or 0) + 1

        # Find lead and boost score
        lead_stmt = select(Lead).where(Lead.id == execution.lead_id)
        lead_result = await session.execute(lead_stmt)
        lead = lead_result.scalar_one_or_none()

        if lead:
            # +5 points for open
            lead.score = min(100, (lead.score or 0) + 5)
            lead.last_contacted = datetime.now()
            logger.info(f"Lead {lead.email} opened email. Score now: {lead.score}")

        logger.info(f"Email opened: {email}")
    else:
        logger.warning(f"No workflow execution found for email: {email}")

async def _handle_email_clicked(session: AsyncSession, email: str, url: str, timestamp: int) -> None:
    """Mark email as clicked, significant engagement signal."""

    stmt = select(WorkflowExecution).where(
        WorkflowExecution.lead_email == email
    ).order_by(WorkflowExecution.created_at.desc()).limit(1)

    result = await session.execute(stmt)
    execution = result.scalar_one_or_none()

    if execution:
        execution.email_status = "clicked"
        execution.clicked_at = datetime.fromtimestamp(timestamp)
        execution.clicked_count = (execution.clicked_count or 0) + 1

        # Find lead and boost score
        lead_stmt = select(Lead).where(Lead.id == execution.lead_id)
        lead_result = await session.execute(lead_stmt)
        lead = lead_result.scalar_one_or_none()

        if lead:
            # +15 points for click (strong intent signal)
            lead.score = min(100, (lead.score or 0) + 15)
            lead.status = "engaged"
            lead.last_contacted = datetime.now()
            logger.info(f"Lead {lead.email} clicked link. Score now: {lead.score}, Status: engaged")

        logger.info(f"Email clicked: {email} -> {url}")
    else:
        logger.warning(f"No workflow execution found for email: {email}")

async def _handle_email_bounced(session: AsyncSession, email: str, reason: str, timestamp: int) -> None:
    """Mark email as bounced, disable future sending."""

    # Find lead and mark as bounced
    lead_stmt = select(Lead).where(Lead.email == email)
    lead_result = await session.execute(lead_stmt)
    lead = lead_result.scalar_one_or_none()

    if lead:
        lead.status = "bounced"
        lead.score = 0  # Zero out score
        logger.warning(f"Lead {email} bounced. Reason: {reason}")

    # Mark all pending executions as bounced
    exec_stmt = select(WorkflowExecution).where(
        (WorkflowExecution.lead_email == email) &
        (WorkflowExecution.email_status.in_(["scheduled", "sent"]))
    )
    exec_result = await session.execute(exec_stmt)
    executions = exec_result.scalars().all()

    for execution in executions:
        execution.email_status = "bounced"
        execution.bounce_reason = reason
        execution.bounced_at = datetime.fromtimestamp(timestamp)

async def _handle_email_unsubscribed(session: AsyncSession, email: str, timestamp: int) -> None:
    """Mark lead as unsubscribed."""

    # Find lead
    lead_stmt = select(Lead).where(Lead.email == email)
    lead_result = await session.execute(lead_stmt)
    lead = lead_result.scalar_one_or_none()

    if lead:
        lead.status = "unsubscribed"
        logger.info(f"Lead {email} unsubscribed")

    # Mark all executions as unsubscribed
    exec_stmt = select(WorkflowExecution).where(
        WorkflowExecution.lead_email == email
    )
    exec_result = await session.execute(exec_stmt)
    executions = exec_result.scalars().all()

    for execution in executions:
        if execution.email_status in ["scheduled", "sent", "delivered"]:
            execution.email_status = "unsubscribed"

# ============================================================
# MANUAL WEBHOOK SIMULATOR (for testing)
# ============================================================
@router.post("/sendgrid/test-open")
async def test_email_opened(email: str) -> dict:
    """Simulate email open event (testing only)."""
    async with AsyncSessionLocal() as session:
        await _handle_email_opened(session, email, int(datetime.now().timestamp()))
        await session.commit()
    return {"status": "ok", "event": "open", "email": email}

@router.post("/sendgrid/test-click")
async def test_email_clicked(email: str, url: str = "https://example.com") -> dict:
    """Simulate email click event (testing only)."""
    async with AsyncSessionLocal() as session:
        await _handle_email_clicked(session, email, url, int(datetime.now().timestamp()))
        await session.commit()
    return {"status": "ok", "event": "click", "email": email, "url": url}

@router.post("/sendgrid/test-bounce")
async def test_email_bounced(email: str, reason: str = "hard_bounce") -> dict:
    """Simulate email bounce event (testing only)."""
    async with AsyncSessionLocal() as session:
        await _handle_email_bounced(session, email, reason, int(datetime.now().timestamp()))
        await session.commit()
    return {"status": "ok", "event": "bounce", "email": email, "reason": reason}
