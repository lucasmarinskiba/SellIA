"""Gradient-boosted ML forecaster — direct multi-horizon.

One model learns y[t+h] from the demand summary as of day t plus the
target day's calendar / price / ad-spend and the horizon step h itself.
Prediction is a single batched call over h = 1..H — no recursion.

LightGBM is used when importable (native quantile objective); otherwise
scikit-learn's HistGradientBoostingRegressor. The point model uses a
Poisson objective for non-negative targets.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.domains.forecasting.features import build_supervised, origin_matrix
from app.domains.forecasting.models.base import DEFAULT_QUANTILES, Forecaster
from app.domains.forecasting.types import ForecastResult, TimeSeries

try:
    import lightgbm as lgb
    _HAS_LGB = True
except Exception:  # noqa: BLE001
    lgb = None
    _HAS_LGB = False

from sklearn.ensemble import HistGradientBoostingRegressor

MIN_TRAIN_ROWS = 120
_QLEVELS = (0.1, 0.5, 0.9)


class GBMForecaster(Forecaster):
    name = "gbm"
    supports_exog = True

    def __init__(self, max_horizon: int = 45, light: bool = False):
        self.max_horizon = max_horizon
        self.light = light   # backtest mode: skip quantile sub-models, fewer iters

    # ------------------------------------------------------------------
    def fit(self, ts: TimeSeries) -> "GBMForecaster":
        self.country = ts.spec.country
        self.grain = ts.spec.grain.value
        self.history = ts.values.astype(float)
        self.index = pd.DatetimeIndex(ts.index)
        self.exog_hist = ts.exog
        H = min(self.max_horizon, max(7, ts.n // 3))
        self.fit_horizon = H

        X, y, cols = build_supervised(
            self.history, self.index, H, self.country, self.grain, self.exog_hist
        )
        self.columns = cols
        self.trained = len(X) >= MIN_TRAIN_ROWS
        if not self.trained:
            self.level = float(np.mean(self.history[-14:])) if len(self.history) else 0.0
            self.sigma = self._residual_sigma(
                np.diff(self.history) if len(self.history) > 1 else np.array([0.0])
            )
            return self

        nonneg = bool((y >= 0).all())
        self.point = self._point_model(nonneg).fit(X.values, y.values)
        resid = y.values - np.clip(self.point.predict(X.values), 0, None)
        self.sigma = self._residual_sigma(resid)

        self.qmodels: dict[float, object] = {}
        if not self.light:
            for q in _QLEVELS:
                try:
                    self.qmodels[q] = self._quantile_model(q).fit(X.values, y.values)
                except Exception:  # noqa: BLE001
                    self.qmodels[q] = None
        return self

    def _point_model(self, nonneg: bool):
        if _HAS_LGB:
            return lgb.LGBMRegressor(
                objective="poisson" if nonneg else "regression",
                n_estimators=300, learning_rate=0.04, num_leaves=31,
                subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                min_child_samples=20, reg_lambda=1.0, n_jobs=1, verbose=-1,
            )
        return HistGradientBoostingRegressor(
            loss="poisson" if nonneg else "squared_error",
            learning_rate=0.06, max_iter=140 if self.light else 250, max_leaf_nodes=31,
            min_samples_leaf=20, l2_regularization=1.0, early_stopping=False,
        )

    def _quantile_model(self, q: float):
        if _HAS_LGB:
            return lgb.LGBMRegressor(
                objective="quantile", alpha=q, n_estimators=250,
                learning_rate=0.05, num_leaves=31, subsample=0.8, subsample_freq=1,
                colsample_bytree=0.8, min_child_samples=25, n_jobs=1, verbose=-1,
            )
        return HistGradientBoostingRegressor(
            loss="quantile", quantile=q, learning_rate=0.06, max_iter=200,
            max_leaf_nodes=31, min_samples_leaf=25, early_stopping=False,
        )

    # ------------------------------------------------------------------
    def predict(self, horizon, future_index, future_exog=None, quantiles=DEFAULT_QUANTILES):
        future_index = pd.DatetimeIndex(future_index)
        if not self.trained:
            mean = np.full(horizon, max(self.level, 0.0))
            return ForecastResult(
                self.name, horizon, future_index, mean,
                self._normal_quantiles(mean, self.sigma, quantiles),
                diagnostics={"trained": False},
            )

        X, gen_index = origin_matrix(
            self.history, self.index, horizon, self.columns,
            self.country, self.grain, future_exog,
        )
        mean = np.clip(self.point.predict(X.values), 0.0, None)

        raw_q: dict[float, np.ndarray] = {}
        for q, model in self.qmodels.items():
            if model is None:
                continue
            raw_q[q] = np.clip(model.predict(X.values), 0.0, None)

        q_out: dict[float, np.ndarray] = {}
        for q in quantiles:
            if q in raw_q:
                q_out[q] = raw_q[q]
            elif len(raw_q) >= 2:
                q_out[q] = self._interp_quantile(q, raw_q, mean)
            else:
                q_out[q] = self._normal_quantiles(mean, self.sigma, (q,))[q]

        if len(q_out) > 1:
            keys = sorted(q_out)
            stacked = np.sort(np.vstack([q_out[k] for k in keys]), axis=0)
            q_out = {k: stacked[i] for i, k in enumerate(keys)}

        return ForecastResult(
            self.name, horizon, future_index, mean, q_out,
            diagnostics={"trained": True, "backend": "lightgbm" if _HAS_LGB else "sklearn",
                         "n_features": len(self.columns)},
        )

    @staticmethod
    def _interp_quantile(q, raw_q, mean):
        ks = np.array(sorted(raw_q))
        vals = np.vstack([raw_q[k] for k in ks])  # (nq, h)
        out = np.empty(vals.shape[1])
        for j in range(vals.shape[1]):
            out[j] = np.interp(q, ks, vals[:, j])
        return np.clip(out, 0.0, None)
