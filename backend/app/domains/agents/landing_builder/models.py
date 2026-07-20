"""Landing Page Builder Agent Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class LandingPageJob(Base):
    """Job de generación de landing pages."""
    __tablename__ = "landing_page_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | running | completed | failed
    product_id = Column(UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True, index=True)
    template_used = Column(String(100), nullable=True, default="modern")
    generated_code_url = Column(String(500), nullable=True)  # ruta al ZIP o carpeta
    preview_url = Column(String(500), nullable=True)
    variants = Column(JSONB, default=list, nullable=False)  # [LandingVariant, ...]
    generated_code = Column(JSONB, default=dict, nullable=False)  # {files: {path: content}}
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
