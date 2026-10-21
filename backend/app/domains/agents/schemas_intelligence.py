"""Intelligence Engine Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ========== Emotion Schemas ==========


class EmotionResult(BaseModel):
    emotion: str = "neutral"
    intensity: float = 0.0
    triggers: list[str] = Field(default_factory=list)


class EmotionDetectRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None
    message_id: UUID | None = None


class EmotionDetectResponse(EmotionResult):
    id: UUID | None = None
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    detected_at: datetime | None = None


class EmotionTimelineItem(BaseModel):
    emotion: str
    intensity: float
    triggers: list[str]
    detected_at: datetime


class EmotionTimelineResponse(BaseModel):
    conversation_id: UUID
    timeline: list[EmotionTimelineItem]


# ========== Negotiation Schemas ==========


class NegotiationStartRequest(BaseModel):
    conversation_id: UUID
    business_id: UUID
    customer_id: UUID
    product_id: UUID | None = None
    original_price: float = Field(..., gt=0)
    max_discount_percent: float | None = Field(15.0, ge=0, le=100)


class NegotiationResponse(BaseModel):
    accepted: bool
    counter_offer: float | None = None
    discount_percent: float = 0.0
    round: int
    status: str
    message: str = ""
    urgency: bool = False


class NegotiationOfferRequest(BaseModel):
    conversation_id: UUID
    customer_offer: float = Field(..., gt=0)


class NegotiationStateResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    business_id: UUID
    customer_id: UUID
    product_id: UUID | None = None
    original_price: float
    current_offer: float
    minimum_acceptable: float
    max_discount_percent: float
    round: int
    concessions_made: list[dict[str, Any]] = Field(default_factory=list)
    status: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
