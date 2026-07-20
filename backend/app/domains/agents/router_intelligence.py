"""Intelligence Router — Emotion & Negotiation APIs"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.emotion_engine import EmotionDetector, EmotionTimeline
from app.domains.agents.negotiation_engine import NegotiationEngine
from app.domains.agents.schemas_intelligence import (
    EmotionDetectRequest,
    EmotionDetectResponse,
    EmotionTimelineResponse,
    EmotionTimelineItem,
    NegotiationStartRequest,
    NegotiationOfferRequest,
    NegotiationResponse,
    NegotiationStateResponse,
)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# ========== Emotion ==========

@router.post("/emotion/detect", response_model=EmotionDetectResponse)
async def detect_emotion(
    data: EmotionDetectRequest,
    business_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detect emotion in a customer message."""
    if not business_id and current_user.businesses:
        business_id = current_user.businesses[0].id

    if not business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="business_id required",
        )

    result = await EmotionDetector.detect_emotion(
        db=db,
        business_id=business_id,
        message=data.message,
        conversation_id=data.conversation_id,
        message_id=data.message_id,
    )
    return EmotionDetectResponse(
        emotion=result.emotion,
        intensity=result.intensity,
        triggers=result.triggers,
        conversation_id=data.conversation_id,
        message_id=data.message_id,
    )


@router.get("/emotion/timeline/{conversation_id}", response_model=EmotionTimelineResponse)
async def get_emotion_timeline(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get emotion timeline for a conversation."""
    timeline = await EmotionTimeline.get_emotion_timeline(db, conversation_id)
    return EmotionTimelineResponse(
        conversation_id=conversation_id,
        timeline=[
            EmotionTimelineItem(
                emotion=t.emotion,
                intensity=t.intensity,
                triggers=t.triggers,
                detected_at=t.detected_at if hasattr(t, "detected_at") else None,
            )
            for t in timeline
        ],
    )


# ========== Negotiation ==========

@router.post("/negotiate/start", response_model=NegotiationStateResponse, status_code=status.HTTP_201_CREATED)
async def start_negotiation(
    data: NegotiationStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new negotiation session."""
    engine = NegotiationEngine(db)
    state = await engine.create_negotiation_state(
        conversation_id=data.conversation_id,
        business_id=data.business_id,
        customer_id=data.customer_id,
        product_id=data.product_id,
        original_price=data.original_price,
        max_discount_percent=data.max_discount_percent,
    )
    return state


@router.post("/negotiate/offer", response_model=NegotiationResponse)
async def process_negotiation_offer(
    data: NegotiationOfferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process a customer offer in an active negotiation."""
    engine = NegotiationEngine(db)
    neg_resp = await engine.process_offer(
        conversation_id=data.conversation_id,
        customer_offer=data.customer_offer,
    )

    # Enrich with natural-language reply if active
    if neg_resp.status == "active":
        state = await engine.get_active_state(data.conversation_id)
        if state:
            # Resolve business_id from state
            reply = await engine.generate_negotiation_reply(
                business_id=state.business_id,
                negotiation_response=neg_resp,
                state=state,
            )
            neg_resp.message = reply

    return neg_resp


@router.get("/negotiate/state/{conversation_id}", response_model=NegotiationStateResponse)
async def get_negotiation_state(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the active negotiation state for a conversation."""
    engine = NegotiationEngine(db)
    state = await engine.get_active_state(conversation_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active negotiation found for this conversation",
        )
    return state
