"""Agentes IA - Schemas"""

import uuid
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ========== Personality Schemas ==========

class AgentPersonalityBase(BaseModel):
    slug: str
    name: str
    emoji: str = "🤖"
    tagline: str
    description: str
    expertise: List[str] = Field(default_factory=list)
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
    custom_instructions: Optional[str] = None
    tone_override: Optional[str] = None
    voice_personality_id: Optional[UUID] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class AgentConfigUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    custom_instructions: Optional[str] = None
    tone_override: Optional[str] = None
    voice_personality_id: Optional[UUID] = None
    extra_data: Optional[Dict[str, Any]] = None


class AgentConfigResponse(BaseModel):
    id: UUID
    business_id: UUID
    personality_id: UUID
    is_enabled: bool
    custom_instructions: Optional[str]
    tone_override: Optional[str]
    voice_personality_id: Optional[UUID]
    extra_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    personality: AgentPersonalityResponse
    voice_personality: Optional[AgentPersonalityResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ========== Conversation & Message Schemas ==========

class AgentConversationCreate(BaseModel):
    business_id: UUID
    personality_id: UUID
    title: Optional[str] = None


class AgentMessageCreate(BaseModel):
    content: str


class AgentMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    model_used: Optional[str]
    tokens_used: Optional[int]
    extra_data: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    business_id: UUID
    personality_id: UUID
    title: Optional[str]
    message_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    personality: Optional[AgentPersonalityResponse] = None

    model_config = ConfigDict(from_attributes=True)


class AgentConversationDetailResponse(AgentConversationResponse):
    messages: List[AgentMessageResponse] = Field(default_factory=list)


# ========== Auto-Pilot Voice Config ==========

class AutopilotVoiceConfig(BaseModel):
    personality_slug: str
    voice_personality_slug: Optional[str] = None
    custom_instructions: Optional[str] = None


class AutopilotVoiceConfigResponse(BaseModel):
    configs: Dict[str, AutopilotVoiceConfig]


# ========== Chat Response ==========

class AgentChatResponse(BaseModel):
    message: AgentMessageResponse
    conversation_id: UUID
    tokens_used: int = 0
    action_triggered: Optional[str] = None


# ========== ReAct Chat ==========

class ReactChatRequest(BaseModel):
    message: str
    business_id: Optional[UUID] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)


class ReactChatResponse(BaseModel):
    response: str
    iterations: int
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0
    model: Optional[str] = None
    provider: Optional[str] = None


# ========== Planning ==========

class PlanStepResponse(BaseModel):
    id: str
    description: str
    required_tools: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    task_description: str
    business_id: Optional[UUID] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class PlanResponse(BaseModel):
    plan: List[PlanStepResponse]
    results: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    completed_steps: int = 0
    failed_steps: int = 0


# ========== Swarm Schemas ==========

class SwarmExecuteRequest(BaseModel):
    task: str
    agents: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    consensus_required: bool = True
    max_rounds: int = 5


class SwarmAgentContribution(BaseModel):
    agent_id: str
    role: str
    content: str
    message_type: str
    target_agent: Optional[str] = None
    thought: Optional[str] = None
    round: int


class SwarmExecuteResponse(BaseModel):
    session_id: str
    final_response: str
    agent_contributions: List[SwarmAgentContribution]
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
    conversation_id: Optional[uuid.UUID] = None
    agents_involved: List[str] = Field(default_factory=list)
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    round_count: int
    consensus_reached: bool
    final_response: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[SwarmMessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SwarmSuggestRequest(BaseModel):
    task: str


class SwarmSuggestedAgent(BaseModel):
    role: str
    agent_slug: str
    description: str


class SwarmSuggestResponse(BaseModel):
    suggested_agents: List[SwarmSuggestedAgent]
