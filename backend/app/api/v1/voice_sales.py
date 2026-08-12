"""Phase 29 Voice Sales API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.domains.enterprise.voice_sales import (
    VoiceCallManager,
    PlaybookExtractor,
    PlaybookRecommender,
)

router = APIRouter(prefix="/api/v1/voice", tags=["voice-sales"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================


class InitiateCallRequest(BaseModel):
    prospect_id: str
    deal_id: str


class InitiateCallResponse(BaseModel):
    call_id: str
    prospect_id: str
    deal_id: str
    status: str
    script: str


class CallInputRequest(BaseModel):
    call_id: str
    input_text: str


class CallInputResponse(BaseModel):
    response: str
    call_id: str


class EndCallRequest(BaseModel):
    call_id: str
    outcome: str  # meeting_booked, qualified, unqualified


class EndCallResponse(BaseModel):
    call_id: str
    outcome: str
    duration: int
    meeting_booked: bool


class PlaybookResponse(BaseModel):
    playbook_id: str
    name: str
    industry: str
    deal_stage: str
    win_rate: float
    next_step: str
    confidence: float


class CallMetricsResponse(BaseModel):
    total_calls: int
    meeting_booking_rate: float
    average_call_duration: int
    average_objections_handled: float


# ============================================================
# ENDPOINTS
# ============================================================


@router.post("/initiate-call", response_model=InitiateCallResponse)
def initiate_call(
    request: InitiateCallRequest,
    db: Session = Depends(get_db),
):
    """Initiate AI voice call with prospect."""

    try:
        manager = VoiceCallManager(db)
        result = manager.initiate_call(request.prospect_id, request.deal_id)

        return InitiateCallResponse(
            call_id=result.call_id,
            prospect_id=result.prospect_id,
            deal_id=result.deal_id,
            status=result.status,
            script=result.script,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/call/input", response_model=CallInputResponse)
def handle_call_input(
    request: CallInputRequest,
    db: Session = Depends(get_db),
):
    """Send voice input to AI call handler."""

    try:
        manager = VoiceCallManager(db)
        response = manager.handle_call_input(request.call_id, request.input_text)

        return CallInputResponse(
            response=response,
            call_id=request.call_id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/call/end", response_model=EndCallResponse)
def end_call(
    request: EndCallRequest,
    db: Session = Depends(get_db),
):
    """End voice call, analyze outcome."""

    try:
        manager = VoiceCallManager(db)
        result = manager.end_call(request.call_id, request.outcome)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return EndCallResponse(
            call_id=result["call_id"],
            outcome=result["outcome"],
            duration=result.get("duration", 0),
            meeting_booked=result.get("meeting_booked", False),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/playbooks/recommend/{deal_id}", response_model=Optional[PlaybookResponse])
def recommend_playbook(
    deal_id: str,
    db: Session = Depends(get_db),
):
    """Get recommended playbook for deal."""

    try:
        recommender = PlaybookRecommender(db)
        recommendation = recommender.recommend_playbook(deal_id)

        if not recommendation:
            return None

        return PlaybookResponse(
            playbook_id=recommendation.playbook_id,
            name=recommendation.name,
            industry=recommendation.industry,
            deal_stage=recommendation.deal_stage,
            win_rate=recommendation.win_rate,
            next_step=recommendation.next_step,
            confidence=recommendation.confidence,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics", response_model=CallMetricsResponse)
def get_voice_metrics(
    db: Session = Depends(get_db),
):
    """Get voice call metrics."""

    try:
        from sqlalchemy import func
        from backend.app.models.voice_sales import VoiceCall, VoiceCallMetrics

        # Get metrics
        total_calls = db.query(VoiceCall).count()

        booked_calls = db.query(VoiceCall).filter(
            VoiceCall.outcome == "meeting_booked"
        ).count()
        booking_rate = booked_calls / total_calls if total_calls > 0 else 0

        avg_duration = db.query(func.avg(VoiceCall.duration_seconds)).scalar() or 0

        avg_objections = db.query(func.avg(VoiceCallMetrics.objections_handled)).scalar() or 0

        return CallMetricsResponse(
            total_calls=total_calls,
            meeting_booking_rate=booking_rate,
            average_call_duration=int(avg_duration),
            average_objections_handled=avg_objections,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
