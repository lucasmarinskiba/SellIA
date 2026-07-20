"""
Feedback Hub Models

User feedback, voting, comments, and AI-generated system improvements.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Enum, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class FeedbackType(str, PyEnum):
    BUG = "bug"
    IDEA = "idea"
    COMPLAINT = "complaint"
    PRAISE = "praise"
    OTHER = "other"


class FeedbackSeverity(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatus(str, PyEnum):
    NEW = "new"
    UNDER_REVIEW = "under_review"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SHIPPED = "shipped"
    DECLINED = "declined"


class UserFeedback(Base):
    """Feedback enviado por un usuario."""
    __tablename__ = "user_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True)

    type = Column(Enum(FeedbackType), default=FeedbackType.OTHER, nullable=False)
    category = Column(String(50), nullable=True)  # ux, performance, security, billing, etc.
    severity = Column(Enum(FeedbackSeverity), default=FeedbackSeverity.MEDIUM, nullable=False)
    status = Column(Enum(FeedbackStatus), default=FeedbackStatus.NEW, nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    screenshots = Column(JSONB, default=list, nullable=True)  # URLs de screenshots

    # AI analysis
    ai_analysis = Column(Text, nullable=True)
    ai_solution_proposal = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_duplicate_of_id = Column(UUID(as_uuid=True), ForeignKey("user_feedback.id", ondelete="SET NULL"), nullable=True)

    votes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)

    # Si es una idea, qué plan mínimo necesita
    target_plan = Column(String(50), nullable=True)  # free, starter, pro, enterprise
    estimated_effort_hours = Column(Integer, nullable=True)

    # Si se resolvió, link a la mejora del sistema
    system_improvement_id = Column(UUID(as_uuid=True), ForeignKey("system_improvements.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FeedbackVote(Base):
    """Voto de un usuario a un feedback (solo ideas)."""
    __tablename__ = "feedback_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id = Column(UUID(as_uuid=True), ForeignKey("user_feedback.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FeedbackComment(Base):
    """Comentario en un feedback."""
    __tablename__ = "feedback_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id = Column(UUID(as_uuid=True), ForeignKey("user_feedback.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SystemImprovement(Base):
    """Propuesta de mejora generada por el System Intelligence Engine."""
    __tablename__ = "system_improvements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    affected_modules = Column(JSONB, default=list, nullable=False)  # ["auth", "analytics"]
    implementation_details = Column(Text, nullable=True)  # Código/config sugerido

    difficulty = Column(String(20), nullable=True)  # easy, medium, hard
    estimated_hours = Column(Integer, nullable=True)
    target_plan = Column(String(50), nullable=False, default="starter")  # free, starter, pro, enterprise

    status = Column(String(20), default="proposed", nullable=False)  # proposed, approved, in_progress, deployed, reverted

    # Feature flag asociada
    feature_flag_name = Column(String(100), nullable=True, index=True)

    # ML metrics
    ml_model_accuracy_before = Column(Float, nullable=True)
    ml_model_accuracy_after = Column(Float, nullable=True)

    # Source
    source_feedback_ids = Column(JSONB, default=list, nullable=True)  # IDs de feedback que motivaron esta mejora
    source_health_report_id = Column(UUID(as_uuid=True), nullable=True)

    deployed_at = Column(DateTime(timezone=True), nullable=True)
    reverted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FeatureFlag(Base):
    """Feature flags para despliegue gradual por plan."""
    __tablename__ = "feature_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    enabled_plans = Column(JSONB, default=list, nullable=False)  # ["pro", "enterprise"]
    rollout_percentage = Column(Integer, default=100, nullable=False)  # 0-100
    user_id_allowlist = Column(JSONB, default=list, nullable=True)  # usuarios específicos

    is_active = Column(Boolean, default=True, nullable=False)
    created_by_improvement_id = Column(UUID(as_uuid=True), ForeignKey("system_improvements.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class MLTrainingData(Base):
    """Datos recolectados para entrenamiento de modelos ML."""
    __tablename__ = "ml_training_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True)

    data_type = Column(String(50), nullable=False, index=True)  # conversation_outcome, ai_response_rating, intent_accuracy
    features = Column(JSONB, default=dict, nullable=False)  # features del modelo
    label = Column(String(50), nullable=True)  # label/target
    score = Column(Float, nullable=True)  # score numérico
    model_version = Column(String(20), nullable=True)  # versión del modelo que usó estos datos

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
