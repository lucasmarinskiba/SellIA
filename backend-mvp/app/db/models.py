"""SQLAlchemy 2.0 models · multi-tenant via tenant_id + RLS."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ─── Tenant + Users ────────────────────────────────────────────────────────────


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    subdomain: Mapped[str | None] = mapped_column(String(63), unique=True, index=True)
    plan: Mapped[str] = mapped_column(String(40), default="trial")  # trial | starter | pro | scale
    stripe_customer_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(120))
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    deals: Mapped[list["Deal"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tenant: Mapped[Tenant] = relationship(back_populates="users")


# ─── Channels (WhatsApp, IG, etc.) ─────────────────────────────────────────────


class ChannelKind(str, enum.Enum):
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    EMAIL = "email"
    WEB = "web"
    TELEGRAM = "telegram"


class Channel(Base):
    __tablename__ = "channels"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    kind: Mapped[ChannelKind] = mapped_column(Enum(ChannelKind))
    external_id: Mapped[str] = mapped_column(String(255))  # phone_number_id, IG account id, etc.
    config: Mapped[dict] = mapped_column(JSONB, default=dict)  # OAuth tokens, encrypted
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_channels_tenant_kind", "tenant_id", "kind"),)


# ─── Contacts + Deals ──────────────────────────────────────────────────────────


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    phone: Mapped[str | None] = mapped_column(String(40), index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    name: Mapped[str | None] = mapped_column(String(120))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DealStage(str, enum.Enum):
    PROSPECT = "prospect"
    QUALIFIED = "qualified"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    value_cents: Mapped[int] = mapped_column(BigInteger, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    stage: Mapped[DealStage] = mapped_column(Enum(DealStage), default=DealStage.PROSPECT)
    probability: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tenant: Mapped[Tenant] = relationship(back_populates="deals")

    __table_args__ = (Index("ix_deals_tenant_stage", "tenant_id", "stage"),)


# ─── Conversations + Messages ──────────────────────────────────────────────────


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    channel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"))
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MessageRole(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND_AI = "outbound_ai"
    OUTBOUND_HUMAN = "outbound_human"


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole))
    body: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


# ─── Audit log ─────────────────────────────────────────────────────────────────


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    actor_type: Mapped[str] = mapped_column(String(20))  # user | ai | system
    actor_id: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(80))
    resource: Mapped[str | None] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(20), default="info")
    ip: Mapped[str | None] = mapped_column(String(45))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
