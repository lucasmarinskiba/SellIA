"""PostgreSQL Row-Level Security helpers.

Sets session variable so RLS policies can enforce business_id isolation.
"""

import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_rls_business_id(db: AsyncSession, business_id: uuid.UUID | None):
    """Set the RLS business_id session variable for the current DB connection."""
    if business_id:
        await db.execute(
            text("SET LOCAL app.current_business_id = :bid"),
            {"bid": str(business_id)},
        )
    else:
        await db.execute(text("SET LOCAL app.current_business_id = ''"))


async def clear_rls_business_id(db: AsyncSession):
    """Clear the RLS business_id session variable."""
    await db.execute(text("SET LOCAL app.current_business_id = ''"))
