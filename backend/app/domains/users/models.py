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

    # Campos de seguridad anti-hackeo
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_failed_login = Column(DateTime(timezone=True), nullable=True)

    # 2FA / MFA
    totp_secret = Column(EncryptedString, nullable=True)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)

    # Login tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_device_fingerprint = Column(String(64), nullable=True)

    # Region & billing
    country_code = Column(String(2), default="AR", nullable=False)
    detected_country = Column(String(2), nullable=True)
    preferred_currency = Column(String(3), default="ARS", nullable=False)
    timezone = Column(String(50), default="America/Argentina/Buenos_Aires", nullable=False)
    tax_id = Column(EncryptedString, nullable=True)  # CUIT/CUIL/DNI — encrypted at rest
    billing_address = Column(EncryptedJSONB, default=dict, nullable=False)  # encrypted at rest
    payment_methods = Column(EncryptedJSONB, default=list, nullable=False)  # encrypted at rest

    businesses = relationship("Business", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
