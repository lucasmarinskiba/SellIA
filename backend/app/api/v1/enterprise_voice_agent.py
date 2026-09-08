from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.enterprise.voice_agent import VoiceAgentManager

router = APIRouter()


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.id == business_id, Business.user_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


@router.post("/voice/config/{business_id}")
async def update_agent_config(
    business_id: UUID,
    agent_name: str = None,
    system_prompt: str = None,
    voice_id: str = None,
    language: str = None,
    greeting_message: str = None,
    temperature: float = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create/update this business's voice agent configuration.

    Replaces the original create_agent_persona/multiple-personas-per-user
    design -- VoiceConfig (the real model this now runs on) is one row per
    business, matching its actual `unique=True` constraint in production.
    """
    await _get_business_for_user(business_id, current_user, db)
    config = await VoiceAgentManager.update_config(
        business_id, db, voice_id=voice_id, language=language, greeting_message=greeting_message,
        agent_name=agent_name, system_prompt=system_prompt, temperature=temperature,
    )
    return {
        "status": "ok",
        "config": {
            "agent_name": config.agent_name, "voice_id": config.voice_id,
            "language": config.language, "temperature": config.temperature,
        },
    }


@router.get("/voice/config/{business_id}")
async def get_agent_config(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get this business's voice agent configuration."""
    await _get_business_for_user(business_id, current_user, db)
    config = await VoiceAgentManager.get_or_create_config(business_id, db)
    return {
        "status": "ok",
        "config": {
            "agent_name": config.agent_name, "voice_id": config.voice_id,
            "language": config.language, "greeting_message": config.greeting_message,
            "temperature": config.temperature,
        },
    }


@router.post("/voice/calls/outbound/{business_id}")
async def initiate_outbound_call(
    business_id: UUID,
    customer_id: UUID,
    phone_number: str,
    conversation_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initiate outbound call."""
    await _get_business_for_user(business_id, current_user, db)
    call = await VoiceAgentManager.initiate_outbound_call(business_id, customer_id, phone_number, db, conversation_id)
    return {"status": "ok", "call": {"id": str(call.id), "phone_number": call.phone_number, "status": call.status}}


@router.post("/voice/calls/inbound/{business_id}")
async def handle_inbound_call(
    business_id: UUID,
    customer_id: UUID,
    phone_number: str,
    conversation_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Handle inbound call."""
    await _get_business_for_user(business_id, current_user, db)
    call = await VoiceAgentManager.handle_inbound_call(business_id, customer_id, phone_number, db, conversation_id)
    return {"status": "ok", "call": {"id": str(call.id), "phone_number": call.phone_number, "status": call.status}}


@router.post("/voice/calls/{call_id}/transcript")
async def add_transcript(
    call_id: UUID,
    business_id: UUID,
    speaker: str,
    text: str,
    timestamp: float = 0.0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add transcript line to call."""
    await _get_business_for_user(business_id, current_user, db)
    try:
        call = await VoiceAgentManager.append_transcript_segment(call_id, business_id, speaker, text, db, timestamp)
    except ValueError:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return {"status": "ok", "transcript": call.transcript_segments[-1]}


@router.put("/voice/calls/{call_id}/status")
async def update_call_status(
    call_id: UUID,
    business_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update call status."""
    await _get_business_for_user(business_id, current_user, db)
    try:
        call = await VoiceAgentManager.update_call_status(call_id, business_id, status, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return {"status": "ok", "call": {"id": str(call.id), "status": call.status, "duration_seconds": call.recording_duration}}


@router.put("/voice/calls/{call_id}/recording")
async def set_recording_url(
    call_id: UUID,
    business_id: UUID,
    recording_url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set recording URL."""
    await _get_business_for_user(business_id, current_user, db)
    try:
        call = await VoiceAgentManager.set_recording_url(call_id, business_id, recording_url, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return {"status": "ok", "call": {"id": str(call.id), "recording_url": call.recording_url}}


@router.put("/voice/calls/{call_id}/transcript-summary")
async def set_transcript_summary(
    call_id: UUID,
    business_id: UUID,
    summary: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set AI-generated transcript summary."""
    await _get_business_for_user(business_id, current_user, db)
    try:
        call = await VoiceAgentManager.set_ai_summary(call_id, business_id, summary, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return {"status": "ok", "call": {"id": str(call.id), "ai_summary": call.ai_summary}}


@router.put("/voice/calls/{call_id}/sentiment")
async def analyze_sentiment(
    call_id: UUID,
    business_id: UUID,
    sentiment: str,
    score: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set sentiment analysis result."""
    await _get_business_for_user(business_id, current_user, db)
    try:
        call = await VoiceAgentManager.analyze_sentiment(call_id, business_id, sentiment, score, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return {"status": "ok", "call": {"id": str(call.id), **{k: call.extra_data.get(k) for k in ("sentiment", "sentiment_score")}}}


@router.get("/voice/calls/{call_id}")
async def get_call_detail(
    call_id: UUID,
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full call details with transcript."""
    await _get_business_for_user(business_id, current_user, db)
    call = await VoiceAgentManager.get_call_detail(call_id, business_id, db)
    if not call:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return {
        "status": "ok",
        "call": {
            "id": str(call.id), "phone_number": call.phone_number, "direction": call.direction,
            "status": call.status, "recording_url": call.recording_url, "ai_summary": call.ai_summary,
            "outcome": call.outcome, "created_at": call.created_at.isoformat() if call.created_at else None,
        },
        "transcript_segments": call.transcript_segments or [],
    }


@router.get("/voice/calls/business/{business_id}")
async def get_business_calls(
    business_id: UUID,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent calls for this business."""
    await _get_business_for_user(business_id, current_user, db)
    calls = await VoiceAgentManager.get_business_calls(business_id, db, limit)
    return {
        "status": "ok",
        "calls": [
            {
                "id": str(c.id), "phone_number": c.phone_number, "direction": c.direction,
                "status": c.status, "recording_duration": c.recording_duration,
                "sentiment": (c.extra_data or {}).get("sentiment"),
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in calls
        ],
        "count": len(calls),
    }


@router.get("/voice/analytics/{business_id}")
async def get_call_analytics(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get call analytics for this business."""
    await _get_business_for_user(business_id, current_user, db)
    analytics = await VoiceAgentManager.get_call_analytics(business_id, db, days)
    return {"status": "ok", "analytics": analytics}


@router.websocket("/ws/call/{call_id}")
async def websocket_call(websocket: WebSocket, call_id: str):
    """WebSocket for real-time call updates.

    NOT wired to real auth or a real live-transcription pipeline in this
    pass -- same documented gap as enterprise_collaboration.py's deal
    websocket (see that file): no connection registry, always echoes back
    to the same connection rather than broadcasting. A real implementation
    needs a live STT stream feeding this, which is a distinct feature.
    """
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.startswith("transcript:"):
                text = data.replace("transcript:", "")
                await websocket.send_json({"type": "transcript_received", "text": text, "timestamp": 0})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@router.post("/voice/webhooks/twilio")
async def handle_twilio_webhook(data: dict, db: AsyncSession = Depends(get_db)):
    """Handle Twilio call-status webhook.

    NOT verifying Twilio's request signature (X-Twilio-Signature header) in
    this pass -- no TWILIO_AUTH_TOKEN is configured in settings yet, so
    there's nothing to verify against. Documented gap, matching how
    payments.py's MercadoPago webhook required a real secret before its
    signature check could mean anything; the same is true here once Twilio
    is actually wired up.
    """
    twilio_call_id = data.get("CallSid")
    call_status = data.get("CallStatus")
    if not twilio_call_id or not call_status:
        return {"status": "ignored", "reason": "missing CallSid/CallStatus"}

    call = await VoiceAgentManager.find_call_by_twilio_id(twilio_call_id, db)
    if call:
        await VoiceAgentManager.update_call_status(call.id, call.business_id, call_status, db)

    return {"status": "ok", "processed": bool(call)}
