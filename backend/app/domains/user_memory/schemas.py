"""User Memory Schemas"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UserMemoryResponse(BaseModel):
    """Response model para UserMemory"""
    id: str
    user_id: str

    # Preferencias
    preferred_language: str
    preferred_tone: str
    industry_focus: Optional[str]
    business_stage: Optional[str]

    # Contexto aprendido
    primary_business_type: Optional[str]
    target_audience_summary: Optional[str]
    key_challenges: List[str]
    key_interests: List[str]
    technologies_used: List[str]

    # Historial
    total_conversations: int
    total_messages: int
    favorite_agents: List[Dict[str, Any]]
    frequently_asked_topics: List[str]

    # Engagement
    engagement_score: float
    satisfaction_score: float
    churn_risk_score: float
    lifetime_value_estimate: str

    # Session context
    last_active_business_id: Optional[str]
    last_active_conversation_id: Optional[str]
    last_active_agent_id: Optional[str]

    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    last_activity_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserMemoryUpdate(BaseModel):
    """Update model para UserMemory"""
    preferred_language: Optional[str] = None
    preferred_tone: Optional[str] = None
    industry_focus: Optional[str] = None
    business_stage: Optional[str] = None

    primary_business_type: Optional[str] = None
    target_audience_summary: Optional[str] = None
    key_challenges: Optional[List[str]] = None
    key_interests: Optional[List[str]] = None
    technologies_used: Optional[List[str]] = None

    notification_frequency: Optional[str] = None
    email_notifications_enabled: Optional[bool] = None

    last_active_business_id: Optional[str] = None
    last_active_conversation_id: Optional[str] = None
    last_active_agent_id: Optional[str] = None


class UserMemoryEventCreate(BaseModel):
    """Create model para eventos de memoria"""
    event_type: str  # message_sent, action_taken, feedback_given, etc.
    event_data: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[str] = None
    business_id: Optional[str] = None
    agent_id: Optional[str] = None


class UserMemoryEventResponse(BaseModel):
    """Response model para eventos"""
    id: str
    user_id: str
    event_type: str
    event_data: Dict[str, Any]
    conversation_id: Optional[str]
    business_id: Optional[str]
    agent_id: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserPreferenceUpdate(BaseModel):
    """Update model para UserPreference"""
    preference_key: str
    preference_value: Dict[str, Any] = Field(default_factory=dict)


class UserPreferenceResponse(BaseModel):
    """Response model para UserPreference"""
    id: str
    user_id: str
    preference_key: str
    preference_value: Dict[str, Any]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
