"""Forecasting model registry."""

from __future__ import annotations

from app.domains.forecasting.models.base import Forecaster
from app.domains.forecasting.models.ensemble import EnsembleForecaster
from app.domains.forecasting.models.ml import GBMForecaster
from app.domains.forecasting.models.statistical import (
    CrostonForecaster,
    HoltWintersForecaster,
    SeasonalNaiveForecaster,
    ThetaForecaster,
)

try:
    from app.domains.forecasting.models.optional_backends import (
        ETSStatsmodelsForecaster,
        SarimaForecaster,
        _HAS_STATSMODELS,
    )
except Exception:  # noqa: BLE001
    ETSStatsmodelsForecaster = None
    SarimaForecaster = None
    _HAS_STATSMODELS = False


def default_model_pool(intermittent: bool, light_gbm: bool = False) -> list[Forecaster]:
    """The candidate models a series is backtested against.

    `light_gbm=True` (used during backtesting) makes the GBM skip its
    quantile sub-models and use fewer boosting rounds.
    """
    if intermittent:
        pool: list[Forecaster] = [
            SeasonalNaiveForecaster(),
            CrostonForecaster(variant="sba"),
            CrostonForecaster(variant="classic"),
            GBMForecaster(light=light_gbm),
        ]
        return pool

    pool = [
        SeasonalNaiveForecaster(),
        ThetaForecaster(),
        HoltWintersForecaster(),
        GBMForecaster(light=light_gbm),
    ]
    if _HAS_STATSMODELS and ETSStatsmodelsForecaster is not None:
        pool.append(ETSStatsmodelsForecaster())
    if _HAS_STATSMODELS and SarimaForecaster is not None:
        pool.append(SarimaForecaster())
    return pool


__all__ = [
    "Forecaster",
    "SeasonalNaiveForecaster",
    "ThetaForecaster",
    "HoltWintersForecaster",
    "CrostonForecaster",
    "GBMForecaster",
    "EnsembleForecaster",
    "default_model_pool",
]
