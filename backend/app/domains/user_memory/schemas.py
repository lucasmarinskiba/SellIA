"""User Memory Schemas"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserMemoryResponse(BaseModel):
    """Response model para UserMemory"""

    id: str
    user_id: str

    # Preferencias
    preferred_language: str
    preferred_tone: str
    industry_focus: str | None
    business_stage: str | None

    # Contexto aprendido
    primary_business_type: str | None
    target_audience_summary: str | None
    key_challenges: list[str]
    key_interests: list[str]
    technologies_used: list[str]

    # Historial
    total_conversations: int
    total_messages: int
    favorite_agents: list[dict[str, Any]]
    frequently_asked_topics: list[str]

    # Engagement
    engagement_score: float
    satisfaction_score: float
    churn_risk_score: float
    lifetime_value_estimate: str

    # Session context
    last_active_business_id: str | None
    last_active_conversation_id: str | None
    last_active_agent_id: str | None

    created_at: datetime | None
    updated_at: datetime | None
    last_activity_at: datetime | None

    class Config:
        from_attributes = True


class UserMemoryUpdate(BaseModel):
    """Update model para UserMemory"""

    preferred_language: str | None = None
    preferred_tone: str | None = None
    industry_focus: str | None = None
    business_stage: str | None = None

    primary_business_type: str | None = None
    target_audience_summary: str | None = None
    key_challenges: list[str] | None = None
    key_interests: list[str] | None = None
    technologies_used: list[str] | None = None

    notification_frequency: str | None = None
    email_notifications_enabled: bool | None = None

    last_active_business_id: str | None = None
    last_active_conversation_id: str | None = None
    last_active_agent_id: str | None = None


class UserMemoryEventCreate(BaseModel):
    """Create model para eventos de memoria"""

    event_type: str  # message_sent, action_taken, feedback_given, etc.
    event_data: dict[str, Any] = Field(default_factory=dict)
    conversation_id: str | None = None
    business_id: str | None = None
    agent_id: str | None = None


class UserMemoryEventResponse(BaseModel):
    """Response model para eventos"""

    id: str
    user_id: str
    event_type: str
    event_data: dict[str, Any]
    conversation_id: str | None
    business_id: str | None
    agent_id: str | None
    created_at: datetime | None

    class Config:
        from_attributes = True


class UserPreferenceUpdate(BaseModel):
    """Update model para UserPreference"""

    preference_key: str
    preference_value: dict[str, Any] = Field(default_factory=dict)


class UserPreferenceResponse(BaseModel):
    """Response model para UserPreference"""

    id: str
    user_id: str
    preference_key: str
    preference_value: dict[str, Any]
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True
