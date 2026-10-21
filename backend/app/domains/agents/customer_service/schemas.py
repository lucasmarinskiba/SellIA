"""Customer Service Auto-Agent Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServiceBotConfigBase(BaseModel):
    name: str = "SellIA Support"
    greeting_message: str = (
        "¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?"
    )
    fallback_message: str = (
        "No estoy seguro de entender. ¿Te gustaría que te conecte con un agente humano?"
    )
    escalation_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    hours_active: dict[str, Any] = Field(default_factory=dict)
    channels: list[str] = Field(default_factory=list)
    is_active: bool = True


class ServiceBotConfigCreate(ServiceBotConfigBase):
    business_id: UUID


class ServiceBotConfigUpdate(BaseModel):
    name: str | None = None
    greeting_message: str | None = None
    fallback_message: str | None = None
    escalation_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    hours_active: dict[str, Any] | None = None
    channels: list[str] | None = None
    is_active: bool | None = None


class ServiceBotConfigOut(ServiceBotConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime


class ServiceInteractionMessage(BaseModel):
    role: str
    content: str
    created_at: str | None = None


class ServiceInteractionBase(BaseModel):
    channel: str
    customer_id: UUID | None = None
    messages: list[ServiceInteractionMessage] = Field(default_factory=list)
    resolved: bool = False
    escalated: bool = False
    escalation_reason: str | None = None
    satisfaction_score: float | None = Field(default=None, ge=0.0, le=1.0)


class ServiceInteractionCreate(ServiceInteractionBase):
    bot_config_id: UUID
    conversation_id: UUID | None = None


class ServiceInteractionOut(ServiceInteractionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bot_config_id: UUID
    conversation_id: UUID | None = None
    created_at: datetime


class CustomerMessageIn(BaseModel):
    bot_config_id: UUID
    customer_id: UUID | None = None
    message: str
    channel: str
    conversation_id: UUID | None = None


class CustomerMessageOut(BaseModel):
    response: str
    escalated: bool
    escalation_reason: str | None = None
    emotion: dict[str, Any] | None = None
    sources: list[str] = Field(default_factory=list)


class FAQSearchIn(BaseModel):
    query: str
    business_id: UUID


class FAQSearchOut(BaseModel):
    query: str
    answer: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
