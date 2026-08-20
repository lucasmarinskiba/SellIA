"""Phase 40: Sales Funnel Intelligence - Complete Pipeline Orchestration."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class FunnelStage(str, Enum):
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    DECISION = "decision"
    ACQUISITION = "acquisition"
    RETENTION = "retention"
    ADVOCACY = "advocacy"

class LeadScore(Base):
    __tablename__ = "lead_scores"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    awareness_score = Column(Float, default=0)
    consideration_score = Column(Float, default=0)
    decision_score = Column(Float, default=0)
    acquisition_score = Column(Float, default=0)
    current_stage = Column(String(50), default=FunnelStage.AWARENESS)
    stage_confidence = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class FunnelOrchestration(Base):
    __tablename__ = "funnel_orchestration"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    current_stage = Column(String(50), nullable=False)
    next_recommended_action = Column(String(255), nullable=True)
    agent_assigned = Column(String(50), nullable=True)
    action_executed = Column(Boolean, default=False)
    action_result = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class FOMOGenerator(Base):
    __tablename__ = "fomo_generators"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fomo_trigger_type = Column(String(50), nullable=False)  # scarcity, social_proof, urgency, exclusivity
    fomo_intensity = Column(Float, default=0)
    message_sent = Column(String(500), nullable=True)
    engagement_response = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class NeedsIdentification(Base):
    __tablename__ = "needs_identification"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pain_points = Column(JSONB, nullable=True)
    business_objectives = Column(JSONB, nullable=True)
    decision_criteria = Column(JSONB, nullable=True)
    budget_range = Column(String(100), nullable=True)
    timeline = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class SolutionPresentation(Base):
    __tablename__ = "solution_presentations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    solution_type = Column(String(100), nullable=False)
    key_benefits = Column(JSONB, nullable=True)
    roi_projected = Column(Float, default=0)
    differentiation_points = Column(JSONB, nullable=True)
    presentation_date = Column(DateTime(timezone.utc), nullable=True)
    engagement_score = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ObjectionHandling(Base):
    __tablename__ = "objection_handling"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    objection_type = Column(String(100), nullable=False)
    objection_text = Column(Text, nullable=True)
    reframe_strategy = Column(Text, nullable=True)
    counter_argument = Column(Text, nullable=True)
    resolution_success = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class DealClosing(Base):
    __tablename__ = "deal_closing"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    closing_technique = Column(String(100), nullable=True)
    closing_probability = Column(Float, default=0)
    deal_value = Column(Float, default=0)
    deal_status = Column(String(50), default="open")  # open, pending, won, lost
    closing_date = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class CustomerFidelization(Base):
    __tablename__ = "customer_fidelization"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    satisfaction_score = Column(Float, default=0)
    loyalty_tier = Column(String(50), default="bronze")  # bronze, silver, gold, platinum
    retention_action = Column(String(255), nullable=True)
    next_touchpoint = Column(DateTime(timezone.utc), nullable=True)
    advocacy_readiness = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
