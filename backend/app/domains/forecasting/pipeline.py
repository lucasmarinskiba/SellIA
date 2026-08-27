"""End-to-end forecast pipeline for a single series."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.core.logger import get_logger
from app.domains.forecasting.backtest import RollingOriginBacktester
from app.domains.forecasting.models import default_model_pool
from app.domains.forecasting.models.base import DEFAULT_QUANTILES
from app.domains.forecasting.models.ensemble import EnsembleForecaster
from app.domains.forecasting.models.statistical import (
    CrostonForecaster,
    HoltWintersForecaster,
    SeasonalNaiveForecaster,
    ThetaForecaster,
)
from app.domains.forecasting.models.ml import GBMForecaster
from app.domains.forecasting.types import BacktestReport, ForecastResult, TimeSeries

logger = get_logger(__name__)

_CTORS = {
    "seasonal_naive": lambda: SeasonalNaiveForecaster(),
    "theta": lambda: ThetaForecaster(),
    "holt_winters": lambda: HoltWintersForecaster(),
    "gbm": lambda: GBMForecaster(),
    "croston_sba": lambda: CrostonForecaster(variant="sba"),
    "croston_classic": lambda: CrostonForecaster(variant="classic"),
}


def _optional_ctor(name: str):
    try:
        from app.domains.forecasting.models.optional_backends import (
            ETSStatsmodelsForecaster,
            SarimaForecaster,
        )
        return {"ets_sm": ETSStatsmodelsForecaster, "sarima": SarimaForecaster}.get(name)
    except Exception:  # noqa: BLE001
        return None


@dataclass
class PipelineOutput:
    forecast: ForecastResult
    backtest: BacktestReport
    intermittent: bool
    adi: float
    zero_share: float
    horizon: int


def classify_intermittency(y: np.ndarray) -> tuple[bool, float, float]:
    n = len(y)
    nz = int((y > 0).sum())
    zero_share = 1.0 - nz / n if n else 1.0
    adi = n / nz if nz else float("inf")
    cv2 = float(np.var(y[y > 0]) / (np.mean(y[y > 0]) ** 2)) if nz > 1 else 0.0
    intermittent = adi >= 1.32 or zero_share >= 0.45 or (adi >= 1.2 and cv2 >= 0.49)
    return intermittent, float(adi), float(zero_share)


class ForecastPipeline:
    def __init__(
        self,
        horizon: int = 28,
        quantiles: tuple[float, ...] = DEFAULT_QUANTILES,
        n_folds: int = 4,
        profile: str = "full",   # "full" | "fast"
    ):
        self.horizon = horizon
        self.quantiles = tuple(sorted(set(quantiles) | {0.5}))
        self.profile = profile
        self.n_folds = 2 if profile == "fast" else n_folds

    def _future_index(self, ts: TimeSeries) -> pd.DatetimeIndex:
        freq = ts.index.freqstr or ("D" if ts.spec.grain.value == "daily" else "W-MON")
        return pd.date_range(
            start=ts.index[-1] + (ts.index[-1] - ts.index[-2]),
            periods=self.horizon,
            freq=ts.index.freq or freq,
        )

    def _future_exog(self, ts: TimeSeries, future_index: pd.DatetimeIndex) -> pd.DataFrame | None:
        if ts.exog is None or ts.exog.empty:
            return None
        tail = ts.exog.tail(min(28, len(ts.exog)))
        return pd.DataFrame(
            {
                "price": float(tail["price"].replace(0, np.nan).ffill().bfill().iloc[-1]) if "price" in tail else 0.0,
                "promo": float(tail["promo"].mean()) if "promo" in tail else 0.0,
                "ad_spend": float(tail["ad_spend"].mean()) if "ad_spend" in tail else 0.0,
            },
            index=future_index,
        )

    def run(self, ts: TimeSeries) -> PipelineOutput:
        intermittent, adi, zero_share = classify_intermittency(ts.values)
        pool = default_model_pool(intermittent, light_gbm=True)

        bt = RollingOriginBacktester(
            horizon=min(self.horizon, max(7, ts.n // 4)),
            n_folds=self.n_folds,
            quantiles=self.quantiles,
        )
        report = bt.run(ts, pool)

        members = []
        for name in report.weights:
            if self.profile == "fast" and name == "gbm":
                members.append(GBMForecaster(light=True))
                continue
            ctor = _CTORS.get(name)
            if ctor is None:
                opt = _optional_ctor(name)
                ctor = (lambda o=opt: o()) if opt else None
            if ctor:
                try:
                    members.append(ctor())
                except Exception:  # noqa: BLE001
                    continue
        if not members:
            members = [SeasonalNaiveForecaster(), ThetaForecaster()]
            report.weights = {"seasonal_naive": 0.5, "theta": 0.5}

        ensemble = EnsembleForecaster(members, report.weights)
        ensemble.fit(ts)

        future_index = self._future_index(ts)
        forecast = ensemble.predict(
            self.horizon, future_index, self._future_exog(ts, future_index), self.quantiles
        ).clip_nonnegative()
        forecast.diagnostics.setdefault("backtest", report.summary())
        forecast.diagnostics["ensemble_weights"] = report.weights

        return PipelineOutput(
            forecast=forecast,
            backtest=report,
            intermittent=intermittent,
            adi=adi,
            zero_share=zero_share,
            horizon=self.horizon,
        )
