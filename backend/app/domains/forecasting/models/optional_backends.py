"""statsmodels-backed forecasters. Imported defensively by models/__init__."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from app.domains.forecasting.models.base import DEFAULT_QUANTILES, Forecaster
from app.domains.forecasting.types import ForecastResult, TimeSeries

try:
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    _HAS_STATSMODELS = True
except Exception:  # noqa: BLE001
    ETSModel = None
    SARIMAX = None
    _HAS_STATSMODELS = False


class ETSStatsmodelsForecaster(Forecaster):
    name = "ets_sm"

    def fit(self, ts: TimeSeries) -> "ETSStatsmodelsForecaster":
        y = pd.Series(ts.values.astype(float))
        m = ts.seasonal_period if ts.n >= 2 * ts.seasonal_period + 4 else None
        pos = bool((y > 0).all())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ETSModel(
                y,
                error="add",
                trend="add",
                damped_trend=True,
                seasonal="mul" if (m and pos) else ("add" if m else None),
                seasonal_periods=m,
            )
            self.res = model.fit(disp=False)
        self.sigma = self._residual_sigma(np.asarray(self.res.resid))
        return self

    def predict(self, horizon, future_index, future_exog=None, quantiles=DEFAULT_QUANTILES):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fc = self.res.get_forecast(horizon)
            mean = np.clip(np.asarray(fc.predicted_mean, dtype=float), 0.0, None)
            try:
                se = np.asarray(fc.se_mean, dtype=float)
            except Exception:  # noqa: BLE001
                se = np.full(horizon, self.sigma)
        q_out = {}
        for q in quantiles:
            from app.domains.forecasting.models.base import _ppf_approx
            q_out[q] = np.clip(mean + _ppf_approx(q) * se, 0.0, None)
        return ForecastResult(self.name, horizon, future_index, mean, q_out)


class SarimaForecaster(Forecaster):
    name = "sarima"

    def fit(self, ts: TimeSeries) -> "SarimaForecaster":
        y = pd.Series(ts.values.astype(float))
        m = ts.seasonal_period if ts.n >= 2 * ts.seasonal_period + 8 else 0
        candidates = [
            ((1, 1, 1), (0, 0, 0, 0)),
            ((2, 1, 1), (0, 0, 0, 0)),
            ((1, 1, 1), (1, 0, 1, m)) if m else ((1, 1, 2), (0, 0, 0, 0)),
            ((0, 1, 1), (0, 1, 1, m)) if m else ((0, 1, 1), (0, 0, 0, 0)),
        ]
        best = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for order, sorder in candidates:
                try:
                    res = SARIMAX(
                        y, order=order, seasonal_order=sorder,
                        enforce_stationarity=False, enforce_invertibility=False,
                    ).fit(disp=False)
                    if best is None or res.aic < best.aic:
                        best = res
                except Exception:  # noqa: BLE001
                    continue
        if best is None:
            raise RuntimeError("SARIMA failed to fit any candidate")
        self.res = best
        self.sigma = self._residual_sigma(np.asarray(self.res.resid))
        return self

    def predict(self, horizon, future_index, future_exog=None, quantiles=DEFAULT_QUANTILES):
        from app.domains.forecasting.models.base import _ppf_approx

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fc = self.res.get_forecast(horizon)
            mean = np.clip(np.asarray(fc.predicted_mean, dtype=float), 0.0, None)
            se = np.asarray(fc.se_mean, dtype=float)
        q_out = {q: np.clip(mean + _ppf_approx(q) * se, 0.0, None) for q in quantiles}
        return ForecastResult(self.name, horizon, future_index, mean, q_out)
