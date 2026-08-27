"""Feature engineering for the ML forecaster (direct multi-horizon).

`build_supervised` pairs the feature vector known at an origin day `t`
(lags/rolling/EWMA of y up to and including `t`, plus calendar and known
regressors for the *target* day) with the target `y[t+h]` for every
horizon step `h`. Predicting is then a single batched call over
h = 1..H from the last origin row — no recursion, no error accumulation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.domains.forecasting.calendar_features import calendar_frame

LAGS = (1, 2, 3, 7, 14, 21, 28, 35)
ROLL_WINDOWS = (7, 14, 28)
EWM_SPANS = (7, 14, 28)


def _autoregressive_frame(y: pd.Series) -> pd.DataFrame:
    """Features that summarise demand *as of the end of day t* (lag 0 = y[t])."""
    f = pd.DataFrame(index=y.index)
    for lag in LAGS:
        f[f"lag_{lag}"] = y.shift(lag - 1)          # lag_1 = y[t], lag_7 = y[t-6]
    for w in ROLL_WINDOWS:
        r = y.rolling(w, min_periods=max(2, w // 2))
        f[f"rmean_{w}"] = r.mean()
        f[f"rstd_{w}"] = r.std()
        f[f"rmax_{w}"] = r.max()
        f[f"rmin_{w}"] = r.min()
        f[f"rmean_{w}_slope"] = r.mean().diff()
    for s in EWM_SPANS:
        f[f"ewm_{s}"] = y.ewm(span=s, min_periods=2).mean()
    f["diff_1"] = y.diff()
    f["diff_7"] = y - y.shift(7)
    f["mom_7"] = (y - y.shift(7)) / (y.shift(7).abs() + 1.0)
    n = len(y)
    f["trend"] = np.arange(n, dtype=float) / max(n - 1, 1)
    f["zero_share_28"] = y.eq(0).rolling(28, min_periods=5).mean()
    f["mean_level"] = y.expanding(min_periods=7).mean()
    return f


def build_supervised(
    values: np.ndarray,
    index: pd.DatetimeIndex,
    horizon: int,
    country: str = "AR",
    grain: str = "daily",
    exog: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    y = pd.Series(np.asarray(values, dtype=float), index=index, name="y")
    ar = _autoregressive_frame(y)
    cal = calendar_frame(index, country=country, grain=grain)  # targets are always within history

    n = len(index)
    ar_cols = list(ar.columns)
    cal_cols = [f"cal_{c}" for c in cal.columns]
    ar_np = ar.to_numpy(dtype=float)
    cal_np = cal.to_numpy(dtype=float)
    exog_cols: list[str] = []
    exog_np = None
    if exog is not None and not exog.empty:
        exog_np = np.nan_to_num(exog.reindex(index).to_numpy(dtype=float))
        exog_cols = [f"x_{c}" for c in exog.columns]

    valid = np.isfinite(ar_np[:, ar_cols.index("lag_7")]) if "lag_7" in ar_cols else np.ones(n, bool)

    blocks_X = []
    blocks_y = []
    for h in range(1, horizon + 1):
        if n - h <= 0:
            break
        orig = np.arange(0, n - h)
        orig = orig[valid[orig]]
        if orig.size == 0:
            continue
        tgt = orig + h
        parts = [ar_np[orig], np.full((orig.size, 1), float(h))]
        parts.append(cal_np[tgt])
        if exog_np is not None:
            parts.append(exog_np[tgt])
        blocks_X.append(np.hstack(parts))
        blocks_y.append(y.to_numpy()[tgt])

    if not blocks_X:
        return pd.DataFrame(), pd.Series(dtype=float), []
    cols = ar_cols + ["h"] + cal_cols + exog_cols
    X = pd.DataFrame(np.vstack(blocks_X), columns=cols).fillna(0.0)
    yv = pd.Series(np.concatenate(blocks_y), dtype=float)
    return X, yv, cols


def origin_matrix(
    values: np.ndarray,
    index: pd.DatetimeIndex,
    horizon: int,
    columns: list[str],
    country: str = "AR",
    grain: str = "daily",
    exog_future: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """One row per horizon step, all sharing the last available origin
    features, differing only in `h` and the target-day calendar/exog."""
    y = pd.Series(np.asarray(values, dtype=float), index=index, name="y")
    ar = _autoregressive_frame(y)
    ar_cols = list(ar.columns)
    ar_row = np.nan_to_num(ar.to_numpy(dtype=float)[-1])

    step = index[-1] - index[-2] if len(index) > 1 else pd.Timedelta(days=1)
    fut_index = pd.DatetimeIndex([index[-1] + step * (i + 1) for i in range(horizon)])
    cal = calendar_frame(fut_index, country=country, grain=grain)
    cal_np = cal.to_numpy(dtype=float)
    cal_cols = [f"cal_{c}" for c in cal.columns]

    exog_np = None
    exog_cols: list[str] = []
    if exog_future is not None and not exog_future.empty:
        exog_np = np.nan_to_num(exog_future.reindex(fut_index).to_numpy(dtype=float))
        exog_cols = [f"x_{c}" for c in exog_future.columns]

    h_col = np.arange(1, horizon + 1, dtype=float).reshape(-1, 1)
    parts = [np.tile(ar_row, (horizon, 1)), h_col, cal_np]
    if exog_np is not None:
        parts.append(exog_np)
    mat = np.hstack(parts)
    built_cols = ar_cols + ["h"] + cal_cols + exog_cols
    X = pd.DataFrame(mat, columns=built_cols).fillna(0.0)
    for c in columns:
        if c not in X.columns:
            X[c] = 0.0
    return X[columns], fut_index
