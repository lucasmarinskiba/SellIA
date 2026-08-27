"""Forecast-accuracy metrics.

All functions take 1-D numpy arrays of equal length and return a float.
`y_true` may contain zeros — scale-free metrics guard against div-by-zero.
"""

from __future__ import annotations

import numpy as np

EPS = 1e-9


def _align(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return y_true, y_pred


def mae(y_true, y_pred) -> float:
    y_true, y_pred = _align(y_true, y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true, y_pred) -> float:
    y_true, y_pred = _align(y_true, y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true, y_pred) -> float:
    """Mean absolute percentage error over non-zero actuals (%)."""
    y_true, y_pred = _align(y_true, y_pred)
    mask = np.abs(y_true) > EPS
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def wape(y_true, y_pred) -> float:
    """Weighted APE = sum|e| / sum|y|  (%). Robust to zeros; the industry
    standard for demand at SKU level."""
    y_true, y_pred = _align(y_true, y_pred)
    denom = np.sum(np.abs(y_true))
    if denom < EPS:
        return float(np.sum(np.abs(y_pred)) > EPS) * 100.0
    return float(np.sum(np.abs(y_true - y_pred)) / denom * 100.0)


def bias(y_true, y_pred) -> float:
    """Signed mean error as a fraction of mean actual (+ = over-forecast)."""
    y_true, y_pred = _align(y_true, y_pred)
    denom = np.mean(np.abs(y_true))
    if denom < EPS:
        return 0.0
    return float(np.mean(y_pred - y_true) / denom)


def mase(y_true, y_pred, y_train, season: int = 1) -> float:
    """Mean absolute scaled error — scaled by the in-sample seasonal-naive MAE.
    < 1 means better than seasonal naive."""
    y_true, y_pred = _align(y_true, y_pred)
    y_train = np.asarray(y_train, dtype=float)
    if len(y_train) <= season:
        season = 1
    naive_err = np.mean(np.abs(y_train[season:] - y_train[:-season])) if len(y_train) > season else EPS
    naive_err = max(naive_err, EPS)
    return float(np.mean(np.abs(y_true - y_pred)) / naive_err)


def pinball_loss(y_true, quantile_preds: dict[float, np.ndarray]) -> float:
    """Average pinball (quantile) loss across the supplied quantiles."""
    if not quantile_preds:
        return float("nan")
    y_true = np.asarray(y_true, dtype=float)
    losses = []
    for q, pred in quantile_preds.items():
        pred = np.asarray(pred, dtype=float)
        diff = y_true - pred
        losses.append(np.mean(np.maximum(q * diff, (q - 1.0) * diff)))
    return float(np.mean(losses))


def interval_coverage(y_true, lower, upper) -> float:
    """Fraction of actuals inside [lower, upper]."""
    y_true = np.asarray(y_true, dtype=float)
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    return float(np.mean((y_true >= lower) & (y_true <= upper)))


def all_metrics(
    y_true,
    y_pred,
    y_train,
    season: int = 1,
    quantile_preds: dict[float, np.ndarray] | None = None,
    nominal_interval: tuple[float, float] = (0.1, 0.9),
) -> dict[str, float]:
    q = quantile_preds or {}
    lo_key = min(q, key=lambda k: abs(k - nominal_interval[0])) if q else None
    hi_key = min(q, key=lambda k: abs(k - nominal_interval[1])) if q else None
    cover = (
        interval_coverage(y_true, q[lo_key], q[hi_key])
        if lo_key is not None and hi_key is not None and lo_key != hi_key
        else float("nan")
    )
    return {
        "mape": mape(y_true, y_pred),
        "wape": wape(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "mae": mae(y_true, y_pred),
        "mase": mase(y_true, y_pred, y_train, season),
        "bias": bias(y_true, y_pred),
        "pinball": pinball_loss(y_true, q),
        "coverage": cover,
    }
