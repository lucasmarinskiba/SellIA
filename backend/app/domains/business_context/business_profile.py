"""Per-business profile: one BusinessContext row per business, owned by the business owner.

The legacy /business-context API keys contexts by user, with business_id optional, so one user with several
businesses has no single "their" profile there. This module is the business-scoped path: the row's business_id is
always set, and every read or write goes through the caller's access to that business.

Language lives in businesses.config["language"], where the offline triggers, the post-visit worker and the seasonal
suggestions already read it. Geography (country, city) comes from the business's locations, which are the source of
truth, so it is not duplicated here.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.business_context.models import BusinessContext
from app.domains.businesses.models import Business

# Fields the profile edits directly on the BusinessContext row.
PROFILE_FIELDS = (
    "business_type",
    "sales_model",
    "geographic_reach",
    "presence_type",
    "industry",
    "target_audience",
    "value_proposition",
    "price_range",
    "primary_goal",
    "has_physical_location",
    "does_delivery",
    "does_pickup",
)


async def get_or_create_profile(db: AsyncSession, business: Business) -> BusinessContext:
    row = (
        await db.execute(select(BusinessContext).where(BusinessContext.business_id == business.id))
    ).scalars().first()
    if row is None:
        row = BusinessContext(user_id=business.user_id, business_id=business.id)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


async def update_profile(db: AsyncSession, business: Business, changes: dict) -> BusinessContext:
    """Apply the given fields. A null value means "no change": every field here is optional on the way in."""
    row = await get_or_create_profile(db, business)
    language = changes.pop("language", None)
    for field, value in changes.items():
        if value is not None and field in PROFILE_FIELDS:
            setattr(row, field, value)
    if language is not None:
        # Reassign rather than mutate: SQLAlchemy only sees a JSON change when the whole dict is replaced.
        business.config = {**(business.config or {}), "language": language}
    await db.commit()
    await db.refresh(row)
    return row
