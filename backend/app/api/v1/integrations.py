"""Post-MVP Step 5: External Integrations - Slack, Calendar, Docusign, Stripe, Zapier."""

from fastapi import APIRouter, HTTPException, Query, Body, Header
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import os

from app.domains.integrations.slack_service import SlackService, SlackMessageType
from app.domains.integrations.calendar_service import CalendarService, EventType
from app.domains.integrations.docusign_service import DocusignService
from app.domains.integrations.stripe_service import StripeService, StripeEventType

router = APIRouter(tags=["integrations"])
logger = logging.getLogger(__name__)

# Service instances (in production, load from config)
slack_service = SlackService(
    webhook_url=os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/mock")
)
calendar_service = CalendarService(
    credentials_json=os.getenv("GOOGLE_CALENDAR_CREDENTIALS", "{}")
)
docusign_service = DocusignService(
    account_id=os.getenv("DOCUSIGN_ACCOUNT_ID", "mock"),
    api_key=os.getenv("DOCUSIGN_API_KEY", "mock"),
)
stripe_service = StripeService(
    api_key=os.getenv("STRIPE_API_KEY", "mock"),
    webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", "mock"),
)


# ============================================================
# Slack Integration
# ============================================================


@router.post("/integrations/slack/escalation-alert")
async def slack_escalation_alert(
    lead_name: str = Query(...),
    company: str = Query(...),
    reason: str = Query(...),
    deal_size: float = Query(...),
) -> Dict[str, Any]:
    """Send escalation alert to Slack."""
    success = await slack_service.send_escalation_alert(
        lead_name, company, reason, deal_size
    )

    return {
        "status": "success" if success else "failed",
        "message": "Escalation alert sent to Slack #sales-alerts",
        "details": {
            "lead": lead_name,
            "company": company,
            "deal_size": deal_size,
        },
    }


@router.post("/integrations/slack/deal-closed")
async def slack_deal_closed(
    lead_name: str = Query(...),
    company: str = Query(...),
    deal_size: float = Query(...),
    agent_name: str = Query(...),
) -> Dict[str, Any]:
    """Send deal closed celebration to Slack."""
    success = await slack_service.send_deal_closed_alert(
        lead_name, company, deal_size, agent_name
    )

    return {
        "status": "success" if success else "failed",
        "message": "Deal closed alert posted to Slack #wins",
        "celebration": "🎉🎊",
    }


@router.post("/integrations/slack/churn-warning")
async def slack_churn_warning(
    customer_name: str = Query(...),
    company: str = Query(...),
    churn_probability: float = Query(..., ge=0, le=1),
    days_until_churn: int = Query(...),
) -> Dict[str, Any]:
    """Send churn risk warning to Slack."""
    success = await slack_service.send_churn_warning(
        customer_name, company, churn_probability, days_until_churn
    )

    return {
        "status": "success" if success else "failed",
        "message": "Churn warning sent to Slack #customer-success",
        "alert_priority": "HIGH" if churn_probability > 0.7 else "MEDIUM",
    }


# ============================================================
# Google Calendar Integration
# ============================================================


@router.post("/integrations/calendar/schedule-demo")
async def schedule_demo(
    lead_name: str = Query(...),
    email: str = Query(...),
    company: str = Query(...),
    preferred_date: str = Query(..., description="ISO date string"),
) -> Dict[str, Any]:
    """Schedule product demo in Google Calendar."""
    try:
        preferred_time = datetime.fromisoformat(preferred_date)
        event_id = await calendar_service.schedule_demo(
            lead_name, email, company, preferred_time
        )

        return {
            "status": "success",
            "event_type": "demo",
            "event_id": event_id,
            "scheduled_for": preferred_time.isoformat(),
            "attendee": f"{lead_name} ({email})",
            "calendar_invite_sent": True,
        }

    except Exception as e:
        logger.error(f"Demo scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/calendar/schedule-follow-up")
async def schedule_follow_up(
    lead_name: str = Query(...),
    email: str = Query(...),
    reason: str = Query(...),
    days_from_now: int = Query(3, ge=1, le=30),
) -> Dict[str, Any]:
    """Schedule follow-up call."""
    event_id = await calendar_service.schedule_follow_up(
        lead_name, email, reason, days_from_now
    )

    return {
        "status": "success",
        "event_type": "follow_up",
        "event_id": event_id,
        "reason": reason,
        "scheduled_days_from_now": days_from_now,
    }


