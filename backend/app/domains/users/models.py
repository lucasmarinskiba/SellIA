import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base
from app.core.encrypted_types import EncryptedString, EncryptedJSONB
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    is_superuser = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)

    # 2FA / MFA
    totp_secret = Column(EncryptedString, nullable=True)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)

    # Region & billing (must match signup.py INSERT schema)
    country_code = Column(String(2), default="AR", nullable=False)
    preferred_currency = Column(String(3), default="ARS", nullable=False)
    timezone = Column(String(64), default="America/Argentina/Buenos_Aires", nullable=False)
    billing_address = Column(String, nullable=True)
    payment_methods = Column(String, nullable=True)

    businesses = relationship("Business", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
