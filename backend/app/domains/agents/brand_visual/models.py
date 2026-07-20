"""Brand Visual Agent Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class BrandKitJob(Base):
    """A brand kit generation job."""

    __tablename__ = "brand_kit_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    brand_name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False)
    colors = Column(JSONB, nullable=True)
    fonts = Column(JSONB, nullable=True)
    logo_url = Column(String(500), nullable=True)
    assets = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class BrandAsset(Base):
    """Individual brand asset generated for a kit."""

    __tablename__ = "brand_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("brand_kit_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)
    file_url = Column(String(500), nullable=False)
    config = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
