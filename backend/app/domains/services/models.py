"""Services & Appointments Models

Gestión de entregas de servicios, citas y agenda del prestador.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


class ServiceModality(str, enum.Enum):
    HOME_OFFICE = "home_office"
    CLIENT_OFFICE = "client_office"
    CLIENT_HOME = "client_home"
    PROVIDER_OFFICE = "provider_office"
    HYBRID = "hybrid"
    REMOTE = "remote"
    ON_SITE = "on_site"


class SolutionType(str, enum.Enum):
    TEMPORARY = "temporary"
    DEFINITIVE = "definitive"
    CONTINGENCY = "contingency"
    ANALYTICAL = "analytical"
    HEURISTIC = "heuristic"
    CREATIVE = "creative"
    ARCHITECTURAL = "architectural"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    STRUCTURAL = "structural"
    INSTALLATION = "installation"
    DIAGNOSTIC = "diagnostic"
    PROTECTION = "protection"
    AUTOMATION = "automation"
    COMFORT = "comfort"
    PSYCHOLOGICAL = "psychological"
    ADVISORY = "advisory"
    EMOTIONAL = "emotional"
    BEHAVIORAL = "behavioral"
    GUIDANCE = "guidance"
    RELIEF = "relief"
    CAUSALITY = "causality"
    RITUAL = "ritual"
    MEANING = "meaning"
    COMMUNITY = "community"
    MORAL = "moral"
    CONSOLATION = "consolation"


class ServiceDeliveryStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    REMINDED = "reminded"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ServiceDelivery(Base):
    """Entrega de un servicio vendido."""
    __tablename__ = "service_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    catalog_item_id = Column(UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Service details
    modality = Column(Enum(ServiceModality), nullable=True)
    solution_type = Column(Enum(SolutionType), nullable=True)
    status = Column(Enum(ServiceDeliveryStatus), default=ServiceDeliveryStatus.SCHEDULED, nullable=False, index=True)

    # Location
    location_address = Column(JSONB, default=dict, nullable=False)
    meeting_url = Column(Text, nullable=True)

    # Provider notes & client feedback
    provider_notes = Column(Text, nullable=True)
    client_feedback = Column(Text, nullable=True)
    client_rating = Column(Integer, nullable=True)  # 1-5

    # Structured data
    materials_used = Column(JSONB, default=list, nullable=False)  # [{"name": "...", "qty": 1, "cost": 0}]
    diagnosis = Column(JSONB, default=dict, nullable=False)       # {"findings": "...", "severity": "...", "recommendations": "..."}
    follow_up_required = Column(Boolean, default=False, nullable=False)
    follow_up_notes = Column(Text, nullable=True)

    # Reminders tracking
    reminders_sent = Column(JSONB, default=list, nullable=False)  # [{"type": "24h", "channel": "whatsapp", "sent_at": "..."}]

    # Duration tracking
    estimated_duration_minutes = Column(Integer, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Appointment(Base):
    """Cita individual en la agenda del prestador."""
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    service_delivery_id = Column(UUID(as_uuid=True), ForeignKey("service_deliveries.id", ondelete="CASCADE"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)

    # Client info
    client_name = Column(String(255), nullable=True)
    client_email = Column(String(255), nullable=True)
    client_phone = Column(String(50), nullable=True)

    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(50), default="America/Argentina/Buenos_Aires", nullable=False)

    # Service context
    modality = Column(Enum(ServiceModality), nullable=True)
    solution_type = Column(Enum(SolutionType), nullable=True)
    service_name = Column(String(255), nullable=True)  # nombre del servicio vendido

    # Location
    location_address = Column(JSONB, default=dict, nullable=False)
    meeting_url = Column(Text, nullable=True)

    # Status
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False, index=True)

    # Communication tracking
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    confirmation_sent_at = Column(DateTime(timezone=True), nullable=True)
    confirmation_received_at = Column(DateTime(timezone=True), nullable=True)
    feedback_sent_at = Column(DateTime(timezone=True), nullable=True)
    feedback_received_at = Column(DateTime(timezone=True), nullable=True)

    # Provider notes
    provider_notes = Column(Text, nullable=True)
    preparation_notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
