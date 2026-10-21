"""Phase 35: Neural Networks."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class MLLeadScorer(Base):
    __tablename__ = "ml_lead_scorers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    lead_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    dl_score = Column(Float, default=0)
    model_version = Column(String(50), default="v1")
    created_at = Column(DateTime(UTC), default=lambda: datetime.now(UTC))


class ChurnRNNModel(Base):
    __tablename__ = "churn_rnn_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    churn_probability_rnn = Column(Float, default=0)
    retention_action = Column(String(255), nullable=True)
    created_at = Column(DateTime(UTC), default=lambda: datetime.now(UTC))


class WinLossClassifier(Base):
    __tablename__ = "win_loss_classifiers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    outcome = Column(String(20), nullable=False)  # won, lost
    outcome_probability = Column(Float, default=0)
    contributing_factors = Column(JSONB, nullable=True)
    created_at = Column(DateTime(UTC), default=lambda: datetime.now(UTC))
