"""Agentes IA - Schemas"""

import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ========== Personality Schemas ==========


class AgentPersonalityBase(BaseModel):
    slug: str
    name: str
    emoji: str = "🤖"
    tagline: str
    description: str
    expertise: list[str] = Field(default_factory=list)
    color: str = "#FF6B35"
    display_order: int = 0


class AgentPersonalityResponse(AgentPersonalityBase):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Config Schemas ==========


class AgentConfigCreate(BaseModel):
    personality_id: UUID
    custom_instructions: str | None = None
    tone_override: str | None = None
    voice_personality_id: UUID | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class AgentConfigUpdate(BaseModel):
    is_enabled: bool | None = None
    custom_instructions: str | None = None
    tone_override: str | None = None
    voice_personality_id: UUID | None = None
    extra_data: dict[str, Any] | None = None


class AgentConfigResponse(BaseModel):
    id: UUID
    business_id: UUID
    personality_id: UUID
    is_enabled: bool
    custom_instructions: str | None
    tone_override: str | None
    voice_personality_id: UUID | None
    extra_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    personality: AgentPersonalityResponse
    voice_personality: AgentPersonalityResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ========== Conversation & Message Schemas ==========


class AgentConversationCreate(BaseModel):
    business_id: UUID
    personality_id: UUID
    title: str | None = None


class AgentMessageCreate(BaseModel):
    content: str


class AgentMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    model_used: str | None
    tokens_used: int | None
    extra_data: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    business_id: UUID
    personality_id: UUID
    title: str | None
    message_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    personality: AgentPersonalityResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class AgentConversationDetailResponse(AgentConversationResponse):
    messages: list[AgentMessageResponse] = Field(default_factory=list)


# ========== Auto-Pilot Voice Config ==========


class AutopilotVoiceConfig(BaseModel):
    personality_slug: str
    voice_personality_slug: str | None = None
    custom_instructions: str | None = None


class AutopilotVoiceConfigResponse(BaseModel):
    configs: dict[str, AutopilotVoiceConfig]


# ========== Chat Response ==========


class AgentChatResponse(BaseModel):
    message: AgentMessageResponse
    conversation_id: UUID
    tokens_used: int = 0
    action_triggered: str | None = None


# ========== ReAct Chat ==========


class ReactChatRequest(BaseModel):
    message: str
    business_id: UUID | None = None
    conversation_history: list[dict[str, str]] = Field(default_factory=list)


class ReactChatResponse(BaseModel):
    response: str
    iterations: int
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0
    model: str | None = None
    provider: str | None = None


# ========== Planning ==========


class PlanStepResponse(BaseModel):
    id: str
    description: str
    required_tools: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    task_description: str
    business_id: UUID | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class PlanResponse(BaseModel):
    plan: list[PlanStepResponse]
    results: list[dict[str, Any]] = Field(default_factory=list)
    status: str
    completed_steps: int = 0
    failed_steps: int = 0


# ========== Swarm Schemas ==========


class SwarmExecuteRequest(BaseModel):
    task: str
    agents: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    consensus_required: bool = True
    max_rounds: int = 5


class SwarmAgentContribution(BaseModel):
    agent_id: str
    role: str
    content: str
    message_type: str
    target_agent: str | None = None
    thought: str | None = None
    round: int


class SwarmExecuteResponse(BaseModel):
    session_id: str
    final_response: str
    agent_contributions: list[SwarmAgentContribution]
    reasoning: str
    consensus_reached: bool
    rounds: int


class SwarmMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    agent_id: str
    role: str
    content: str
    message_type: str
    round: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SwarmSessionResponse(BaseModel):
    id: uuid.UUID
    task: str
    business_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    agents_involved: list[str] = Field(default_factory=list)
    shared_context: dict[str, Any] = Field(default_factory=dict)
    round_count: int
    consensus_reached: bool
    final_response: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[SwarmMessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SwarmSuggestRequest(BaseModel):
    task: str


class SwarmSuggestedAgent(BaseModel):
    role: str
    agent_slug: str
    description: str


class SwarmSuggestResponse(BaseModel):
    suggested_agents: list[SwarmSuggestedAgent]
