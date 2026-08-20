"""Phase 51: AI Content Generation & Auto-Optimization."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base


class ContentTemplate(Base):
    __tablename__ = "content_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    template_name = Column(String(255), nullable=False)
    template_type = Column(String(50), nullable=False)  # product_title, product_description, social_post, email_subject, email_body
    platform = Column(String(50), nullable=True)  # amazon, mercado_libre, instagram, etc
    template_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class GeneratedContent(Base):
    __tablename__ = "generated_content"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    content_type = Column(String(50), nullable=False)  # title, description, social_post, email, listing
    platform = Column(String(50), nullable=True)
    original_content = Column(Text, nullable=True)
    generated_content = Column(Text, nullable=False)
    content_length = Column(Integer, default=0)
    seo_score = Column(Float, default=0)
    engagement_score = Column(Float, default=0)
    is_approved = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime(timezone.utc), nullable=True)


class ContentPerformance(Base):
    __tablename__ = "content_performance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_content_id = Column(UUID(as_uuid=True), ForeignKey("generated_content.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    platform = Column(String(50), nullable=False)
    views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0)
    engagement_rate = Column(Float, default=0)
    ctr = Column(Float, default=0)
    conversion_rate = Column(Float, default=0)
    tracked_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class BulkContentGeneration(Base):
    __tablename__ = "bulk_content_generation"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_name = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)
    platform = Column(String(50), nullable=True)
    product_ids = Column(ARRAY(UUID), nullable=False)
    total_items = Column(Integer, default=0)
    generated_count = Column(Integer, default=0)
    approved_count = Column(Integer, default=0)
    published_count = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone.utc), nullable=True)


class ContentVariant(Base):
    __tablename__ = "content_variants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_content_id = Column(UUID(as_uuid=True), ForeignKey("generated_content.id", ondelete="CASCADE"), nullable=False)
    variant_number = Column(Integer, default=1)  # variant 1, 2, 3, etc
    variant_text = Column(Text, nullable=False)
    variant_style = Column(String(50), nullable=False)  # formal, casual, urgent, playful, technical
    seo_score = Column(Float, default=0)
    engagement_score = Column(Float, default=0)
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
