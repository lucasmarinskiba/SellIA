"""Calendar + holiday features.

Uses the `holidays` package when available; otherwise a small built-in
table of fixed-date Argentine/LatAm public holidays. Fourier terms give
the models smooth multi-scale seasonality.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:  # optional
    import holidays as _holidays_pkg
    _HAS_HOLIDAYS = True
except Exception:  # noqa: BLE001
    _holidays_pkg = None
    _HAS_HOLIDAYS = False


# Fallback: (month, day) fixed public holidays for a few LatAm countries.
_FALLBACK_FIXED = {
    "AR": [(1, 1), (3, 24), (4, 2), (5, 1), (5, 25), (6, 20), (7, 9), (12, 8), (12, 25)],
    "MX": [(1, 1), (2, 5), (3, 21), (5, 1), (9, 16), (11, 20), (12, 25)],
    "CL": [(1, 1), (5, 1), (5, 21), (9, 18), (9, 19), (12, 25)],
    "CO": [(1, 1), (5, 1), (7, 20), (8, 7), (12, 25)],
    "BR": [(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (12, 25)],
    "US": [(1, 1), (7, 4), (11, 11), (12, 25)],
}

# Commercial "demand spike" days worth their own flag.
_COMMERCIAL = [(11, 27), (11, 28), (11, 29), (11, 30), (12, 1),  # Black Friday / Cyber Monday window
               (2, 14), (5, 10), (12, 24), (12, 31)]


def _holiday_set(country: str, years: list[int]) -> set:
    country = (country or "AR").upper()
    if _HAS_HOLIDAYS:
        try:
            return set(_holidays_pkg.country_holidays(country, years=years).keys())
        except Exception:  # noqa: BLE001
            pass
    fixed = _FALLBACK_FIXED.get(country, _FALLBACK_FIXED["AR"])
    out = set()
    for y in years:
        for m, d in fixed:
            try:
                out.add(pd.Timestamp(year=y, month=m, day=d).date())
            except ValueError:
                continue
    return out


def calendar_frame(index: pd.DatetimeIndex, country: str = "AR", grain: str = "daily") -> pd.DataFrame:
    idx = pd.DatetimeIndex(index)
    years = sorted({d.year for d in idx} | {d.year + 1 for d in idx})
    hol = _holiday_set(country, years)
    dates = idx.date

    df = pd.DataFrame(index=idx)
    df["dow"] = idx.dayofweek
    df["dom"] = idx.day
    df["month"] = idx.month
    df["weekofyear"] = idx.isocalendar().week.astype(int).values
    df["quarter"] = idx.quarter
    df["is_weekend"] = (idx.dayofweek >= 5).astype(int)
    df["is_month_start"] = idx.is_month_start.astype(int)
    df["is_month_end"] = idx.is_month_end.astype(int)
    df["is_payday"] = idx.day.isin([1, 15, 16, 30, 31]).astype(int)

    is_hol = np.array([d in hol for d in dates], dtype=int)
    df["is_holiday"] = is_hol
    # holiday proximity (yesterday / tomorrow)
    df["is_holiday_eve"] = np.r_[is_hol[1:], 0]
    df["is_post_holiday"] = np.r_[0, is_hol[:-1]]

    commercial = {(m, d) for m, d in _COMMERCIAL}
    df["is_commercial_peak"] = np.array(
        [(ts.month, ts.day) in commercial for ts in idx], dtype=int
    )

    # Fourier seasonality
    if grain == "daily":
        t = idx.dayofyear.values.astype(float)
        for k in (1, 2, 3):
            df[f"yr_sin{k}"] = np.sin(2 * np.pi * k * t / 365.25)
            df[f"yr_cos{k}"] = np.cos(2 * np.pi * k * t / 365.25)
        dow = idx.dayofweek.values.astype(float)
        for k in (1, 2, 3):
            df[f"wk_sin{k}"] = np.sin(2 * np.pi * k * dow / 7.0)
            df[f"wk_cos{k}"] = np.cos(2 * np.pi * k * dow / 7.0)
    else:  # weekly
        w = df["weekofyear"].values.astype(float)
        for k in (1, 2, 3):
            df[f"yr_sin{k}"] = np.sin(2 * np.pi * k * w / 52.0)
            df[f"yr_cos{k}"] = np.cos(2 * np.pi * k * w / 52.0)

    return df
