"""BI Models — re-exported from analytics to avoid duplication."""

from app.domains.analytics.models import (
    FunnelMetric as FunnelMetrics,
    CohortMetric as CohortMetrics,
    ChurnPrediction,
    LtvPrediction,
    InsightAlert,
)

__all__ = [
    "FunnelMetrics",
    "CohortMetrics",
    "ChurnPrediction",
    "LtvPrediction",
    "InsightAlert",
]
