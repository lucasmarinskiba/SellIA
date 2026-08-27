"""Load regularly-spaced demand series from orders (+ ledger ad-spend exog)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.forecasting.types import Grain, SeriesLevel, SeriesSpec, TargetKind, TimeSeries

logger = get_logger(__name__)

_PAID_STATES = ("completed", "paid")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DemandDataLoader:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    async def _order_rows(
        self, business_id: uuid.UUID, start: datetime, end: datetime
    ) -> pd.DataFrame:
        from app.domains.orders.models import Order

        res = await self.db.execute(
            select(
                func.coalesce(Order.paid_at, Order.created_at).label("ts"),
                Order.total_amount,
                Order.discount_amount,
                Order.source_channel,
                Order.items,
            ).where(
                Order.business_id == business_id,
                func.lower(func.cast(Order.payment_status, __import__("sqlalchemy").String)).in_(_PAID_STATES),
                func.coalesce(Order.paid_at, Order.created_at) >= start,
                func.coalesce(Order.paid_at, Order.created_at) < end,
            )
        )
        rows = res.all()
        if not rows:
            return pd.DataFrame(columns=["ts", "total_amount", "discount_amount", "source_channel", "items"])
        df = pd.DataFrame(rows, columns=["ts", "total_amount", "discount_amount", "source_channel", "items"])
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
        df["total_amount"] = df["total_amount"].astype(float)
        df["discount_amount"] = df["discount_amount"].fillna(0).astype(float)
        return df

    async def _daily_ad_spend(
        self, business_id: uuid.UUID, index: pd.DatetimeIndex
    ) -> pd.Series:
        try:
            from app.domains.ledger.models import (
                AccountType,
                JournalEntry,
                JournalLine,
                JournalStatus,
                LedgerAccount,
            )

            res = await self.db.execute(
                select(
                    func.date_trunc("day", JournalEntry.entry_date).label("d"),
                    func.coalesce(func.sum(JournalLine.debit - JournalLine.credit), 0),
                )
                .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
                .join(LedgerAccount, LedgerAccount.id == JournalLine.account_id)
                .where(
                    JournalLine.business_id == business_id,
                    LedgerAccount.subtype.like("ad_spend%"),
                    JournalEntry.status == JournalStatus.POSTED.value,
                    JournalEntry.entry_date >= index[0],
                    JournalEntry.entry_date < index[-1] + pd.Timedelta(days=1),
                )
                .group_by("d")
            )
            s = pd.Series(0.0, index=index)
            for d, amt in res.all():
                ts = pd.Timestamp(d, tz="UTC").normalize()
                if ts in s.index:
                    s.loc[ts] = float(amt or 0)
            return s
        except Exception as e:  # noqa: BLE001
            logger.debug("forecasting: ad-spend exog unavailable: %s", e)
            return pd.Series(0.0, index=index)

    # ------------------------------------------------------------------
    async def load(
        self,
        spec: SeriesSpec,
        *,
        lookback_days: int = 540,
        end: Optional[datetime] = None,
        min_points: int = 28,
    ) -> Optional[TimeSeries]:
        end = (end or _utcnow()).replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=lookback_days)
        business_id = uuid.UUID(spec.business_id) if isinstance(spec.business_id, str) else spec.business_id

        df = await self._order_rows(business_id, start, end)
        freq = "D" if spec.grain == Grain.DAILY else "W-MON"
        full_index = pd.date_range(start=start, end=end - timedelta(days=1), freq=freq, tz="UTC")
        if len(full_index) < min_points:
            return None

        if spec.level == SeriesLevel.PRODUCT:
            series, price = self._product_series(df, spec.key, spec.target)
        elif spec.level == SeriesLevel.CHANNEL:
            series, price = self._channel_series(df, spec.key, spec.target)
        else:
            series, price = self._total_series(df, spec.target)

        if series.empty or series.sum() == 0:
            return None

        y = series.reindex(pd.to_datetime(series.index, utc=True)).resample(freq).sum()
        y = y.reindex(full_index).fillna(0.0)
        price = (
            price.resample(freq).mean().reindex(full_index).ffill().fillna(0.0)
            if price is not None and not price.empty
            else pd.Series(0.0, index=full_index)
        )

        promo = (
            df.assign(d=df["ts"].dt.floor("D"))
            .groupby("d")["discount_amount"].apply(lambda x: float((x > 0).mean()))
        )
        promo = promo.resample(freq).mean().reindex(full_index).fillna(0.0) if not promo.empty else pd.Series(0.0, index=full_index)

        ad_spend = await self._daily_ad_spend(business_id, full_index)
        ad_spend = ad_spend.resample(freq).sum().reindex(full_index).fillna(0.0)

        exog = pd.DataFrame(
            {"price": price.values, "promo": promo.values, "ad_spend": ad_spend.values},
            index=full_index,
        )

        nz = int((y.values > 0).sum())
        if nz < 4:
            return None

        return TimeSeries(spec=spec, index=full_index, values=y.values.astype(float), exog=exog)

    # ------------------------------------------------------------------
    def _total_series(self, df: pd.DataFrame, target: TargetKind):
        if df.empty:
            return pd.Series(dtype=float), None
        g = df.set_index("ts")
        if target == TargetKind.ORDERS:
            s = g["total_amount"].groupby(g.index.floor("D")).count().astype(float)
        elif target == TargetKind.UNITS:
            df2 = df.copy()
            df2["units"] = df2["items"].apply(_sum_units)
            s = df2.set_index("ts")["units"].groupby(df2["ts"].dt.floor("D")).sum().astype(float)
        else:
            s = g["total_amount"].groupby(g.index.floor("D")).sum().astype(float)
        price = None
        return s, price

    def _channel_series(self, df: pd.DataFrame, key: str | None, target: TargetKind):
        if df.empty or not key:
            return pd.Series(dtype=float), None
        sub = df[df["source_channel"].fillna("").str.lower() == key.lower()]
        return self._total_series(sub, target)

    def _product_series(self, df: pd.DataFrame, sku: str | None, target: TargetKind):
        if df.empty or not sku:
            return pd.Series(dtype=float), None
        recs = []
        for _, row in df.iterrows():
            for it in _iter_items(row["items"]):
                if str(it.get("sku") or it.get("name") or "").strip() != str(sku).strip():
                    continue
                qty = float(it.get("qty") or it.get("quantity") or 1)
                price = float(it.get("price") or 0)
                recs.append({"ts": row["ts"], "units": qty, "revenue": qty * price, "price": price})
        if not recs:
            return pd.Series(dtype=float), None
        pdf = pd.DataFrame(recs).set_index("ts")
        col = "units" if target != TargetKind.REVENUE else "revenue"
        s = pdf[col].groupby(pdf.index.floor("D")).sum().astype(float)
        price = pdf["price"].groupby(pdf.index.floor("D")).mean()
        return s, price

    # ------------------------------------------------------------------
    async def discover_series(
        self, business_id: uuid.UUID, *, top_products: int = 20, top_channels: int = 8
    ) -> list[SeriesSpec]:
        """Auto-pick which series are worth forecasting for a business."""
        end = _utcnow()
        df = await self._order_rows(business_id, end - timedelta(days=180), end)
        bid = str(business_id)
        specs = [SeriesSpec(business_id=bid, level=SeriesLevel.TOTAL, target=TargetKind.REVENUE),
                 SeriesSpec(business_id=bid, level=SeriesLevel.TOTAL, target=TargetKind.ORDERS)]
        if df.empty:
            return specs

        ch = (
            df.assign(c=df["source_channel"].fillna("unknown").str.lower())
            .groupby("c")["total_amount"].sum().sort_values(ascending=False)
        )
        for c in ch.head(top_channels).index:
            if c and c != "unknown":
                specs.append(SeriesSpec(business_id=bid, level=SeriesLevel.CHANNEL,
                                        target=TargetKind.REVENUE, key=c, label=c))

        sku_rev: dict[str, float] = {}
        for _, row in df.iterrows():
            for it in _iter_items(row["items"]):
                k = str(it.get("sku") or it.get("name") or "").strip()
                if not k:
                    continue
                sku_rev[k] = sku_rev.get(k, 0.0) + float(it.get("qty") or 1) * float(it.get("price") or 0)
        for k, _ in sorted(sku_rev.items(), key=lambda kv: kv[1], reverse=True)[:top_products]:
            specs.append(SeriesSpec(business_id=bid, level=SeriesLevel.PRODUCT,
                                    target=TargetKind.UNITS, key=k, label=k))
        return specs


def _iter_items(items: Any):
    if isinstance(items, list):
        for it in items:
            if isinstance(it, dict):
                yield it


def _sum_units(items: Any) -> float:
    return float(sum(float(it.get("qty") or it.get("quantity") or 1) for it in _iter_items(items))) or 0.0
