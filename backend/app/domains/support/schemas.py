"""Support system Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domains.support.models import (
    MessageSenderType,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)

# ===== FAQ Schemas =====

class FAQCreate(BaseModel):
    question: str = Field(..., max_length=500)
    answer: str
    tags: str | None = None


class FAQUpdate(BaseModel):
    question: str | None = Field(None, max_length=500)
    answer: str | None = None
    tags: str | None = None
    is_active: bool | None = None


class FAQResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID | None = None
    question: str
    answer: str
    tags: str | None = None
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Knowledge Base Schemas =====

class KnowledgeBaseArticleCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    category: str | None = Field(None, max_length=100)
    tags: str | None = None


class KnowledgeBaseArticleUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: str | None = None
    category: str | None = Field(None, max_length=100)
    tags: str | None = None
    is_active: bool | None = None


class KnowledgeBaseArticleResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID | None = None
    title: str
    content: str
    category: str | None = None
    tags: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KBSearchResult(BaseModel):
    article: KnowledgeBaseArticleResponse
    score: float


# ===== Ticket Message Schemas =====

class TicketMessageCreate(BaseModel):
    content: str
    is_internal: bool = False


class TicketMessageResponse(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    sender_type: MessageSenderType
    sender_id: uuid.UUID | None = None
    content: str
    is_internal: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Ticket Schemas =====

class SupportTicketCreate(BaseModel):
    business_id: uuid.UUID | None = None
    category: TicketCategory = TicketCategory.OTHER
    title: str = Field(..., max_length=255)
    description: str


class SupportTicketUpdate(BaseModel):
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    assigned_to: uuid.UUID | None = None


class SupportTicketResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    business_id: uuid.UUID | None = None
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    title: str
    description: str
    ai_suggested_answer: str | None = None
    ai_confidence: float | None = None
    assigned_to: uuid.UUID | None = None
    escalated_at: datetime | None = None
    resolved_at: datetime | None = None
    csat_rating: int | None = None
    csat_comment: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int | None = None

    model_config = ConfigDict(from_attributes=True)


class SupportTicketDetailResponse(SupportTicketResponse):
    messages: list[TicketMessageResponse] = []


class SupportTicketListResponse(BaseModel):
    items: list[SupportTicketResponse]
    total: int


# ===== CSAT Schema =====

class CSATSubmit(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


# ===== Admin Stats Schema =====

class SupportStatsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_today: int
    avg_resolution_hours: float | None = None
    ai_resolution_rate: float | None = None
    csat_avg: float | None = None
