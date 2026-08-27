"""Forecaster interface + shared helpers."""

from __future__ import annotations

import abc

import numpy as np
import pandas as pd

from app.domains.forecasting.types import ForecastResult, TimeSeries

DEFAULT_QUANTILES = (0.1, 0.25, 0.5, 0.75, 0.9)


class Forecaster(abc.ABC):
    """Stateless-ish: `fit` returns self, `predict` produces an H-step forecast.

    Implementations must be cheap to construct; heavy work happens in `fit`.
    `predict` must always return non-negative means and a full set of the
    requested quantiles (fall back to a normal approx around the mean if the
    model has no native quantiles).
    """

    name: str = "base"
    supports_exog: bool = False

    @abc.abstractmethod
    def fit(self, ts: TimeSeries) -> "Forecaster":
        ...

    @abc.abstractmethod
    def predict(
        self,
        horizon: int,
        future_index: pd.DatetimeIndex,
        future_exog: pd.DataFrame | None = None,
        quantiles: tuple[float, ...] = DEFAULT_QUANTILES,
    ) -> ForecastResult:
        ...

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _residual_sigma(resid: np.ndarray) -> float:
        resid = resid[np.isfinite(resid)]
        if resid.size < 3:
            return float(np.std(resid)) if resid.size else 1.0
        # robust scale: 1.4826 * MAD
        mad = np.median(np.abs(resid - np.median(resid)))
        return float(max(1.4826 * mad, np.std(resid) * 0.5, 1e-6))

    @classmethod
    def _normal_quantiles(
        cls,
        mean: np.ndarray,
        sigma: float,
        quantiles: tuple[float, ...],
        horizon_growth: bool = True,
    ) -> dict[float, np.ndarray]:
        from math import sqrt

        try:
            from scipy.stats import norm
            z = {q: float(norm.ppf(q)) for q in quantiles}
        except Exception:  # noqa: BLE001
            z = {q: _ppf_approx(q) for q in quantiles}
        h = len(mean)
        # interval widens with the square root of the horizon step
        scale = np.sqrt(np.arange(1, h + 1)) if horizon_growth else np.ones(h)
        return {q: np.clip(mean + z[q] * sigma * scale, 0.0, None) for q in quantiles}


def _ppf_approx(p: float) -> float:
    """Acklam's rational approximation to the standard-normal quantile."""
    if p <= 0:
        return -6.0
    if p >= 1:
        return 6.0
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = (-2 * np.log(p)) ** 0.5
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = (-2 * np.log(1 - p)) ** 0.5
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
