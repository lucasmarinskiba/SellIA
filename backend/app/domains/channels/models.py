import uuid
import secrets
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum, Integer, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


class ChannelPlatform(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    INSTAGRAM = "instagram"
    MERCADOLIBRE = "mercadolibre"
    AMAZON = "amazon"
    BEACONS = "beacons"
    LINKEDIN = "linkedin"
    TELEGRAM = "telegram"
    WEBCHAT = "webchat"
    MESSENGER = "messenger"
    FACEBOOK_ADS = "facebook_ads"
    META_ADS = "meta_ads"
    GOOGLE_ADS = "google_ads"
    SHOPIFY = "shopify"
    TIKTOK = "tiktok"
    TIKTOK_ADS = "tiktok_ads"
    TWITTER = "twitter"
    THREADS = "threads"


class ChannelStatus(str, enum.Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


def _generate_webhook_token() -> str:
    return secrets.token_urlsafe(32)


class ChannelConnection(Base):
    __tablename__ = "channel_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(Enum(ChannelPlatform), nullable=False)
    name = Column(String(255), nullable=False)
    credentials = Column(JSONB, default=dict, nullable=False)
    settings = Column(JSONB, default=dict, nullable=False)
    status = Column(Enum(ChannelStatus), default=ChannelStatus.PENDING, nullable=False)
    status_message = Column(Text, nullable=True)
    webhook_url = Column(String(512), nullable=True)
    webhook_token = Column(String(64), unique=True, nullable=False, default=_generate_webhook_token)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="channels")


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SPAM = "spam"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_connection_id = Column(UUID(as_uuid=True), ForeignKey("channel_connections.id", ondelete="SET NULL"), nullable=True)
    external_id = Column(String(255), nullable=True, index=True)
    lead_name = Column(String(255), nullable=True)
    lead_email = Column(String(255), nullable=True)
    lead_phone = Column(String(50), nullable=True)
    lead_source = Column(String(100), nullable=True)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    extra_data = Column(JSONB, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="conversations")
    channel = relationship("ChannelConnection")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(Enum(MessageDirection), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text", nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT, nullable=False)
    external_message_id = Column(String(255), nullable=True)
    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_messages_conversation_created', 'conversation_id', 'created_at'),
    )

    conversation = relationship("Conversation", back_populates="messages")
