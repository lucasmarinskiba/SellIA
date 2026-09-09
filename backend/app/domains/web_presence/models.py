"""The real links an account actually sells from — and the last real audit of each.

Why this table exists: business_contexts.channels_configured only ever stored
booleans ({"instagram": true, "mercadolibre": false}). A boolean cannot be
audited, cannot be positioned in search, and cannot be cross-linked -- so the
SEO and authority tools had nothing real to work on and fell back to describing
a site nobody had ever fetched. The frontend did collect real per-platform URLs,
but only in localStorage (frontend/src/lib/business-profile.ts), where no
backend job could ever reach them.

Each row is one URL the account owns. The audit columns hold the result of the
last REAL fetch of that URL (see fetcher.py / analyzer.py): status code,
measured response time, page title, and the on-page SEO signals found in the
HTML. Nothing here is ever inferred -- a column is NULL until the URL has
actually been fetched.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class LinkKind(str, enum.Enum):
    WEBSITE = "website"          # su web propia / landing / blog
    SOCIAL = "social"            # perfil de red social
    MARKETPLACE = "marketplace"  # tienda o publicación en un marketplace
    OTHER = "other"


#: Platform slug -> (kind, human label). Kept in sync with the frontend's
#: PLATFORM_META so a badge on either side never invents its own label.
PLATFORM_KINDS: dict[str, tuple[LinkKind, str]] = {
    "own_site": (LinkKind.WEBSITE, "Sitio propio"),
    "landing": (LinkKind.WEBSITE, "Landing"),
    "blog": (LinkKind.WEBSITE, "Blog"),
    "instagram": (LinkKind.SOCIAL, "Instagram"),
    "facebook": (LinkKind.SOCIAL, "Facebook"),
    "tiktok": (LinkKind.SOCIAL, "TikTok"),
    "youtube": (LinkKind.SOCIAL, "YouTube"),
    "linkedin": (LinkKind.SOCIAL, "LinkedIn"),
    "twitter": (LinkKind.SOCIAL, "Twitter/X"),
    "threads": (LinkKind.SOCIAL, "Threads"),
    "pinterest": (LinkKind.SOCIAL, "Pinterest"),
    "whatsapp": (LinkKind.SOCIAL, "WhatsApp"),
    "mercadolibre": (LinkKind.MARKETPLACE, "MercadoLibre"),
    "amazon": (LinkKind.MARKETPLACE, "Amazon"),
    "shopify": (LinkKind.MARKETPLACE, "Shopify"),
    "tiendanube": (LinkKind.MARKETPLACE, "Tiendanube"),
    "etsy": (LinkKind.MARKETPLACE, "Etsy"),
    "hotmart": (LinkKind.MARKETPLACE, "Hotmart"),
    "tiktok_shop": (LinkKind.MARKETPLACE, "TikTok Shop"),
}


class BusinessLink(Base):
    __tablename__ = "business_links"
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_business_links_user_url"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    business_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    platform = Column(String(40), nullable=False)
    kind = Column(Enum(LinkKind), nullable=False, default=LinkKind.OTHER)
    url = Column(String(1024), nullable=False)
    label = Column(String(200), nullable=True)
    #: The one link that represents the business itself (its site, or its main
    #: store when it has no site). Authority scoring treats it as the hub every
    #: other profile should point back to.
    is_primary = Column(Boolean, nullable=False, default=False)

    # ── last REAL fetch of this URL (all NULL until it has been audited) ──
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    http_status = Column(Integer, nullable=True)
    final_url = Column(String(1024), nullable=True)      # after redirects
    response_ms = Column(Integer, nullable=True)         # measured, not estimated
    content_bytes = Column(Integer, nullable=True)
    fetch_error = Column(String(300), nullable=True)

    #: Full analyzer output for the last audit: title/meta/headings/schema/
    #: images/links/issues. Shape is analyzer.PageAudit.as_dict().
    audit = Column(JSONB, nullable=True)
    #: 0-100, computed by analyzer.score_page from the audit above.
    seo_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


WEB_PRESENCE_TABLES = [BusinessLink.__table__]
