"""Customer Service Auto-Agent Schemas"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ServiceBotConfigBase(BaseModel):
    name: str = "SellIA Support"
    greeting_message: str = "¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?"
    fallback_message: str = "No estoy seguro de entender. ¿Te gustaría que te conecte con un agente humano?"
    escalation_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    hours_active: Dict[str, Any] = Field(default_factory=dict)
    channels: List[str] = Field(default_factory=list)
    is_active: bool = True


class ServiceBotConfigCreate(ServiceBotConfigBase):
    business_id: UUID


class ServiceBotConfigUpdate(BaseModel):
    name: Optional[str] = None
    greeting_message: Optional[str] = None
    fallback_message: Optional[str] = None
    escalation_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    hours_active: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ServiceBotConfigOut(ServiceBotConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime


class ServiceInteractionMessage(BaseModel):
    role: str
    content: str
    created_at: Optional[str] = None


class ServiceInteractionBase(BaseModel):
    channel: str
    customer_id: Optional[UUID] = None
    messages: List[ServiceInteractionMessage] = Field(default_factory=list)
    resolved: bool = False
    escalated: bool = False
    escalation_reason: Optional[str] = None
    satisfaction_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ServiceInteractionCreate(ServiceInteractionBase):
    bot_config_id: UUID
    conversation_id: Optional[UUID] = None


class ServiceInteractionOut(ServiceInteractionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bot_config_id: UUID
    conversation_id: Optional[UUID] = None
    created_at: datetime


class CustomerMessageIn(BaseModel):
    bot_config_id: UUID
    customer_id: Optional[UUID] = None
    message: str
    channel: str
    conversation_id: Optional[UUID] = None


class CustomerMessageOut(BaseModel):
    response: str
    escalated: bool
    escalation_reason: Optional[str] = None
    emotion: Optional[Dict[str, Any]] = None
    sources: List[str] = Field(default_factory=list)


class FAQSearchIn(BaseModel):
    query: str
    business_id: UUID


class FAQSearchOut(BaseModel):
    query: str
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
