import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class FeatureFlag(Base):
    """Feature flag for gradual rollouts and plan-gating."""
    __tablename__ = "feature_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    enabled_plans = Column(JSONB, nullable=False, default=list)  # ["free", "pro", "enterprise"]
    rollout_percentage = Column(Integer, default=100, nullable=False)  # 0-100
    user_id_allowlist = Column(JSONB, nullable=True, default=list)  # ["uuid", ...]
    is_active = Column(Boolean, default=True, nullable=False)  # Global kill-switch
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
