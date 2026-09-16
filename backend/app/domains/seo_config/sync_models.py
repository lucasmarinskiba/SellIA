"""Models for platform listing sync tracking."""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, ForeignKey, func, Boolean, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PlatformSyncLog(Base):
    """Track every attempt to sync FOMO copy to a platform."""
    __tablename__ = "platform_sync_logs"
    __table_args__ = (
        Index("idx_link_sync", "link_id"),
        Index("idx_business_sync", "business_id"),
        Index("idx_platform_sync", "platform_name"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    link_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_links.id", ondelete="CASCADE"))
    fomo_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publication_link_fomo.id", ondelete="SET NULL"), nullable=True)

    # Platform target
    platform_name: Mapped[str] = mapped_column(String(50))  # mercado-libre, shopify, instagram, etc.
    external_listing_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # ID on the platform

    # What was synced
    sync_type: Mapped[str] = mapped_column(String(50))  # title_update, description_update, full_update

    # Status
    status: Mapped[str] = mapped_column(String(20))  # pending, synced, failed, skipped
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sync metadata
    data_sent: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # what we sent to platform
    response_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # platform's response

    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


SYNC_TABLES = [PlatformSyncLog.__table__]
