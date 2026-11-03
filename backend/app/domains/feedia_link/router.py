"""Owner-facing controls for the feedIA link: connect an account, see the feed's state, retry, backfill history."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.feedia_link import delivery
from app.domains.feedia_link.capture import COUNTED, _secret_key
from app.domains.feedia_link.models import FeediaLink, FeediaOutbox
from app.domains.feedia_link.signing import ACCOUNT_ID, sale_event
from app.domains.orders.models import Order
from app.domains.users.models import User

router = APIRouter()

BACKFILL_MAX = 500  # feedIA keeps at most 3000 orders per account


class LinkIn(BaseModel):
    account_id: str = Field(..., description="The id of the business's account in feedIA")
    enabled: bool = True


def _configured() -> bool:
    s = get_settings()
    return delivery.valid_base_url(s.FEEDIA_BASE_URL) and bool(s.SELLIA_WEBHOOK_SECRET)


async def _status(db: AsyncSession, business_id: UUID) -> dict:
    link = await db.get(FeediaLink, business_id)
    return {
        "linked": link is not None,
        "account_id": link.feedia_account_id if link else None,
        "enabled": bool(link and link.enabled),
        "link_error": link.last_error if link else None,
        # False until the platform owner sets FEEDIA_BASE_URL and SELLIA_WEBHOOK_SECRET: events queue meanwhile.
        "delivery_configured": _configured(),
        **await delivery.counts(db, business_id),
    }


@router.get("/link")
async def get_link(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await require_business_access(db, business_id, current_user)
    return await _status(db, business_id)


@router.put("/link")
async def set_link(
    business_id: UUID,
    data: LinkIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await require_business_access(db, business_id, current_user, manage=True)
    account = data.account_id.strip()
    if not ACCOUNT_ID.match(account):
        raise HTTPException(status_code=422, detail="El id de cuenta de feedIA no es válido (letras, números, - y _).")
    link = await db.get(FeediaLink, business_id)
    if link is None:
        db.add(FeediaLink(business_id=business_id, feedia_account_id=account, enabled=data.enabled))
    else:
        link.feedia_account_id, link.enabled, link.last_error = account, data.enabled, None
    await db.commit()
    await delivery.requeue_failed(db, business_id)  # a corrected id gets a second chance
    return await _status(db, business_id)


@router.delete("/link", status_code=204)
async def delete_link(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await require_business_access(db, business_id, current_user, manage=True)
    link = await db.get(FeediaLink, business_id)
    if link is not None:
        await db.delete(link)
        await db.commit()


@router.post("/retry")
async def retry_failed(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await require_business_access(db, business_id, current_user, manage=True)
    return {"requeued": await delivery.requeue_failed(db, business_id)}


@router.post("/backfill")
async def backfill(
    business_id: UUID,
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Queue the sales of the last `days` days so feedIA has history from day one. Safe to repeat."""
    await require_business_access(db, business_id, current_user, manage=True)
    link = await db.get(FeediaLink, business_id)
    if link is None or not link.enabled:
        raise HTTPException(status_code=409, detail="Primero conectá la cuenta de feedIA.")
    since = datetime.now(timezone.utc) - timedelta(days=days)
    orders = (
        await db.execute(
            select(Order)
            .where(Order.business_id == business_id, Order.status.in_(COUNTED), Order.created_at >= since)
            .order_by(Order.created_at.desc())
            .limit(BACKFILL_MAX)
        )
    ).scalars().all()
    known = set(
        (
            await db.execute(
                select(FeediaOutbox.order_id).where(
                    FeediaOutbox.business_id == business_id, FeediaOutbox.event_type == "sale"
                )
            )
        ).scalars().all()
    )
    key, queued = _secret_key(), 0
    for order in orders:
        if str(order.id) in known:
            continue
        db.add(
            FeediaOutbox(
                business_id=business_id,
                event_type="sale",
                order_id=str(order.id),
                payload=sale_event(
                    order_id=order.id,
                    total=order.total_amount,
                    when=order.paid_at or order.created_at,
                    business_id=business_id,
                    email=order.customer_email,
                    key=key,
                ),
            )
        )
        queued += 1
    await db.commit()
    return {"queued": queued, "already_queued": len(orders) - queued, "capped_at": BACKFILL_MAX}
