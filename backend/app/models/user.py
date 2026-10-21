"""User model for seller accounts."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.database import Base


class User(Base):
    """Seller user account."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)

    seller_name = Column(String(255), nullable=False)
    business_name = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    is_active = Column(Boolean, default=True)
