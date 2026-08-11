from fastapi import APIRouter, Query, WebSocket
from app.domains.enterprise.voice_agent import VoiceAgentManager, CallType, CallStatus

router = APIRouter()
voice_agent = VoiceAgentManager()


@router.post("/voice/personas")
async def create_agent_persona(
    user_id: str,
    name: str,
    system_prompt: str,
    voice_id: str,
    language: str = "en-US",
    speaking_rate: float = 1.0,
    temperature: float = 0.7,
    description: str = None,
    instructions: dict = None,
):
    """Create agent persona for voice calls."""
    persona = voice_agent.create_agent_persona(
        user_id=user_id,
        name=name,
        system_prompt=system_prompt,
        voice_id=voice_id,
        language=language,
        speaking_rate=speaking_rate,
        temperature=temperature,
        description=description,
        instructions=instructions,
    )

    return {
        "status": "ok",
        "persona": {
            "id": persona.id,
            "name": persona.name,
            "voice_id": persona.voice_id,
            "language": persona.language,
        },
    }


@router.get("/voice/personas/{user_id}")
async def get_agent_personas(user_id: str):
    """Get all personas for user."""
    personas = [
        p
        for p in voice_agent.agent_personas.values()
        if p.user_id == user_id
    ]

    return {
        "status": "ok",
        "personas": [
            {
                "id": p.id,
                "name": p.name,
                "voice_id": p.voice_id,
                "language": p.language,
                "description": p.description,
            }
            for p in personas
        ],
    }


@router.post("/voice/calls/outbound")
async def initiate_outbound_call(
    user_id: str,
    agent_persona_id: str,
    contact_number: str,
    contact_name: str = None,
    deal_id: str = None,
):
    """Initiate outbound call."""
    call = voice_agent.initiate_outbound_call(
        user_id=user_id,
        agent_persona_id=agent_persona_id,
        contact_number=contact_number,
        contact_name=contact_name,
        deal_id=deal_id,
    )

    return {
        "status": "ok",
        "call": {
            "id": call.id,
            "twilio_call_id": call.twilio_call_id,
            "contact_number": call.contact_number,
            "status": call.status,
        },
    }


@router.post("/voice/calls/inbound")
async def handle_inbound_call(
    user_id: str,
    agent_persona_id: str,
    contact_number: str,
    contact_name: str = None,
):
    """Handle inbound call."""
    call = voice_agent.handle_inbound_call(
        user_id=user_id,
        agent_persona_id=agent_persona_id,
        contact_number=contact_number,
        contact_name=contact_name,
    )

    return {
        "status": "ok",
        "call": {
            "id": call.id,
            "contact_number": call.contact_number,
            "status": call.status,
        },
    }


@router.post("/voice/calls/{call_id}/transcript")
async def add_transcript(
    call_id: str,
    speaker: str,
    text: str,
    timestamp: float,
    confidence: float = None,
):
    """Add transcript line to call."""
    transcript = voice_agent.add_transcript(
        call_id=call_id,
        speaker=speaker,
        text=text,
        timestamp=timestamp,
        confidence=confidence,
    )

    return {
        "status": "ok",
        "transcript": {
            "speaker": transcript.speaker,
            "text": transcript.text,
            "timestamp": transcript.timestamp,
        },
    }


@router.put("/voice/calls/{call_id}/status")
async def update_call_status(call_id: str, status: str):
    """Update call status."""
    call = voice_agent.update_call_status(call_id, CallStatus(status))

    return {
        "status": "ok",
        "call": {
            "id": call.id,
            "status": call.status,
            "duration_seconds": call.duration_seconds,
        },
    }


@router.put("/voice/calls/{call_id}/recording")
async def set_recording_url(call_id: str, recording_url: str):
    """Set recording URL."""
    call = voice_agent.set_recording_url(call_id, recording_url)

    return {
        "status": "ok",
        "call": {
            "id": call.id,
            "recording_url": call.recording_url,
        },
    }


@router.put("/voice/calls/{call_id}/transcript-summary")
async def set_transcript_summary(call_id: str, summary: str):
    """Set transcript summary."""
    call = voice_agent.set_transcript_summary(call_id, summary)

    return {
        "status": "ok",
        "call": {
            "id": call.id,
            "transcript": call.transcript[:100] + "...",
        },
    }


@router.put("/voice/calls/{call_id}/sentiment")
async def analyze_sentiment(call_id: str, sentiment: str, score: float):
    """Set sentiment analysis."""
    call = voice_agent.analyze_sentiment(call_id, sentiment, score)

    return {
        "status": "ok",
        "call": {
            "id": call.id,
            "sentiment": call.sentiment,
            "sentiment_score": call.sentiment_score,
        },
    }


@router.get("/voice/calls/{call_id}")
async def get_call_detail(call_id: str):
    """Get full call details."""
    detail = voice_agent.get_call_detail(call_id)

    return {
        "status": "ok",
        "call": detail["call"],
        "transcript_count": len(detail["transcripts"]),
        "transcripts": detail["transcripts"],
    }


@router.get("/voice/calls/user/{user_id}")
async def get_user_calls(user_id: str, limit: int = Query(50, le=100)):
    """Get recent calls for user."""
    calls = voice_agent.get_user_calls(user_id, limit)

    return {
        "status": "ok",
        "calls": [
            {
                "id": c.id,
                "contact_number": c.contact_number,
                "call_type": c.call_type,
                "status": c.status,
                "duration_seconds": c.duration_seconds,
                "sentiment": c.sentiment,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in calls
        ],
        "count": len(calls),
    }


@router.get("/voice/analytics/{user_id}")
async def get_call_analytics(user_id: str, days: int = Query(30, ge=1, le=365)):
    """Get call analytics."""
    analytics = voice_agent.get_call_analytics(user_id, days)

    return {
        "status": "ok",
        "analytics": analytics,
    }


@router.websocket("/ws/call/{call_id}")
async def websocket_call(websocket: WebSocket, call_id: str):
    """WebSocket for real-time call updates."""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.startswith("transcript:"):
                text = data.replace("transcript:", "")
                await websocket.send_json(
                    {
                        "type": "transcript_received",
                        "text": text,
                        "timestamp": 0,
                    }
                )
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@router.post("/voice/webhooks/twilio")
async def handle_twilio_webhook(data: dict):
    """Handle Twilio webhook events."""
    twilio_call_id = data.get("CallSid")
    call_status = data.get("CallStatus")

    # Find call by twilio_call_id
    matching_calls = [
        c
        for c in voice_agent.call_records.values()
        if c.twilio_call_id == twilio_call_id
    ]

    if matching_calls:
        call = matching_calls[0]
        voice_agent.update_call_status(call.id, CallStatus(call_status))

    return {
        "status": "ok",
        "processed": True,
    }
