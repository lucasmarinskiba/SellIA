from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any

from app.domains.channels.models import ChannelPlatform, ChannelStatus, ConversationStatus, MessageDirection, MessageStatus


# ChannelConnection schemas
class ChannelConnectionBase(BaseModel):
    platform: ChannelPlatform
    name: str = Field(..., min_length=1, max_length=255)


class ChannelConnectionCreate(ChannelConnectionBase):
    credentials: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None


class ChannelConnectionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    credentials: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None
    status: ChannelStatus | None = None
    is_active: bool | None = None


class ChannelConnectionResponse(ChannelConnectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    credentials: dict[str, Any]
    settings: dict[str, Any]
    status: ChannelStatus
    status_message: str | None
    webhook_url: str | None
    webhook_token: str
    last_sync_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Conversation schemas
class ConversationBase(BaseModel):
    lead_name: str | None = Field(None, max_length=255)
    lead_email: str | None = Field(None, max_length=255)
    lead_phone: str | None = Field(None, max_length=50)
    lead_source: str | None = Field(None, max_length=100)


class ConversationCreate(ConversationBase):
    channel_connection_id: UUID | None = None
    external_id: str | None = None
    extra_data: dict[str, Any] | None = None


class ConversationUpdate(BaseModel):
    lead_name: str | None = Field(None, max_length=255)
    lead_email: str | None = Field(None, max_length=255)
    lead_phone: str | None = Field(None, max_length=50)
    status: ConversationStatus | None = None
    extra_data: dict[str, Any] | None = None
    is_active: bool | None = None


class ConversationResponse(ConversationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    channel_connection_id: UUID | None
    external_id: str | None
    status: ConversationStatus
    last_message_at: datetime | None
    extra_data: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(ConversationResponse):
    message_count: int = 0
    last_message_preview: str | None = None


# Message schemas
class MessageBase(BaseModel):
    content: str
    content_type: str = "text"


class MessageCreate(MessageBase):
    direction: MessageDirection
    extra_data: dict[str, Any] | None = None


class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    direction: MessageDirection
    status: MessageStatus
    external_message_id: str | None
    extra_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# Webhook schemas
class WebhookPayload(BaseModel):
    platform: ChannelPlatform
    external_id: str
    sender_name: str | None = None
    sender_phone: str | None = None
    sender_email: str | None = None
    sender_id: str | None = None
    content: str
    content_type: str = "text"
    timestamp: datetime | None = None
    extra_data: dict[str, Any] | None = None