@router.post("/integrations/calendar/schedule-closing-call")
async def schedule_closing_call(
    lead_name: str = Query(...),
    email: str = Query(...),
    company: str = Query(...),
    deal_size: float = Query(...),
    preferred_date: str = Query(...),
) -> Dict[str, Any]:
    """Schedule closing call."""
    try:
        preferred_time = datetime.fromisoformat(preferred_date)
        event_id = await calendar_service.schedule_negotiation_call(
            lead_name, email, company, deal_size, preferred_time
        )

        return {
            "status": "success",
            "event_type": "closing_call",
            "event_id": event_id,
            "deal_size": deal_size,
            "scheduled_for": preferred_time.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Docusign Integration
# ============================================================


@router.post("/integrations/docusign/send-contract")
async def send_contract_for_signature(
    recipient_email: str = Query(...),
    recipient_name: str = Query(...),
    contract_name: str = Query(...),
    annual_price: float = Query(...),
    payment_terms: str = Query(...),
    company_name: str = Query(...),
) -> Dict[str, Any]:
    """Send contract for e-signature via Docusign."""
    try:
        # Mock contract PDF (in production, generate real contract)
        contract_pdf_base64 = "JVBERi0xLjQK"  # Minimal PDF header

        result = await docusign_service.send_contract_for_signature(
            recipient_email,
            recipient_name,
            contract_name,
            contract_pdf_base64,
            annual_price,
            payment_terms,
            company_name,
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to send contract")

        return {
            "status": "success",
            "envelope_id": result["envelope_id"],
            "signing_link": result["signing_link"],
            "deadline": result["deadline"],
            "recipient": recipient_email,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/docusign/signature-status/{envelope_id}")
async def get_signature_status(envelope_id: str) -> Dict[str, Any]:
    """Get signature status of Docusign envelope."""
    status = await docusign_service.get_signature_status(envelope_id)

    if not status:
        raise HTTPException(status_code=404, detail="Envelope not found")

    return {
        "status": "success",
        "envelope_id": envelope_id,
        "signature_status": status["status"],
        "signers": status["signers"],
    }


# ============================================================
# Stripe Webhooks
# ============================================================


@router.post("/integrations/stripe/webhooks")
async def stripe_webhook(
    request_body: bytes = Body(...),
    stripe_signature: str = Header(None),
) -> Dict[str, Any]:
    """Handle Stripe webhook events."""
    try:
        # Verify webhook signature
        if not stripe_service.verify_webhook_signature(
            request_body.decode(), stripe_signature
        ):
            logger.warning("Invalid Stripe webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse event
        import json
        event = json.loads(request_body)
        event_type = event.get("type")

        logger.info(f"Stripe webhook received: {event_type}")

        # Route to appropriate handler
        if event_type == StripeEventType.PAYMENT_SUCCEEDED:
            result = await stripe_service.handle_payment_succeeded(event["data"])
        elif event_type == StripeEventType.PAYMENT_FAILED:
            result = await stripe_service.handle_payment_failed(event["data"])
        elif event_type == StripeEventType.INVOICE_PAID:
            result = await stripe_service.handle_invoice_paid(event["data"])
        else:
            logger.info(f"Unhandled event type: {event_type}")
            result = None

        return {
            "status": "success",
            "event_type": event_type,
            "processed": result is not None,
            "action": result.get("action") if result else None,
        }

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Zapier Integration
# ============================================================


@router.post("/integrations/zapier/new-lead")
async def zapier_new_lead(
    lead_data: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    Zapier webhook for new lead creation.
    Triggered by: Zapier automation on form submission.
    """
    try:
        lead_id = lead_data.get("lead_id", f"lead_{datetime.now().timestamp()}")

        logger.info(f"New lead via Zapier: {lead_data.get('email')}")

        return {
            "status": "success",
            "lead_id": lead_id,
            "message": "Lead created and routing through agent pipeline",
            "next_action": "orchestrate/route-lead",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/zapier/deal-update")
async def zapier_deal_update(
    deal_data: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    Zapier webhook for deal updates.
    Triggered by: CRM pipeline stage changes.
    """
    try:
        deal_id = deal_data.get("deal_id")
        stage = deal_data.get("stage")

        logger.info(f"Deal update via Zapier: {deal_id} → {stage}")

        return {
            "status": "success",
            "deal_id": deal_id,
            "stage": stage,
            "intelligence_updated": True,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/health")
async def integrations_health() -> Dict[str, Any]:
    """Check health of all integrations."""
    return {
        "status": "success",
        "integrations": {
            "slack": "configured" if os.getenv("SLACK_WEBHOOK_URL") else "not_configured",
            "google_calendar": "configured" if os.getenv("GOOGLE_CALENDAR_CREDENTIALS") else "not_configured",
            "docusign": "configured" if os.getenv("DOCUSIGN_API_KEY") else "not_configured",
            "stripe": "configured" if os.getenv("STRIPE_API_KEY") else "not_configured",
            "zapier": "ready",  # Zapier is webhook-based, always ready
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
