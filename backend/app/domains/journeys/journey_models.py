"""Customer journey orchestration models."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class JourneyType(str, Enum):
    LINEAR = "linear"
    BRANCHING = "branching"
    LOOP = "loop"


class NodeType(str, Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    WAIT = "wait"
    END = "end"


class CustomerJourney(Base):
    __tablename__ = "journeys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    journey_type = Column(String(50), default="linear")
    
    nodes = Column(JSONB, nullable=False)  # Graph nodes
    edges = Column(JSONB, nullable=False)  # Connections
    
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class JourneyVariant(Base):
    __tablename__ = "journey_variants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    
    variant_name = Column(String(100), nullable=False)
    variant_config = Column(JSONB, nullable=False)  # Variant-specific overrides
    
    traffic_allocation = Column(Float, default=50.0)  # % of audience
    is_control = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class JourneyExecution(Base):
    __tablename__ = "journey_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    variant_id = Column(UUID(as_uuid=True), ForeignKey("journey_variants.id", ondelete="SET NULL"), nullable=True)
    
    current_node_id = Column(String(100), nullable=True)
    status = Column(String(50), default="active")  # active, completed, abandoned
    
    execution_path = Column(JSONB, default=list)  # [node1, node2, ...]
    
    started_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone.utc), nullable=True)
    
    __table_args__ = (
        Index("idx_journey_customer", "journey_id", "customer_id"),
        Index("idx_journey_status", "journey_id", "status"),
    )


class JourneyMetrics(Base):
    __tablename__ = "journey_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    total_journeys = Column(Integer, default=0)
    completed_journeys = Column(Integer, default=0)
    abandoned_journeys = Column(Integer, default=0)
    
    avg_journey_duration_hours = Column(Float, default=0)
    completion_rate = Column(Float, default=0)
    
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ABTestResult(Base):
    __tablename__ = "ab_test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    
    variant_a_id = Column(UUID(as_uuid=True), ForeignKey("journey_variants.id"), nullable=False)
    variant_b_id = Column(UUID(as_uuid=True), ForeignKey("journey_variants.id"), nullable=False)
    
    metric_name = Column(String(100), nullable=False)  # completion_rate, conversion, revenue
    variant_a_value = Column(Float, nullable=False)
    variant_b_value = Column(Float, nullable=False)
    
    confidence_level = Column(Float, default=95.0)
    is_significant = Column(Boolean, default=False)
    winner = Column(String(10), nullable=True)  # A or B
    
    test_start_date = Column(DateTime(timezone.utc), nullable=False)
    test_end_date = Column(DateTime(timezone.utc), nullable=True)
    
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
