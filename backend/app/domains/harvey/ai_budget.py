"""A monthly cap on the AI tokens each business spends through Harvey, charged to the business's owner.

Harvey, the market brief and "complete from my website" all use SellIA's own Anthropic key, so without a cap every
business's usage lands on one bill. Every model call is metered (input + output tokens from the API's own usage
numbers) into ``usage_tracking`` under ``harvey_ai_tokens_monthly``, and a call is refused once the month's cap is
reached. Callers degrade instead of failing: a reply goes to a person, a brief falls back to the plain facts.

The cap comes from the plan's ``limits["harvey_ai_tokens_monthly"]`` when the plan defines it, otherwise from
``DEFAULT_MONTHLY`` by plan slug. An account with no subscription (every account today) gets the free-plan cap.
``-1`` means unlimited; superusers are unlimited. Any error while reading the limit fails OPEN: billing trouble must
never stop prospecting.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

METRIC = "harvey_ai_tokens_monthly"
# ~1k tokens per drafted email: the free cap is about a hundred drafts a month.
DEFAULT_MONTHLY: dict[str, int] = {"free": 100_000, "starter": 500_000, "pro": 2_000_000, "enterprise": -1}
NO_SUBSCRIPTION_SLUG = "free"
WARN_AT = 0.8


class BudgetExceeded(Exception):
    """This month's AI allowance is used up."""


@dataclass
class Meter:
    tokens: int = 0

    def add(self, n: int) -> None:
        self.tokens += max(0, int(n))


_current: ContextVar[Meter | None] = ContextVar("harvey_ai_meter", default=None)


def record_tokens(n: int) -> None:
    """Called by the model client after each call; a no-op outside ``metered``."""
    meter = _current.get()
    if meter is not None:
        meter.add(n)


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


async def monthly_limit(db: AsyncSession, user_id: Any) -> int:
    """Tokens per month for this owner; -1 = unlimited. Fails open."""
    try:
        from app.domains.subscriptions.models import Subscription, SubscriptionPlan
        from app.domains.users.models import User

        async with db.begin_nested():  # a failed lookup must not abort the caller's transaction
            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
            if user is not None and getattr(user, "is_superuser", False):
                return -1
            row = (
                await db.execute(
                    select(SubscriptionPlan)
                    .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
                    .where(Subscription.user_id == user_id)
                )
            ).scalars().first()
        slug = row.slug if row is not None else NO_SUBSCRIPTION_SLUG
        explicit = (row.limits or {}).get(METRIC) if row is not None else None
        if isinstance(explicit, int | float) and not isinstance(explicit, bool):
            return int(explicit)
        return DEFAULT_MONTHLY.get(slug, DEFAULT_MONTHLY[NO_SUBSCRIPTION_SLUG])
    except Exception:  # noqa: BLE001 - fail open
        logger.warning("harvey: could not read the AI cap; allowing", exc_info=True)
        return -1


async def tokens_used(db: AsyncSession, user_id: Any) -> int:
    try:
        from app.domains.subscriptions.models import UsageTracking

        async with db.begin_nested():
            total = (
                await db.execute(
                    select(func.coalesce(func.sum(UsageTracking.quantity), 0)).where(
                        UsageTracking.user_id == user_id,
                        UsageTracking.metric_type == METRIC,
                        UsageTracking.period_month == _month(),
                    )
                )
            ).scalar()
        return int(total or 0)
    except Exception:  # noqa: BLE001 - fail open
        logger.warning("harvey: could not read AI usage; assuming none", exc_info=True)
        return 0


async def status(db: AsyncSession, user_id: Any) -> dict[str, Any]:
    limit = await monthly_limit(db, user_id)
    used = await tokens_used(db, user_id)
    unlimited = limit < 0
    return {
        "used": used,
        "limit": limit,
        "remaining": None if unlimited else max(0, limit - used),
        "percent": None if unlimited or limit == 0 else min(100, round(100 * used / limit)),
        "near_limit": (not unlimited) and limit > 0 and used >= WARN_AT * limit,
        "exceeded": (not unlimited) and used >= limit,
    }


async def _persist(db: AsyncSession, user_id: Any, business_id: uuid.UUID, tokens: int) -> None:
    """Its own session: the caller's transaction may be mid-flight and this must not commit or roll it back."""
    try:
        from app.domains.subscriptions.models import UsageTracking

        engine = db.bind
        if engine is None:
            from app.core.database import AsyncSessionLocal

            own = AsyncSessionLocal()
        else:
            own = AsyncSession(engine, expire_on_commit=False)
        async with own:
            own.add(
                UsageTracking(
                    user_id=user_id, business_id=business_id, metric_type=METRIC, quantity=tokens, period_month=_month()
                )
            )
            await own.commit()
    except Exception:  # noqa: BLE001 - metering must never break the call that already happened
        logger.warning("harvey: could not record %s AI tokens", tokens, exc_info=True)


@asynccontextmanager
async def metered(db: AsyncSession, business: Any, *, enforce: bool = True) -> AsyncIterator[Meter]:
    """Run model calls under the owner's monthly cap and record what they used.

    Raises ``BudgetExceeded`` on entry when the cap is already used up. Tokens are recorded on exit, even if the body
    raised: a failed call may still have been billed.
    """
    user_id = getattr(business, "user_id", None)
    if user_id is None:  # cannot attribute the spend (should not happen for a real business)
        yield Meter()
        return
    if enforce:
        st = await status(db, user_id)
        if st["exceeded"]:
            raise BudgetExceeded(
                "Llegaste al límite de IA de tu plan este mes. Se renueva el mes próximo, o podés subir de plan."
            )
    meter = Meter()
    token = _current.set(meter)
    try:
        yield meter
    finally:
        _current.reset(token)
        if meter.tokens:
            await _persist(db, user_id, business.id, meter.tokens)
