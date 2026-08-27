"""Shared value types for the forecasting pipeline."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

import numpy as np
import pandas as pd


class Grain(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class SeriesLevel(str, enum.Enum):
    TOTAL = "total"          # whole-business demand (revenue or units)
    PRODUCT = "product"      # per SKU / product
    CHANNEL = "channel"      # per acquisition channel
    CATEGORY = "category"


class TargetKind(str, enum.Enum):
    UNITS = "units"
    REVENUE = "revenue"
    ORDERS = "orders"


@dataclass(frozen=True)
class SeriesSpec:
    business_id: str
    level: SeriesLevel
    target: TargetKind = TargetKind.REVENUE
    grain: Grain = Grain.DAILY
    key: Optional[str] = None          # sku / channel / category value; None for TOTAL
    label: Optional[str] = None
    country: str = "AR"                # for holiday features

    @property
    def series_key(self) -> str:
        return f"{self.level.value}:{self.target.value}:{self.grain.value}:{self.key or '*'}"


@dataclass
class TimeSeries:
    """A single, gap-filled, regularly-spaced series."""
    spec: SeriesSpec
    index: pd.DatetimeIndex
    values: np.ndarray                 # float, non-negative, gaps filled with 0
    exog: Optional[pd.DataFrame] = None  # aligned known regressors (price, ad_spend, promo)
    stockout_mask: Optional[np.ndarray] = None  # True where demand was likely censored

    def __post_init__(self) -> None:
        self.values = np.asarray(self.values, dtype=float)
        if len(self.index) != len(self.values):
            raise ValueError("index / values length mismatch")

    @property
    def n(self) -> int:
        return len(self.values)

    @property
    def seasonal_period(self) -> int:
        return 7 if self.spec.grain == Grain.DAILY else 52

    def to_frame(self) -> pd.DataFrame:
        df = pd.DataFrame({"y": self.values}, index=self.index)
        if self.exog is not None:
            df = df.join(self.exog)
        return df


@dataclass
class ForecastResult:
    model_name: str
    horizon: int
    index: pd.DatetimeIndex
    mean: np.ndarray
    quantiles: dict[float, np.ndarray] = field(default_factory=dict)   # {0.1: arr, 0.9: arr}
    diagnostics: dict = field(default_factory=dict)

    def clip_nonnegative(self) -> "ForecastResult":
        self.mean = np.clip(self.mean, 0.0, None)
        for q in self.quantiles:
            self.quantiles[q] = np.clip(self.quantiles[q], 0.0, None)
        return self


@dataclass
class FoldMetrics:
    model_name: str
    fold: int
    horizon: int
    mape: float
    wape: float
    rmse: float
    mae: float
    mase: float
    bias: float
    pinball: float
    coverage: float          # empirical coverage of the nominal interval


@dataclass
class BacktestReport:
    spec: SeriesSpec
    per_model: dict[str, list[FoldMetrics]] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)
    chosen: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        out = {}
        for name, folds in self.per_model.items():
            if not folds:
                continue
            out[name] = {
                "mase": float(np.mean([f.mase for f in folds])),
                "wape": float(np.mean([f.wape for f in folds])),
                "rmse": float(np.mean([f.rmse for f in folds])),
                "pinball": float(np.mean([f.pinball for f in folds])),
                "coverage": float(np.mean([f.coverage for f in folds])),
                "folds": len(folds),
            }
        return out
