"""Support system Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from app.domains.support.models import TicketStatus, TicketPriority, TicketCategory, MessageSenderType


# ===== FAQ Schemas =====

class FAQCreate(BaseModel):
    question: str = Field(..., max_length=500)
    answer: str
    tags: Optional[str] = None


class FAQUpdate(BaseModel):
    question: Optional[str] = Field(None, max_length=500)
    answer: Optional[str] = None
    tags: Optional[str] = None
    is_active: Optional[bool] = None


class FAQResponse(BaseModel):
    id: uuid.UUID
    business_id: Optional[uuid.UUID] = None
    question: str
    answer: str
    tags: Optional[str] = None
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Knowledge Base Schemas =====

class KnowledgeBaseArticleCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = None


class KnowledgeBaseArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeBaseArticleResponse(BaseModel):
    id: uuid.UUID
    business_id: Optional[uuid.UUID] = None
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[str] = None
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
    sender_id: Optional[uuid.UUID] = None
    content: str
    is_internal: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Ticket Schemas =====

class SupportTicketCreate(BaseModel):
    business_id: Optional[uuid.UUID] = None
    category: TicketCategory = TicketCategory.OTHER
    title: str = Field(..., max_length=255)
    description: str


class SupportTicketUpdate(BaseModel):
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None


class SupportTicketResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    business_id: Optional[uuid.UUID] = None
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    title: str
    description: str
    ai_suggested_answer: Optional[str] = None
    ai_confidence: Optional[float] = None
    assigned_to: Optional[uuid.UUID] = None
    escalated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    csat_rating: Optional[int] = None
    csat_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SupportTicketDetailResponse(SupportTicketResponse):
    messages: List[TicketMessageResponse] = []


class SupportTicketListResponse(BaseModel):
    items: List[SupportTicketResponse]
    total: int


# ===== CSAT Schema =====

class CSATSubmit(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# ===== Admin Stats Schema =====

class SupportStatsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_today: int
    avg_resolution_hours: Optional[float] = None
    ai_resolution_rate: Optional[float] = None
    csat_avg: Optional[float] = None
