"""ForecastingService — orchestrates data load, pipeline, persistence, accuracy."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

import numpy as np
import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.forecasting import metrics as M
from app.domains.forecasting import reconciliation as R
from app.domains.forecasting.data import DemandDataLoader
from app.domains.forecasting.models_db import (
    ForecastAccuracy,
    ForecastPoint,
    ForecastRun,
    ForecastSeries,
    RunStatus,
)
from app.domains.forecasting.pipeline import ForecastPipeline
from app.domains.forecasting.types import Grain, SeriesLevel, SeriesSpec, TargetKind

logger = get_logger(__name__)

DEFAULT_HORIZON = 28
_HBUCKETS = [("1-7", 1, 7), ("8-14", 8, 14), ("15-28", 15, 28), ("29+", 29, 10_000)]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _spec_from_row(row: ForecastSeries) -> SeriesSpec:
    return SeriesSpec(
        business_id=str(row.business_id),
        level=SeriesLevel(row.level),
        target=TargetKind(row.target),
        grain=Grain(row.grain),
        key=row.key,
        label=row.label,
        country=row.country or "AR",
    )


class ForecastingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.loader = DemandDataLoader(db)

    # ------------------------------------------------------------------
    async def sync_series(self, business_id: uuid.UUID) -> dict[str, int]:
        specs = await self.loader.discover_series(business_id)
        existing = {
            r.series_key: r
            for r in (
                await self.db.execute(
                    select(ForecastSeries).where(ForecastSeries.business_id == business_id)
                )
            ).scalars().all()
        }
        created = 0
        for spec in specs:
            if spec.series_key in existing:
                continue
            self.db.add(
                ForecastSeries(
                    business_id=business_id,
                    series_key=spec.series_key,
                    level=spec.level.value,
                    target=spec.target.value,
                    grain=spec.grain.value,
                    key=spec.key,
                    label=spec.label,
                    country=spec.country,
                )
            )
            created += 1
        await self.db.commit()
        return {"discovered": len(specs), "created": created, "total": len(existing) + created}

    async def list_series(self, business_id: uuid.UUID, active_only: bool = True) -> list[ForecastSeries]:
        q = select(ForecastSeries).where(ForecastSeries.business_id == business_id)
        if active_only:
            q = q.where(ForecastSeries.is_active.is_(True))
        q = q.order_by(ForecastSeries.level, ForecastSeries.label)
        return list((await self.db.execute(q)).scalars().all())

    # ------------------------------------------------------------------
    async def run_series(
        self,
        business_id: uuid.UUID,
        series_row: ForecastSeries,
        *,
        horizon: int = DEFAULT_HORIZON,
        persist: bool = True,
    ) -> dict[str, Any]:
        spec = _spec_from_row(series_row)
        ts = await self.loader.load(spec, lookback_days=540)
        if ts is None or ts.n < 28:
            if persist:
                series_row.last_run_at = _utcnow()
                await self.db.commit()
            return {"status": RunStatus.SKIPPED.value, "reason": "serie con datos insuficientes"}

        try:
            out = ForecastPipeline(horizon=horizon, profile=self.profile).run(ts)
        except Exception as e:  # noqa: BLE001
            logger.exception("forecast pipeline failed for %s", spec.series_key)
            if persist:
                run = ForecastRun(
                    series_id=series_row.id, business_id=business_id,
                    origin_date=ts.index[-1].date(), horizon=horizon,
                    grain=spec.grain.value, status=RunStatus.FAILED.value, error=str(e)[:2000],
                    n_history=ts.n,
                )
                self.db.add(run)
                series_row.last_run_at = _utcnow()
                await self.db.commit()
            return {"status": RunStatus.FAILED.value, "error": str(e)}

        fc = out.forecast
        bt = out.backtest.summary()
        chosen = list(out.backtest.weights)
        best = min(bt.values(), key=lambda v: v["mase"]) if bt else {}

        result: dict[str, Any] = {
            "status": RunStatus.OK.value,
            "series_key": spec.series_key,
            "origin_date": ts.index[-1].date().isoformat(),
            "horizon": horizon,
            "weights": out.backtest.weights,
            "backtest": bt,
            "intermittent": out.intermittent,
            "mean": fc.mean.tolist(),
            "index": [d.date().isoformat() for d in fc.index],
            "quantiles": {str(q): fc.quantiles[q].tolist() for q in fc.quantiles},
        }

        if persist:
            run = ForecastRun(
                series_id=series_row.id,
                business_id=business_id,
                origin_date=ts.index[-1].date(),
                horizon=horizon,
                grain=spec.grain.value,
                status=RunStatus.OK.value,
                model_weights=out.backtest.weights,
                chosen_models=chosen,
                backtest_summary=bt,
                n_history=ts.n,
                wape_backtest=_num(best.get("wape")),
                mase_backtest=_num(best.get("mase")),
                pinball_backtest=_num(best.get("pinball")),
                coverage_backtest=_num(best.get("coverage")),
                total_forecast=Decimal(str(round(float(np.sum(fc.mean)), 2))),
            )
            self.db.add(run)
            await self.db.flush()
            self._persist_points(run, series_row, business_id, fc)

            series_row.last_run_at = _utcnow()
            series_row.intermittent = out.intermittent
            series_row.adi = _num(out.adi)
            series_row.zero_share = _num(out.zero_share)
            series_row.last_wape = _num(best.get("wape"))
            series_row.last_mase = _num(best.get("mase"))
            await self.db.commit()
            result["run_id"] = str(run.id)

        return result

    def _persist_points(self, run, series_row, business_id, fc) -> None:
        for i, ts in enumerate(fc.index):
            q = {str(k): float(v[i]) for k, v in fc.quantiles.items()}
            self.db.add(
                ForecastPoint(
                    run_id=run.id,
                    series_id=series_row.id,
                    business_id=business_id,
                    target_date=ts.date(),
                    horizon_step=i + 1,
                    yhat=Decimal(str(round(float(fc.mean[i]), 4))),
                    q10=_num(q.get("0.1")),
                    q50=_num(q.get("0.5")),
                    q90=_num(q.get("0.9")),
                    quantiles=q,
                )
            )

    # ------------------------------------------------------------------
    async def run_all(
        self, business_id: uuid.UUID, *, horizon: int = DEFAULT_HORIZON, reconcile: bool = True
    ) -> dict[str, Any]:
        await self.sync_series(business_id)
        rows = await self.list_series(business_id)

        order = {"total": 0, "category": 1, "channel": 2, "product": 3}
        rows.sort(key=lambda r: order.get(r.level, 9))

        results = []
        for row in rows:
            try:
                res = await self.run_series(business_id, row, horizon=horizon)
            except Exception as e:  # noqa: BLE001
                res = {"status": "failed", "error": str(e), "series_key": row.series_key}
            results.append(res)

        recon_info = None
        if reconcile:
            recon_info = await self._reconcile_revenue_hierarchy(business_id, horizon)

        ok = sum(1 for r in results if r.get("status") == "ok")
        return {
            "series_run": len(results),
            "ok": ok,
            "skipped": sum(1 for r in results if r.get("status") == "skipped"),
            "failed": sum(1 for r in results if r.get("status") == "failed"),
            "reconciliation": recon_info,
        }

    async def _reconcile_revenue_hierarchy(
        self, business_id: uuid.UUID, horizon: int
    ) -> Optional[dict]:
        total_row = await self._find_series(business_id, level="total", target="revenue")
        channel_rows = await self._find_series_many(business_id, level="channel", target="revenue")
        if not channel_rows:
            return None

        total_run, total_path = await self._latest_path(total_row) if total_row else (None, None)
        child = []
        child_wapes = []
        for cr in channel_rows:
            run, path = await self._latest_path(cr)
            if path is None:
                continue
            child.append((cr, run, path))
            child_wapes.append(float(cr.last_wape) if cr.last_wape is not None else np.nan)
        if not child:
            return None

        paths = [c[2] for c in child]
        new_total, new_children = R.reconcile(
            total_path, paths,
            total_wape=float(total_row.last_wape) if total_row and total_row.last_wape else None,
            child_wapes=child_wapes,
        )

        # write reconciled means back onto the latest points
        for (cr, run, _), newp in zip(child, new_children):
            await self._overwrite_point_means(run, newp)
            if run:
                run.reconciled = True
        if total_row and total_run is not None:
            await self._overwrite_point_means(total_run, new_total)
            total_run.reconciled = True
        await self.db.commit()
        return {
            "channels": len(child),
            "total_before": float(np.sum(total_path)) if total_path is not None else None,
            "total_after": float(np.sum(new_total)),
        }

    async def _overwrite_point_means(self, run: ForecastRun, path: np.ndarray) -> None:
        if run is None:
            return
        pts = (
            await self.db.execute(
                select(ForecastPoint).where(ForecastPoint.run_id == run.id)
                .order_by(ForecastPoint.horizon_step)
            )
        ).scalars().all()
        for p, v in zip(pts, path):
            old = float(p.yhat) or 1.0
            scale = float(v) / old if old else 1.0
            p.yhat = Decimal(str(round(float(v), 4)))
            if p.q10 is not None:
                p.q10 = Decimal(str(round(float(p.q10) * scale, 4)))
            if p.q90 is not None:
                p.q90 = Decimal(str(round(float(p.q90) * scale, 4)))
            p.q50 = Decimal(str(round(float(v), 4)))

    # ------------------------------------------------------------------
    async def _find_series(self, business_id, level, target) -> Optional[ForecastSeries]:
        rows = await self._find_series_many(business_id, level, target)
        return rows[0] if rows else None

    async def _find_series_many(self, business_id, level, target) -> list[ForecastSeries]:
        return list(
            (
                await self.db.execute(
                    select(ForecastSeries).where(
                        ForecastSeries.business_id == business_id,
                        ForecastSeries.level == level,
                        ForecastSeries.target == target,
                        ForecastSeries.is_active.is_(True),
                    )
                )
            ).scalars().all()
        )

    async def _latest_run(self, series_row: ForecastSeries) -> Optional[ForecastRun]:
        if series_row is None:
            return None
        return (
            await self.db.execute(
                select(ForecastRun)
                .where(ForecastRun.series_id == series_row.id, ForecastRun.status == RunStatus.OK.value)
                .order_by(ForecastRun.run_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def _latest_path(self, series_row) -> tuple[Optional[ForecastRun], Optional[np.ndarray]]:
        run = await self._latest_run(series_row)
        if not run:
            return None, None
        pts = (
            await self.db.execute(
                select(ForecastPoint).where(ForecastPoint.run_id == run.id)
                .order_by(ForecastPoint.horizon_step)
            )
        ).scalars().all()
        if not pts:
            return run, None
        return run, np.array([float(p.yhat) for p in pts])

    # ------------------------------------------------------------------
    async def get_forecast(
        self, business_id: uuid.UUID, series_key: str, horizon: Optional[int] = None
    ) -> Optional[dict]:
        row = (
            await self.db.execute(
                select(ForecastSeries).where(
                    ForecastSeries.business_id == business_id,
                    ForecastSeries.series_key == series_key,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return None
        run = await self._latest_run(row)
        if not run:
            return {"series_key": series_key, "status": "no_forecast"}
        pts = (
            await self.db.execute(
                select(ForecastPoint).where(ForecastPoint.run_id == run.id)
                .order_by(ForecastPoint.horizon_step)
            )
        ).scalars().all()
        if horizon:
            pts = pts[:horizon]
        return {
            "series_key": series_key,
            "label": row.label,
            "level": row.level,
            "target": row.target,
            "origin_date": run.origin_date.isoformat(),
            "run_at": run.run_at.isoformat(),
            "model_weights": run.model_weights,
            "backtest": run.backtest_summary,
            "reconciled": run.reconciled,
            "points": [
                {
                    "date": p.target_date.isoformat(),
                    "step": p.horizon_step,
                    "yhat": float(p.yhat),
                    "q10": float(p.q10) if p.q10 is not None else None,
                    "q50": float(p.q50) if p.q50 is not None else None,
                    "q90": float(p.q90) if p.q90 is not None else None,
                }
                for p in pts
            ],
        }

    # ------------------------------------------------------------------
    async def evaluate_accuracy(self, business_id: uuid.UUID, lookback_days: int = 45) -> dict[str, Any]:
        rows = await self.list_series(business_id)
        cutoff = date.today() - timedelta(days=1)
        written = 0
        for row in rows:
            run = (
                await self.db.execute(
                    select(ForecastRun).where(
                        ForecastRun.series_id == row.id,
                        ForecastRun.status == RunStatus.OK.value,
                        ForecastRun.origin_date <= cutoff - timedelta(days=7),
                        ForecastRun.origin_date >= cutoff - timedelta(days=lookback_days),
                    ).order_by(ForecastRun.run_at.desc()).limit(1)
                )
            ).scalar_one_or_none()
            if not run:
                continue
            pts = (
                await self.db.execute(
                    select(ForecastPoint).where(
                        ForecastPoint.run_id == run.id,
                        ForecastPoint.target_date <= cutoff,
                    ).order_by(ForecastPoint.horizon_step)
                )
            ).scalars().all()
            if len(pts) < 4:
                continue

            spec = _spec_from_row(row)
            ts = await self.loader.load(spec, lookback_days=lookback_days + 30, end=_utcnow())
            if ts is None:
                continue
            actual_by_date = {d.date(): float(v) for d, v in zip(ts.index, ts.values)}
            train_tail = ts.values

            for label, lo, hi in _HBUCKETS:
                bucket = [p for p in pts if lo <= p.horizon_step <= hi and p.target_date in actual_by_date]
                if len(bucket) < 3:
                    continue
                yt = np.array([actual_by_date[p.target_date] for p in bucket])
                yp = np.array([float(p.yhat) for p in bucket])
                q = {
                    0.1: np.array([float(p.q10) if p.q10 is not None else np.nan for p in bucket]),
                    0.9: np.array([float(p.q90) if p.q90 is not None else np.nan for p in bucket]),
                }
                mt = M.all_metrics(yt, yp, train_tail, season=ts.seasonal_period, quantile_preds=q)
                self.db.add(
                    ForecastAccuracy(
                        series_id=row.id, business_id=business_id, run_id=run.id,
                        window_start=min(p.target_date for p in bucket),
                        window_end=max(p.target_date for p in bucket),
                        horizon_bucket=label, n=len(bucket),
                        wape=_num(mt["wape"]), mape=_num(mt["mape"]), mase=_num(mt["mase"]),
                        bias=_num(mt["bias"]), rmse=_num(mt["rmse"]), coverage=_num(mt["coverage"]),
                    )
                )
                written += 1
        await self.db.commit()
        return {"series": len(rows), "accuracy_rows": written}

    # ------------------------------------------------------------------
    async def dashboard(self, business_id: uuid.UUID) -> dict[str, Any]:
        rows = await self.list_series(business_id)
        total_row = await self._find_series(business_id, "total", "revenue")
        total_run = await self._latest_run(total_row) if total_row else None

        next30 = None
        if total_run:
            pts = (
                await self.db.execute(
                    select(ForecastPoint).where(ForecastPoint.run_id == total_run.id)
                    .order_by(ForecastPoint.horizon_step).limit(30)
                )
            ).scalars().all()
            next30 = {
                "sum_mean": float(sum(float(p.yhat) for p in pts)),
                "sum_q10": float(sum(float(p.q10 or 0) for p in pts)),
                "sum_q90": float(sum(float(p.q90 or 0) for p in pts)),
            }

        acc = (
            await self.db.execute(
                select(ForecastAccuracy)
                .where(ForecastAccuracy.business_id == business_id)
                .order_by(ForecastAccuracy.evaluated_at.desc())
                .limit(50)
            )
        ).scalars().all()

        return {
            "business_id": str(business_id),
            "series_count": len(rows),
            "revenue_forecast_30d": next30,
            "series": [
                {
                    "series_key": r.series_key,
                    "label": r.label,
                    "level": r.level,
                    "target": r.target,
                    "intermittent": r.intermittent,
                    "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
                    "backtest_wape": float(r.last_wape) if r.last_wape is not None else None,
                    "backtest_mase": float(r.last_mase) if r.last_mase is not None else None,
                }
                for r in rows
            ],
            "accuracy": [
                {
                    "series_id": str(a.series_id),
                    "bucket": a.horizon_bucket,
                    "wape": float(a.wape) if a.wape is not None else None,
                    "mase": float(a.mase) if a.mase is not None else None,
                    "bias": float(a.bias) if a.bias is not None else None,
                    "coverage": float(a.coverage) if a.coverage is not None else None,
                    "n": a.n,
                    "window_end": a.window_end.isoformat(),
                }
                for a in acc
            ],
        }


def _num(v) -> Optional[Decimal]:
    if v is None:
        return None
    try:
        f = float(v)
        if not np.isfinite(f):
            return None
        return Decimal(str(round(f, 6)))
    except (TypeError, ValueError):
        return None
