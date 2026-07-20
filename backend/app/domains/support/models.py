"""
Support System Models

Tickets, FAQ, Knowledge Base, and Ticket Messages.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Float, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TicketStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class TicketPriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(str, PyEnum):
    ACCOUNT = "account"
    BILLING = "billing"
    TECHNICAL = "technical"
    SALES = "sales"
    SECURITY = "security"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"


class MessageSenderType(str, PyEnum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    AI = "ai"


class SupportTicket(Base):
    """Ticket de soporte técnico."""
    __tablename__ = "support_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True)
    
    category = Column(Enum(TicketCategory), default=TicketCategory.OTHER, nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    ai_suggested_answer = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)  # 0.0 - 1.0
    ai_response_at = Column(DateTime(timezone=True), nullable=True)
    
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    last_customer_reply = Column(Text, nullable=True)
    last_customer_reply_at = Column(DateTime(timezone=True), nullable=True)
    
    csat_rating = Column(Integer, nullable=True)  # 1-5
    csat_comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class TicketMessage(Base):
    """Mensaje dentro de un ticket de soporte."""
    __tablename__ = "ticket_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type = Column(Enum(MessageSenderType), default=MessageSenderType.USER, nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)  # Notas internas del equipo
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FAQ(Base):
    """Preguntas frecuentes por negocio."""
    __tablename__ = "support_faqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    tags = Column(Text, nullable=True)  # comma-separated
    usage_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class KnowledgeBaseArticle(Base):
    """Artículos de knowledge base para soporte IA."""
    __tablename__ = "support_kb_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)
    embedding_vector = Column(Text, nullable=True)  # JSON array de embeddings (futuro)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
