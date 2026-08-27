"""Pure-numpy statistical forecasters — always available."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.domains.forecasting.models.base import DEFAULT_QUANTILES, Forecaster
from app.domains.forecasting.types import ForecastResult, TimeSeries


# ---------------------------------------------------------------------------
class SeasonalNaiveForecaster(Forecaster):
    name = "seasonal_naive"

    def fit(self, ts: TimeSeries) -> "SeasonalNaiveForecaster":
        self.y = ts.values.astype(float)
        self.m = ts.seasonal_period if ts.n > 2 * ts.seasonal_period else 1
        if len(self.y) > self.m:
            resid = self.y[self.m:] - self.y[:-self.m]
        else:
            resid = np.diff(self.y) if len(self.y) > 1 else np.array([0.0])
        self.sigma = self._residual_sigma(resid)
        return self

    def predict(self, horizon, future_index, future_exog=None, quantiles=DEFAULT_QUANTILES):
        m = self.m
        tail = self.y[-m:] if len(self.y) >= m else np.full(m, self.y.mean())
        mean = np.array([tail[i % m] for i in range(horizon)], dtype=float)
        mean = np.clip(mean, 0.0, None)
        return ForecastResult(
            self.name, horizon, future_index, mean,
            self._normal_quantiles(mean, self.sigma, quantiles),
        )


# ---------------------------------------------------------------------------
class HoltWintersForecaster(Forecaster):
    """Additive Holt-Winters with an optional damped trend; parameters chosen
    by a coarse grid search minimising one-step in-sample SSE."""

    name = "holt_winters"

    def __init__(self, damped: bool = True):
        self.damped = damped

    def fit(self, ts: TimeSeries) -> "HoltWintersForecaster":
        self.y = ts.values.astype(float)
        self.m = ts.seasonal_period if ts.n >= 2 * ts.seasonal_period + 2 else 1
        best = None
        grid_a = (0.05, 0.15, 0.3, 0.5, 0.8)
        grid_b = (0.0, 0.02, 0.1, 0.3)
        grid_g = (0.0, 0.05, 0.2, 0.5) if self.m > 1 else (0.0,)
        grid_phi = (0.85, 0.95, 1.0) if self.damped else (1.0,)
        for a in grid_a:
            for b in grid_b:
                for g in grid_g:
                    for phi in grid_phi:
                        sse, state = self._run(a, b, g, phi)
                        if best is None or sse < best[0]:
                            best = (sse, a, b, g, phi, state)
        self.sse, self.a, self.b, self.g, self.phi, self.state = best
        _, self._fitted = self._run(self.a, self.b, self.g, self.phi, return_fitted=True)[1:]
        resid = self.y[-len(self._fitted):] - self._fitted
        self.sigma = self._residual_sigma(resid)
        return self

    def _run(self, a, b, g, phi, return_fitted=False):
        y = self.y
        m = self.m
        n = len(y)
        level = y[:m].mean() if m > 1 else y[0]
        trend = (y[m:2 * m].mean() - y[:m].mean()) / m if (m > 1 and n >= 2 * m) else 0.0
        season = (y[:m] - level).tolist() if m > 1 else [0.0]
        fitted = []
        sse = 0.0
        for t in range(n):
            s_idx = t % m
            s = season[s_idx] if m > 1 else 0.0
            yhat = level + phi * trend + s
            fitted.append(yhat)
            if t >= m:
                sse += (y[t] - yhat) ** 2
            err = y[t] - yhat
            new_level = level + phi * trend + a * err
            new_trend = phi * trend + b * (new_level - level)
            if m > 1:
                season[s_idx] = s + g * err
            level, trend = new_level, new_trend
        state = (level, trend, list(season))
        if return_fitted:
            return sse, state, np.array(fitted[m:]) if n > m else np.array(fitted)
        return sse, state

    def predict(self, horizon, future_index, future_exog=None, quantiles=DEFAULT_QUANTILES):
        level, trend, season = self.state
        m = self.m
        phi = self.phi
        mean = np.empty(horizon)
        damp_sum = 0.0
        for h in range(1, horizon + 1):
            damp_sum += phi ** h
            s = season[(len(self.y) + h - 1) % m] if m > 1 else 0.0
            mean[h - 1] = level + damp_sum * trend + s
        mean = np.clip(mean, 0.0, None)
        return ForecastResult(
            self.name, horizon, future_index, mean,
            self._normal_quantiles(mean, self.sigma, quantiles),
            diagnostics={"alpha": self.a, "beta": self.b, "gamma": self.g, "phi": self.phi},
        )


# ---------------------------------------------------------------------------
class ThetaForecaster(Forecaster):
    """The Theta method (M3 winner): average of a linear-trend extrapolation
    and SES, on the classically deseasonalised series, then reseasonalised."""

    name = "theta"

    def fit(self, ts: TimeSeries) -> "ThetaForecaster":
        y = ts.values.astype(float)
        self.n = len(y)
        self.m = ts.seasonal_period if self.n >= 2 * ts.seasonal_period + 2 else 1

        self.seasonal = np.ones(self.m)
        work = y.copy()
        if self.m > 1 and self._seasonal_strength(y, self.m) > 0.5:
            self.seasonal = self._seasonal_indices(y, self.m)
            work = y / np.tile(self.seasonal, int(np.ceil(self.n / self.m)))[: self.n]
            work = np.where(np.isfinite(work), work, y)

        t = np.arange(self.n, dtype=float)
        A = np.vstack([np.ones(self.n), t]).T
        coef, *_ = np.linalg.lstsq(A, work, rcond=None)
        self.intercept, self.slope = coef

        self.alpha = self._opt_ses_alpha(work)
        self.ses_level = self._ses_level(work, self.alpha)

        fitted_lin = self.intercept + self.slope * t
        fitted = 0.5 * fitted_lin + 0.5 * self._ses_fitted(work, self.alpha)
        if self.m > 1:
            fitted = fitted * np.tile(self.seasonal, int(np.ceil(self.n / self.m)))[: self.n]
        resid = y[self.m:] - fitted[self.m:] if self.n > self.m else y - fitted
        self.sigma = self._residual_sigma(resid)
        return self

    @staticmethod
    def _seasonal_strength(y, m):
        if len(y) < 2 * m:
            return 0.0
        means = np.array([y[i::m].mean() for i in range(m)])
        return float(np.std(means) / (np.mean(np.abs(y)) + 1e-9))

    @staticmethod
    def _seasonal_indices(y, m):
        idx = np.array([y[i::m].mean() for i in range(m)])
        idx = idx / (idx.mean() + 1e-9)
        return np.where(np.isfinite(idx) & (idx > 0), idx, 1.0)

    @staticmethod
    def _ses_fitted(y, alpha):
        out = np.empty(len(y))
        lvl = y[0]
        for i in range(len(y)):
            out[i] = lvl
            lvl = alpha * y[i] + (1 - alpha) * lvl
        return out

    @classmethod
    def _ses_level(cls, y, alpha):
        lvl = y[0]
        for v in y:
            lvl = alpha * v + (1 - alpha) * lvl
        return lvl

    @classmethod
    def _opt_ses_alpha(cls, y):
        best_a, best_sse = 0.2, np.inf
        for a in np.linspace(0.05, 0.95, 19):
            f = cls._ses_fitted(y, a)
            sse = np.sum((y[1:] - f[1:]) ** 2)
            if sse < best_sse:
                best_sse, best_a = sse, a
        return float(best_a)

    def predict(self, horizon, future_index, future_exog=None, quantiles=DEFAULT_QUANTILES):
        h = np.arange(1, horizon + 1)
        lin = self.intercept + self.slope * (self.n - 1 + h)
        # Theta reduces to: SES level + 0.5 * slope * (h - 1 + ...) drift term
        drift = self.slope * (h - 1) * 0.5
        mean = 0.5 * lin + 0.5 * (self.ses_level + drift)
        if self.m > 1:
            season_tail = np.array([self.seasonal[(self.n + i) % self.m] for i in range(horizon)])
            mean = mean * season_tail
        mean = np.clip(mean, 0.0, None)
        return ForecastResult(
            self.name, horizon, future_index, mean,
            self._normal_quantiles(mean, self.sigma, quantiles),
            diagnostics={"alpha": self.alpha, "slope": float(self.slope)},
        )


# ---------------------------------------------------------------------------
class CrostonForecaster(Forecaster):
    """Croston / SBA / TSB for intermittent demand."""

    def __init__(self, variant: str = "sba", alpha: float = 0.1):
        self.variant = variant
        self.alpha = alpha
        self.name = f"croston_{variant}"

    def fit(self, ts: TimeSeries) -> "CrostonForecaster":
        y = ts.values.astype(float)
        self.n = len(y)
        nz_idx = np.flatnonzero(y > 0)
        if nz_idx.size == 0:
            self.rate = 0.0
            self.sigma = 1.0
            return self
        sizes = y[nz_idx]
        intervals = np.diff(np.concatenate([[nz_idx[0] - (nz_idx[0] or 1) + 0], nz_idx]))
        intervals = np.where(intervals <= 0, 1, intervals).astype(float)

        z = sizes[0]
        p = intervals[0] if intervals.size else 1.0
        for i in range(1, sizes.size):
            z = self.alpha * sizes[i] + (1 - self.alpha) * z
            p = self.alpha * intervals[i] + (1 - self.alpha) * p
        p = max(p, 1e-6)
        rate = z / p
        if self.variant == "sba":
            rate *= 1.0 - self.alpha / 2.0
        elif self.variant == "tsb":
            prob = np.mean(y > 0)
            rate = prob * z
        self.rate = float(max(rate, 0.0))
        # residual scale from period-level demand
        self.sigma = self._residual_sigma(y - self.rate)
        return self

    def predict(self, horizon, future_index, future_exog=None, quantiles=DEFAULT_QUANTILES):
        mean = np.full(horizon, self.rate, dtype=float)
        # widen intervals: intermittent demand is highly dispersed
        sigma = max(self.sigma, np.sqrt(max(self.rate, 1e-6)))
        q = self._normal_quantiles(mean, sigma, quantiles, horizon_growth=False)
        for k in q:
            if k <= 0.5:
                q[k] = np.clip(q[k], 0.0, None)
        return ForecastResult(self.name, horizon, future_index, mean, q,
                              diagnostics={"rate": self.rate, "variant": self.variant})
