"""Weighted ensemble of forecasters.

Point forecast = weighted mean of members. Quantiles are combined by
Vincentization (weighted average of the members' quantile functions),
which yields a coherent, non-crossing predictive distribution.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.domains.forecasting.models.base import DEFAULT_QUANTILES, Forecaster
from app.domains.forecasting.types import ForecastResult, TimeSeries


class EnsembleForecaster(Forecaster):
    name = "ensemble"

    def __init__(self, members: list[Forecaster], weights: dict[str, float] | None = None):
        self.members = members
        self.weights = weights or {}

    def fit(self, ts: TimeSeries) -> "EnsembleForecaster":
        self._fitted: list[Forecaster] = []
        for m in self.members:
            try:
                self._fitted.append(m.fit(ts))
            except Exception:  # noqa: BLE001
                continue
        if not self._fitted:
            raise RuntimeError("ensemble: no member fit successfully")
        w = np.array([max(self.weights.get(m.name, 0.0), 0.0) for m in self._fitted], dtype=float)
        if w.sum() <= 0:
            w = np.ones(len(self._fitted))
        self._w = w / w.sum()
        self.active_weights = {m.name: float(wi) for m, wi in zip(self._fitted, self._w)}
        return self

    def predict(self, horizon, future_index, future_exog=None, quantiles=DEFAULT_QUANTILES):
        future_index = pd.DatetimeIndex(future_index)
        results = []
        for m in self._fitted:
            try:
                results.append(m.predict(horizon, future_index, future_exog, quantiles))
            except Exception:  # noqa: BLE001
                results.append(None)

        keep = [(w, r) for w, r in zip(self._w, results) if r is not None]
        if not keep:
            raise RuntimeError("ensemble: all members failed to predict")
        wsum = sum(w for w, _ in keep)
        keep = [(w / wsum, r) for w, r in keep]

        mean = np.zeros(horizon)
        for w, r in keep:
            mean += w * r.mean

        q_out: dict[float, np.ndarray] = {}
        for q in quantiles:
            acc = np.zeros(horizon)
            wtot = 0.0
            for w, r in keep:
                arr = r.quantiles.get(q)
                if arr is None:
                    continue
                acc += w * np.asarray(arr, dtype=float)
                wtot += w
            if wtot > 0:
                q_out[q] = np.clip(acc / wtot, 0.0, None)
        if len(q_out) > 1:
            keys = sorted(q_out)
            stacked = np.sort(np.vstack([q_out[k] for k in keys]), axis=0)
            q_out = {k: stacked[i] for i, k in enumerate(keys)}

        return ForecastResult(
            self.name, horizon, future_index, np.clip(mean, 0.0, None), q_out,
            diagnostics={"weights": self.active_weights,
                         "members": [r.model_name for _, r in keep]},
        )
