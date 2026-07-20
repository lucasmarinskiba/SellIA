"""Emotion Detection Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class EmotionDetection(Base):
    __tablename__ = "emotion_detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    emotion = Column(String(20), nullable=False)
    intensity = Column(Float, nullable=False, default=0.0)
    triggers = Column(JSONB, default=list)
    detected_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
