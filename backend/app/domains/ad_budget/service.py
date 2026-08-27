"""AdBudgetService — config, channels, and the reallocation cycle."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.ad_budget.apply import BudgetApplier
from app.domains.ad_budget.models import (
    AdBudgetConfig,
    AdChannel,
    BudgetReallocation,
    ReallocationStatus,
)
from app.domains.ad_budget.optimizer import (
    ChannelInput,
    OptimizerConfig,
    optimize,
)
from app.domains.ad_budget.performance import AdPerformanceService

logger = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AdBudgetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.perf = AdPerformanceService(db)

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    async def get_or_create_config(self, business_id: uuid.UUID) -> AdBudgetConfig:
        res = await self.db.execute(
            select(AdBudgetConfig).where(AdBudgetConfig.business_id == business_id)
        )
        cfg = res.scalar_one_or_none()
        if not cfg:
            cfg = AdBudgetConfig(business_id=business_id)
            self.db.add(cfg)
            await self.db.commit()
            await self.db.refresh(cfg)
        return cfg

    async def update_config(self, business_id: uuid.UUID, **fields: Any) -> AdBudgetConfig:
        cfg = await self.get_or_create_config(business_id)
        for k, v in fields.items():
            if v is not None and hasattr(cfg, k):
                setattr(cfg, k, v)
        await self.db.commit()
        await self.db.refresh(cfg)
        return cfg

    # ------------------------------------------------------------------
    # Channels
    # ------------------------------------------------------------------
    async def list_channels(self, business_id: uuid.UUID) -> list[AdChannel]:
        res = await self.db.execute(
            select(AdChannel).where(AdChannel.business_id == business_id).order_by(AdChannel.platform)
        )
        return list(res.scalars().all())

    async def create_channel(self, business_id: uuid.UUID, **data: Any) -> AdChannel:
        ch = AdChannel(business_id=business_id, **data)
        self.db.add(ch)
        await self.db.commit()
        await self.db.refresh(ch)
        return ch

    async def update_channel(self, business_id: uuid.UUID, channel_id: uuid.UUID, **fields: Any) -> AdChannel:
        ch = await self._get_channel(business_id, channel_id)
        for k, v in fields.items():
            if v is not None and hasattr(ch, k):
                setattr(ch, k, v)
        await self.db.commit()
        await self.db.refresh(ch)
        return ch

    async def delete_channel(self, business_id: uuid.UUID, channel_id: uuid.UUID) -> None:
        ch = await self._get_channel(business_id, channel_id)
        await self.db.delete(ch)
        await self.db.commit()

    async def _get_channel(self, business_id: uuid.UUID, channel_id: uuid.UUID) -> AdChannel:
        res = await self.db.execute(
            select(AdChannel).where(
                AdChannel.id == channel_id, AdChannel.business_id == business_id
            )
        )
        ch = res.scalar_one_or_none()
        if not ch:
            raise ValueError("ad channel not found")
        return ch

    # ------------------------------------------------------------------
    # Cycle
    # ------------------------------------------------------------------
    def _optimizer_config(self, cfg: AdBudgetConfig) -> OptimizerConfig:
        return OptimizerConfig(
            total_daily_budget=cfg.total_daily_budget,
            target_roas=cfg.target_roas,
            kill_roas=cfg.kill_roas,
            min_channel_share=cfg.min_channel_share,
            max_daily_shift_pct=cfg.max_daily_shift_pct,
            aggressiveness=cfg.aggressiveness,
            allow_pause=cfg.allow_pause,
            min_data_conversions=cfg.min_data_conversions,
        )

    async def run_cycle(
        self, business_id: uuid.UUID, *, force: bool = False, auto_apply: Optional[bool] = None
    ) -> dict[str, Any]:
        cfg = await self.get_or_create_config(business_id)
        if not force and (not cfg.is_active or cfg.is_paused):
            return {"status": "skipped", "reason": "autopilot inactivo o pausado"}

        channels = await self.list_channels(business_id)
        if not channels:
            return {"status": "skipped", "reason": "sin canales configurados"}

        inputs: list[ChannelInput] = []
        for ch in channels:
            metrics = await self.perf.gather(business_id, ch, cfg.optimization_window_days)
            await self.perf.snapshot(business_id, ch, metrics)
            await self.perf.reconcile_spend_to_ledger(business_id, ch, metrics)
            inputs.append(
                ChannelInput(
                    channel_id=str(ch.id),
                    platform=ch.platform,
                    name=ch.display_name,
                    current_budget=ch.current_daily_budget or Decimal("0"),
                    spend=metrics["spend"],
                    revenue=metrics["revenue"],
                    conversions=metrics["conversions"],
                    roas=metrics["roas"],
                    recent_roas=metrics["recent_roas"],
                    min_budget=ch.min_daily_budget,
                    max_budget=ch.max_daily_budget,
                    is_managed=ch.is_managed,
                    is_paused=ch.is_paused,
                )
            )

        result = optimize(inputs, self._optimizer_config(cfg))

        realloc = BudgetReallocation(
            business_id=business_id,
            run_id=uuid.uuid4(),
            status=ReallocationStatus.NOOP.value if result.noop else ReallocationStatus.RECOMMENDED.value,
            blended_roas=result.blended_roas,
            total_budget_before=result.total_before,
            total_budget_after=result.total_after,
            decisions=result.as_dicts(),
            window_days=cfg.optimization_window_days,
            notes=result.note or None,
        )
        self.db.add(realloc)
        await self.db.flush()

        cfg.last_run_at = _utcnow()
        should_apply = (not cfg.requires_approval) if auto_apply is None else auto_apply
        applied = False
        if should_apply and not result.noop:
            await self._apply(business_id, realloc, applied_by=None)
            applied = True
        cfg.last_status = realloc.status
        await self.db.commit()
        await self.db.refresh(realloc)

        return {
            "status": "ok",
            "reallocation_id": str(realloc.id),
            "applied": applied,
            "decisions": realloc.decisions,
            "blended_roas": float(result.blended_roas),
            "total_before": float(result.total_before),
            "total_after": float(result.total_after),
        }

    async def apply_reallocation(
        self, business_id: uuid.UUID, realloc_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> BudgetReallocation:
        res = await self.db.execute(
            select(BudgetReallocation).where(
                BudgetReallocation.id == realloc_id,
                BudgetReallocation.business_id == business_id,
            )
        )
        realloc = res.scalar_one_or_none()
        if not realloc:
            raise ValueError("reallocation not found")
        if realloc.status in (ReallocationStatus.APPLIED.value, ReallocationStatus.REJECTED.value):
            raise ValueError(f"reallocation already {realloc.status}")
        await self._apply(business_id, realloc, applied_by=user_id)
        await self.db.commit()
        await self.db.refresh(realloc)
        return realloc

    async def reject_reallocation(
        self, business_id: uuid.UUID, realloc_id: uuid.UUID
    ) -> BudgetReallocation:
        res = await self.db.execute(
            select(BudgetReallocation).where(
                BudgetReallocation.id == realloc_id,
                BudgetReallocation.business_id == business_id,
            )
        )
        realloc = res.scalar_one_or_none()
        if not realloc:
            raise ValueError("reallocation not found")
        realloc.status = ReallocationStatus.REJECTED.value
        await self.db.commit()
        await self.db.refresh(realloc)
        return realloc

    async def _apply(
        self, business_id: uuid.UUID, realloc: BudgetReallocation, applied_by: Optional[uuid.UUID]
    ) -> None:
        applier = BudgetApplier(self.db)
        channels = {str(c.id): c for c in await self.list_channels(business_id)}
        updated_decisions = []
        any_ok = False
        any_fail = False
        for d in realloc.decisions:
            d = dict(d)
            action = d.get("action")
            ch = channels.get(d.get("ad_channel_id"))
            if not ch or action == "hold":
                d.setdefault("applied", None)
                updated_decisions.append(d)
                continue
            try:
                res = await applier.apply(
                    business_id, ch, Decimal(str(d["after"])), pause=(action == "pause")
                )
                d["applied"] = bool(res.get("applied"))
                d["apply_message"] = res.get("message")
                d["manual_required"] = bool(res.get("manual_required"))
                any_ok = any_ok or d["applied"]
                any_fail = any_fail or (not d["applied"])
            except Exception as e:  # noqa: BLE001
                d["applied"] = False
                d["apply_message"] = str(e)
                any_fail = True
            updated_decisions.append(d)

        realloc.decisions = updated_decisions
        realloc.applied_at = _utcnow()
        realloc.applied_by = applied_by
        if any_ok and any_fail:
            realloc.status = ReallocationStatus.PARTIALLY_APPLIED.value
        elif any_ok:
            realloc.status = ReallocationStatus.APPLIED.value
        else:
            realloc.status = ReallocationStatus.FAILED.value
        await self.db.flush()

    # ------------------------------------------------------------------
    # Dashboard / history
    # ------------------------------------------------------------------
    async def dashboard(self, business_id: uuid.UUID) -> dict[str, Any]:
        cfg = await self.get_or_create_config(business_id)
        channels = await self.list_channels(business_id)
        rows = []
        total_spend = Decimal("0")
        total_rev = Decimal("0")
        total_budget = Decimal("0")
        for ch in channels:
            snap = await self.perf.latest_snapshot(ch.id)
            spend = snap.spend if snap else Decimal("0")
            rev = snap.revenue if snap else Decimal("0")
            total_spend += spend
            total_rev += rev
            total_budget += ch.current_daily_budget or Decimal("0")
            rows.append({
                "id": str(ch.id),
                "platform": ch.platform,
                "name": ch.display_name,
                "daily_budget": float(ch.current_daily_budget or 0),
                "is_managed": ch.is_managed,
                "is_paused": ch.is_paused,
                "roas": float(snap.roas) if snap else None,
                "spend": float(spend),
                "revenue": float(rev),
                "conversions": snap.conversions if snap else 0,
                "captured_at": snap.captured_at.isoformat() if snap else None,
            })

        last = await self.db.execute(
            select(BudgetReallocation)
            .where(BudgetReallocation.business_id == business_id)
            .order_by(BudgetReallocation.created_at.desc())
            .limit(1)
        )
        last_realloc = last.scalar_one_or_none()

        return {
            "business_id": str(business_id),
            "is_active": cfg.is_active,
            "is_paused": cfg.is_paused,
            "requires_approval": cfg.requires_approval,
            "target_roas": float(cfg.target_roas),
            "total_daily_budget": float(cfg.total_daily_budget) if cfg.total_daily_budget else float(total_budget),
            "blended_roas": float((total_rev / total_spend).quantize(Decimal("0.0001"))) if total_spend > 0 else 0.0,
            "window_days": cfg.optimization_window_days,
            "last_run_at": cfg.last_run_at.isoformat() if cfg.last_run_at else None,
            "channels": rows,
            "pending_reallocation": (
                {
                    "id": str(last_realloc.id),
                    "status": last_realloc.status,
                    "created_at": last_realloc.created_at.isoformat(),
                    "decisions": last_realloc.decisions,
                }
                if last_realloc and last_realloc.status == ReallocationStatus.RECOMMENDED.value
                else None
            ),
        }

    async def history(self, business_id: uuid.UUID, limit: int = 50) -> list[BudgetReallocation]:
        res = await self.db.execute(
            select(BudgetReallocation)
            .where(BudgetReallocation.business_id == business_id)
            .order_by(BudgetReallocation.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())
