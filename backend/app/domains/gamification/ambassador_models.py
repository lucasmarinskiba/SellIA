"""
Ambassador & Certification Models (extends gamification)

Transforms users into referents and industry leaders.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class CertificationProgram(Base):
    """A certification program users can complete."""
    __tablename__ = "certification_programs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    level = Column(String(50), nullable=False)  # beginner | intermediate | advanced | expert
    category = Column(String(50), nullable=False)  # sales | marketing | automation | ai

    # Requirements
    requirements = Column(JSONB, default=list, nullable=False)
    # [{"type": "complete_course", "item_id": "..."}, {"type": "achieve_x_sales", "count": 10}]

    # Badge
    badge_image_url = Column(String(500), nullable=True)
    badge_color = Column(String(20), default="#F97316", nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserCertification(Base):
    """Tracks user progress and completion of certifications."""
    __tablename__ = "user_certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey("certification_programs.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(20), default="in_progress", nullable=False)  # in_progress | completed | expired
    progress_percent = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Public verification
    certificate_id = Column(String(50), nullable=True, unique=True, index=True)  # e.g. "SEL-2024-ABC123"
    is_public = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PublicExpertProfile(Base):
    """A public mini-page showcasing a user as a referent."""
    __tablename__ = "public_expert_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    slug = Column(String(100), nullable=False, unique=True, index=True)
    headline = Column(String(255), nullable=False)
    bio = Column(Text, nullable=False)
    specialty = Column(String(100), nullable=False)  # "E-commerce AI", "Real Estate Automation"

    # Social proof
    total_sales_helped = Column(Integer, default=0, nullable=False)
    total_revenue_helped = Column(Integer, default=0, nullable=False)
    testimonials = Column(JSONB, default=list, nullable=False)

    # Content
    featured_case_studies = Column(JSONB, default=list, nullable=False)
    social_links = Column(JSONB, default=dict, nullable=False)

    # Badges & certs
    displayed_badges = Column(JSONB, default=list, nullable=False)

    # Visibility
    is_published = Column(Boolean, default=False, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    contact_clicks = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
