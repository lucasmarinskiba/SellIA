"""Per-platform selling economics.

A profit-and-loss statement needs costs, and most of them are not in any table
SellIA owns: what MercadoLibre charges this particular seller, what a unit
actually costs to make, what is spent on ads. Inventing plausible numbers for
those would produce a margin that looks authoritative and is fiction.

So the rule here is the same as everywhere else in this codebase: revenue comes
from real orders, costs come either from what the platform actually reported on
the order or from what the SELLER declared once in these settings -- and if
neither exists, the margin is reported as not computable, naming exactly what is
missing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class PlatformSettings(Base):
    """What the seller declares about the economics of one platform.

    Every field is optional. A NULL is not zero: it means "not declared", and
    the P&L says so instead of treating the cost as absent.
    """

    __tablename__ = "platform_settings"
    __table_args__ = (
        UniqueConstraint("business_id", "platform", name="uq_platform_settings_business_platform"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    platform = Column(String(40), nullable=False)

    #: Commission the platform charges this seller, in percent of the sale.
    commission_percent = Column(Numeric(6, 3), nullable=True)
    #: Flat fee the platform takes per order, in the platform's currency.
    fixed_fee_per_order = Column(Numeric(14, 2), nullable=True)
    #: Fallback cost of goods as a percentage of the sale, for sellers who do
    #: not load per-product costs. Used only when a product cost is unknown.
    cogs_percent = Column(Numeric(6, 3), nullable=True)
    #: Recurring platform costs that are not per order (subscription, store fee).
    monthly_fixed_cost = Column(Numeric(14, 2), nullable=True)
    #: Ad spend the seller declares for this platform, when it is not tracked by
    #: an ad integration.
    monthly_ad_spend = Column(Numeric(14, 2), nullable=True)

    currency = Column(String(3), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


PLATFORM_COMMERCE_TABLES = [PlatformSettings.__table__]
