import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class WebsiteTemplate(str, Enum):
    MINIMAL = "minimal"
    CLASSIC = "classic"
    MODERN = "modern"
    ECOMMERCE = "ecommerce"
    PORTFOLIO = "portfolio"


class WebsiteStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Website(Base):
    __tablename__ = "websites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    template = Column(SQLEnum(WebsiteTemplate), nullable=False, default=WebsiteTemplate.MODERN)
    status = Column(SQLEnum(WebsiteStatus), nullable=False, default=WebsiteStatus.DRAFT)

    # Content
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    hero_image_url = Column(String(500), nullable=True)

    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    og_image_url = Column(String(500), nullable=True)

    # Configuration
    config = Column(JSONB, default=dict, nullable=False)  # colors, fonts, layout, etc
    pages = Column(JSONB, default=dict, nullable=False)  # page slugs + content

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", back_populates="website")
    domain = relationship("Domain", back_populates="website", uselist=False, cascade="all, delete-orphan")


class Domain(Base):
    __tablename__ = "domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Subdomain (e.g., "tunegocio" for "tunegocio.sellia.app")
    subdomain = Column(String(63), nullable=False, unique=True, index=True)

    # Custom domain (e.g., "mynegocio.com")
    custom_domain = Column(String(255), nullable=True, unique=True, index=True)

    # Domain verification
    is_primary = Column(Boolean, default=True)  # sellia.app subdomain is primary
    is_verified = Column(Boolean, default=False)  # custom domain verified

    # DNS records
    dns_records = Column(JSONB, default=dict, nullable=False)  # MX, CNAME, etc

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    website = relationship("Website", back_populates="domain")
