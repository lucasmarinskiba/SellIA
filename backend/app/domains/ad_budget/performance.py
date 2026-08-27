"""Per-channel spend / revenue / ROAS ingestion.

Priority order for the numbers:
  1. Ad-platform API (via the channel connector) when a connection is linked
     and the platform exposes insights (Meta today).
  2. Fallback: spend from the `ad_spend_*` GL accounts + revenue from orders
     attributed to the channel (substring match on campaign / channel tags).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.ad_budget.models import (
    LEDGER_SUBTYPE_BY_PLATFORM,
    AdChannel,
    AdPerformanceSnapshot,
)

logger = get_logger(__name__)

ZERO = Decimal("0")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _roas(revenue: Decimal, spend: Decimal) -> Decimal:
    if spend and spend > 0:
        return (revenue / spend).quantize(Decimal("0.0001"))
    return ZERO


class AdPerformanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def gather(self, business_id: uuid.UUID, channel: AdChannel, window_days: int) -> dict[str, Any]:
        end = _utcnow()
        start = end - timedelta(days=window_days)
        recent_start = end - timedelta(days=max(1, window_days // 3))

        data = await self._from_connector(channel, start, end, recent_start)
        if data is None:
            data = await self._from_ledger_and_orders(business_id, channel, start, end, recent_start)

        data["window_start"] = start
        data["window_end"] = end
        data["roas"] = _roas(data["revenue"], data["spend"])
        data["recent_roas"] = (
            _roas(data["recent_revenue"], data["recent_spend"])
            if data.get("recent_spend")
            else None
        )
        return data

    # ------------------------------------------------------------------
    async def _from_connector(
        self, channel: AdChannel, start: datetime, end: datetime, recent_start: datetime
    ) -> Optional[dict[str, Any]]:
        if not channel.channel_connection_id or not channel.campaign_refs:
            return None
        try:
            from app.domains.channels.connectors import get_connector
            from app.domains.channels.models import ChannelConnection

            conn = (
                await self.db.execute(
                    select(ChannelConnection).where(
                        ChannelConnection.id == channel.channel_connection_id
                    )
                )
            ).scalar_one_or_none()
            if not conn:
                return None
            connector = get_connector(conn.platform, conn.credentials, conn.settings)
            if not hasattr(connector, "get_insights"):
                return None

            spend = ZERO
            revenue = ZERO
            conversions = 0
            clicks = 0
            impressions = 0
            for ref in channel.campaign_refs:
                ins = await connector.get_insights(str(ref), level="campaign")
                spend += Decimal(str(ins.get("spend", 0) or 0))
                revenue += _extract_conversion_value(ins)
                conversions += _extract_conversions(ins)
                clicks += int(float(ins.get("clicks", 0) or 0))
                impressions += int(float(ins.get("impressions", 0) or 0))

            return {
                "source": "connector",
                "spend": spend.quantize(Decimal("0.01")),
                "revenue": revenue.quantize(Decimal("0.01")),
                "conversions": conversions,
                "clicks": clicks,
                "impressions": impressions,
                # connector insights are already windowed by date_preset; we can't
                # cheaply split a recent sub-window, so leave trend unset.
                "recent_spend": None,
                "recent_revenue": None,
            }
        except Exception as e:  # noqa: BLE001
            logger.warning("ad_budget: connector insights failed for channel %s: %s", channel.id, e)
            return None

    # ------------------------------------------------------------------
    async def _from_ledger_and_orders(
        self,
        business_id: uuid.UUID,
        channel: AdChannel,
        start: datetime,
        end: datetime,
        recent_start: datetime,
    ) -> dict[str, Any]:
        spend = await self._ledger_spend(business_id, channel.platform, start, end)
        recent_spend = await self._ledger_spend(business_id, channel.platform, recent_start, end)
        revenue, conversions = await self._attributed_revenue(business_id, channel, start, end)
        recent_revenue, _ = await self._attributed_revenue(business_id, channel, recent_start, end)
        return {
            "source": "ledger",
            "spend": spend,
            "revenue": revenue,
            "conversions": conversions,
            "clicks": 0,
            "impressions": 0,
            "recent_spend": recent_spend,
            "recent_revenue": recent_revenue,
        }

    async def _ledger_spend(
        self, business_id: uuid.UUID, platform: str, start: datetime, end: datetime
    ) -> Decimal:
        try:
            from app.domains.ledger.models import (
                JournalEntry,
                JournalLine,
                JournalStatus,
                LedgerAccount,
            )

            subtype = LEDGER_SUBTYPE_BY_PLATFORM.get(platform, "ad_spend_other")
            res = await self.db.execute(
                select(func.coalesce(func.sum(JournalLine.debit - JournalLine.credit), 0))
                .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
                .join(LedgerAccount, LedgerAccount.id == JournalLine.account_id)
                .where(
                    JournalLine.business_id == business_id,
                    LedgerAccount.subtype == subtype,
                    JournalEntry.status == JournalStatus.POSTED.value,
                    JournalEntry.entry_date >= start,
                    JournalEntry.entry_date < end,
                )
            )
            return Decimal(str(res.scalar() or 0)).quantize(Decimal("0.01"))
        except Exception as e:  # noqa: BLE001
            logger.warning("ad_budget: ledger spend lookup failed: %s", e)
            return ZERO

    async def _attributed_revenue(
        self, business_id: uuid.UUID, channel: AdChannel, start: datetime, end: datetime
    ) -> tuple[Decimal, int]:
        from app.domains.orders.models import Order, PaymentStatus

        matches = [m for m in (channel.attribution_match or []) if m] or [channel.platform]
        like_clauses = []
        for m in matches:
            pat = f"%{m}%"
            like_clauses.append(Order.source_campaign.ilike(pat))
            like_clauses.append(Order.source_channel.ilike(pat))
            like_clauses.append(Order.last_touch_channel.ilike(pat))
            like_clauses.append(Order.first_touch_channel.ilike(pat))

        res = await self.db.execute(
            select(
                func.coalesce(func.sum(Order.total_amount), 0),
                func.count(Order.id),
            ).where(
                Order.business_id == business_id,
                Order.payment_status == PaymentStatus.COMPLETED,
                func.coalesce(Order.paid_at, Order.created_at) >= start,
                func.coalesce(Order.paid_at, Order.created_at) < end,
                or_(*like_clauses),
            )
        )
        total, count = res.one()
        return Decimal(str(total or 0)).quantize(Decimal("0.01")), int(count or 0)

    # ------------------------------------------------------------------
    async def snapshot(
        self, business_id: uuid.UUID, channel: AdChannel, metrics: dict[str, Any]
    ) -> AdPerformanceSnapshot:
        conv = metrics.get("conversions") or 0
        cpa = (
            (metrics["spend"] / Decimal(conv)).quantize(Decimal("0.01"))
            if conv and metrics["spend"] > 0
            else None
        )
        snap = AdPerformanceSnapshot(
            business_id=business_id,
            ad_channel_id=channel.id,
            window_start=metrics["window_start"],
            window_end=metrics["window_end"],
            source=metrics.get("source", "ledger"),
            spend=metrics["spend"],
            revenue=metrics["revenue"],
            conversions=conv,
            clicks=metrics.get("clicks", 0),
            impressions=metrics.get("impressions", 0),
            roas=metrics["roas"],
            cpa=cpa,
            recent_roas=metrics.get("recent_roas"),
        )
        self.db.add(snap)
        await self.db.flush()
        return snap

    async def latest_snapshot(
        self, channel_id: uuid.UUID
    ) -> Optional[AdPerformanceSnapshot]:
        res = await self.db.execute(
            select(AdPerformanceSnapshot)
            .where(AdPerformanceSnapshot.ad_channel_id == channel_id)
            .order_by(AdPerformanceSnapshot.captured_at.desc())
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def reconcile_spend_to_ledger(
        self, business_id: uuid.UUID, channel: AdChannel, metrics: dict[str, Any]
    ) -> None:
        """When spend came from the platform API, mirror it into the GL so the
        ledger stays the single source of truth. Idempotent per channel+day."""
        if metrics.get("source") != "connector" or metrics["spend"] <= 0:
            return
        try:
            from app.domains.ledger.posting import PostingService
            from app.domains.ledger.service import LedgerService

            day = _utcnow().strftime("%Y-%m-%d")
            await LedgerService(self.db).ensure_setup(business_id, channel.currency)
            await PostingService(self.db).post_ad_spend(
                business_id,
                platform=channel.platform,
                amount=metrics["spend"],
                spend_ref=f"{channel.id}:{day}",
                currency=channel.currency,
                campaign=channel.display_name,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("ad_budget: spend reconcile to ledger failed: %s", e)


def _extract_conversion_value(insights: dict[str, Any]) -> Decimal:
    cv = insights.get("conversion_values") or insights.get("conversion_value")
    if isinstance(cv, list):
        return sum((Decimal(str(x.get("value", 0) or 0)) for x in cv), ZERO)
    if cv:
        return Decimal(str(cv))
    for action in insights.get("action_values", []) or []:
        if action.get("action_type") in ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"):
            return Decimal(str(action.get("value", 0) or 0))
    return ZERO


def _extract_conversions(insights: dict[str, Any]) -> int:
    c = insights.get("conversions")
    if isinstance(c, (int, float)):
        return int(c)
    total = 0
    for action in insights.get("actions", []) or []:
        if action.get("action_type") in ("purchase", "omni_purchase", "lead", "offsite_conversion.fb_pixel_purchase"):
            total += int(float(action.get("value", 0) or 0))
    return total
