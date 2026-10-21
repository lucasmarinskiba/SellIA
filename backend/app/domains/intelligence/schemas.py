"""Intelligence Schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageAnalysisResponse(BaseModel):
    id: UUID
    business_id: UUID
    conversation_id: UUID
    message_id: UUID
    sentiment_score: float = 0
    sentiment_label: str = "neutral"
    intent_type: str = "neutral"
    intent_confidence: float = 0
    objections_detected: list[str] = Field(default_factory=list)
    pain_points_detected: list[str] = Field(default_factory=list)
    buying_signals_detected: list[str] = Field(default_factory=list)
    urgency_level: str = "low"
    language_detected: str = "es"
    key_entities: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str | None = None
    recommended_personality: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationIntelligenceResponse(BaseModel):
    id: UUID
    business_id: UUID
    conversation_id: UUID
    overall_sentiment_trend: str = "stable"
    average_sentiment_score: float = 0
    dominant_intent: str = "neutral"
    buying_readiness_score: int = 0
    objection_history: list[dict[str, Any]] = Field(default_factory=list)
    churn_risk_signals_count: int = 0
    next_best_action: str | None = None
    next_best_action_reason: str | None = None
    total_messages_analyzed: int = 0
    positive_messages_count: int = 0
    negative_messages_count: int = 0
    buying_signals_count: int = 0
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyzeMessageRequest(BaseModel):
    message_id: UUID


class ConversationIntelligenceFilter(BaseModel):
    business_id: UUID | None = None
    intent_type: str | None = None
    min_buying_readiness: int | None = None
    limit: int = 50
    offset: int = 0
