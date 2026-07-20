"""Credential Models — Encrypted storage for platform credentials."""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Boolean, Index, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AuthType(str, enum.Enum):
    PASSWORD = "password"
    API_KEY = "api_key"
    OAUTH = "oauth"
    TWO_FACTOR = "2fa"


class SiteCredential(Base):
    __tablename__ = "site_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)

    domain = Column(String(200), nullable=False, index=True)
    platform_name = Column(String(100), nullable=False)
    auth_type = Column(Enum(AuthType), nullable=False, default=AuthType.PASSWORD)

    encrypted_username = Column(Text, nullable=True)
    encrypted_password = Column(Text, nullable=True)
    encrypted_api_key = Column(Text, nullable=True)
    encrypted_api_secret = Column(Text, nullable=True)
    encrypted_oauth_token = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    last_successful_login = Column(DateTime(timezone=True), nullable=True)
    failed_attempts = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_site_credentials_user_domain', 'user_id', 'domain', unique=True),
    )
