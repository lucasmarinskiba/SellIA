"""Intelligence Engine Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ========== Emotion Schemas ==========

class EmotionResult(BaseModel):
    emotion: str = "neutral"
    intensity: float = 0.0
    triggers: List[str] = Field(default_factory=list)


class EmotionDetectRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None
    message_id: Optional[UUID] = None


class EmotionDetectResponse(EmotionResult):
    id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    detected_at: Optional[datetime] = None


class EmotionTimelineItem(BaseModel):
    emotion: str
    intensity: float
    triggers: List[str]
    detected_at: datetime


class EmotionTimelineResponse(BaseModel):
    conversation_id: UUID
    timeline: List[EmotionTimelineItem]


# ========== Negotiation Schemas ==========

class NegotiationStartRequest(BaseModel):
    conversation_id: UUID
    business_id: UUID
    customer_id: UUID
    product_id: Optional[UUID] = None
    original_price: float = Field(..., gt=0)
    max_discount_percent: Optional[float] = Field(15.0, ge=0, le=100)


class NegotiationResponse(BaseModel):
    accepted: bool
    counter_offer: Optional[float] = None
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
    product_id: Optional[UUID] = None
    original_price: float
    current_offer: float
    minimum_acceptable: float
    max_discount_percent: float
    round: int
    concessions_made: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
