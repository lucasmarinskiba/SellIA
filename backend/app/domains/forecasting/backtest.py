"""Rolling-origin (expanding-window) backtesting + ensemble weighting."""

from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from app.domains.forecasting import metrics as M
from app.domains.forecasting.models.base import DEFAULT_QUANTILES, Forecaster
from app.domains.forecasting.types import BacktestReport, FoldMetrics, SeriesSpec, TimeSeries


class RollingOriginBacktester:
    def __init__(
        self,
        horizon: int = 28,
        n_folds: int = 4,
        step: int | None = None,
        min_train: int | None = None,
        quantiles: tuple[float, ...] = DEFAULT_QUANTILES,
        temperature: float = 0.5,
        keep_top: int = 4,
    ):
        self.horizon = horizon
        self.n_folds = n_folds
        self.step = step
        self.min_train = min_train
        self.quantiles = quantiles
        self.temperature = temperature
        self.keep_top = keep_top

    # ------------------------------------------------------------------
    def _slices(self, n: int) -> list[int]:
        h = self.horizon
        min_train = self.min_train or max(2 * (7 if n >= 60 else 1) + h, int(n * 0.4), 30)
        step = self.step or max(1, h // 2)
        cuts = []
        cut = n - h
        while cut >= min_train and len(cuts) < self.n_folds:
            cuts.append(cut)
            cut -= step
        return sorted(cuts)

    def _sub_ts(self, ts: TimeSeries, end: int) -> TimeSeries:
        exog = ts.exog.iloc[:end] if ts.exog is not None else None
        return TimeSeries(spec=ts.spec, index=ts.index[:end], values=ts.values[:end], exog=exog)

    # ------------------------------------------------------------------
    def run(self, ts: TimeSeries, model_pool: list[Forecaster]) -> BacktestReport:
        report = BacktestReport(spec=ts.spec)
        cuts = self._slices(ts.n)
        season = ts.seasonal_period

        for model in model_pool:
            report.per_model.setdefault(model.name, [])

        if not cuts:
            # not enough data to backtest — fall back to equal weights over
            # the cheap statistical models only
            report.weights = {m.name: 1.0 for m in model_pool if m.name in ("seasonal_naive", "theta", "holt_winters")}
            if not report.weights:
                report.weights = {model_pool[0].name: 1.0}
            report.chosen = list(report.weights)
            report.weights = _normalize(report.weights)
            return report

        for fi, cut in enumerate(cuts):
            train = self._sub_ts(ts, cut)
            actual = ts.values[cut:cut + self.horizon]
            fut_index = ts.index[cut:cut + self.horizon]
            fut_exog = ts.exog.iloc[cut:cut + self.horizon] if ts.exog is not None else None

            for proto in model_pool:
                model = copy.deepcopy(proto)
                try:
                    model.fit(train)
                    fr = model.predict(len(actual), fut_index, fut_exog, self.quantiles).clip_nonnegative()
                except Exception:  # noqa: BLE001
                    continue
                mt = M.all_metrics(
                    actual, fr.mean, train.values, season=season,
                    quantile_preds={q: fr.quantiles[q] for q in fr.quantiles},
                )
                report.per_model[model.name].append(
                    FoldMetrics(
                        model_name=model.name, fold=fi, horizon=len(actual),
                        mape=mt["mape"], wape=mt["wape"], rmse=mt["rmse"], mae=mt["mae"],
                        mase=mt["mase"], bias=mt["bias"], pinball=mt["pinball"],
                        coverage=mt["coverage"],
                    )
                )

        report.weights = self._weights(report)
        report.chosen = list(report.weights)
        return report

    # ------------------------------------------------------------------
    def _weights(self, report: BacktestReport) -> dict[str, float]:
        avg = {}
        for name, folds in report.per_model.items():
            if not folds:
                continue
            m = np.array([f.mase for f in folds], dtype=float)
            m = m[np.isfinite(m)]
            if m.size == 0:
                continue
            avg[name] = float(np.mean(m))
        if not avg:
            return {list(report.per_model)[0]: 1.0}

        best = min(avg.values())
        # keep only models within 2x of the best, then top-K
        kept = {k: v for k, v in avg.items() if v <= max(best * 2.0, best + 1e-6)}
        kept = dict(sorted(kept.items(), key=lambda kv: kv[1])[: self.keep_top])

        w = {k: float(np.exp(-(v - best) / max(self.temperature, 1e-3))) for k, v in kept.items()}
        return _normalize(w)


def _normalize(w: dict[str, float]) -> dict[str, float]:
    s = sum(w.values())
    if s <= 0:
        n = len(w) or 1
        return {k: 1.0 / n for k in w}
    return {k: v / s for k, v in w.items()}
