"""Forecasting persistence.

forecast_series       Registry of series under management for a business.
forecast_runs         One pipeline execution (weights, backtest scores, status).
forecast_points       The produced H-step probabilistic path.
forecast_accuracy     Realised error once the target dates have passed.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(str, enum.Enum):
    OK = "ok"
    SKIPPED = "skipped"
    FAILED = "failed"


class ForecastSeries(Base):
    __tablename__ = "forecast_series"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"),
                         nullable=False, index=True)

    series_key = Column(String(200), nullable=False)   # SeriesSpec.series_key
    level = Column(String(16), nullable=False)          # total|product|channel|category
    target = Column(String(16), nullable=False)         # units|revenue|orders
    grain = Column(String(10), default="daily", nullable=False)
    key = Column(String(200), nullable=True)            # sku / channel value
    label = Column(String(200), nullable=True)
    country = Column(String(2), default="AR", nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    intermittent = Column(Boolean, default=False, nullable=False)
    adi = Column(Numeric(10, 3), nullable=True)
    zero_share = Column(Numeric(6, 4), nullable=True)

    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_wape = Column(Numeric(10, 3), nullable=True)
    last_mase = Column(Numeric(10, 4), nullable=True)

    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    runs = relationship("ForecastRun", back_populates="series", cascade="all, delete-orphan", lazy="noload")

    __table_args__ = (
        UniqueConstraint("business_id", "series_key", name="uq_forecast_series_business_key"),
        Index("ix_forecast_series_business_active", "business_id", "is_active"),
    )


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id = Column(UUID(as_uuid=True), ForeignKey("forecast_series.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"),
                         nullable=False, index=True)

    run_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    origin_date = Column(Date, nullable=False)          # last actual day used
    horizon = Column(Integer, nullable=False)
    grain = Column(String(10), default="daily", nullable=False)

    status = Column(String(10), default=RunStatus.OK.value, nullable=False)
    error = Column(Text, nullable=True)

    model_weights = Column(JSONB, default=dict, nullable=False)
    chosen_models = Column(JSONB, default=list, nullable=False)
    backtest_summary = Column(JSONB, default=dict, nullable=False)
    n_history = Column(Integer, default=0, nullable=False)

    wape_backtest = Column(Numeric(10, 3), nullable=True)
    mase_backtest = Column(Numeric(10, 4), nullable=True)
    pinball_backtest = Column(Numeric(14, 4), nullable=True)
    coverage_backtest = Column(Numeric(6, 4), nullable=True)

    total_forecast = Column(Numeric(18, 2), nullable=True)   # sum of mean over horizon
    reconciled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=_utcnow)

    series = relationship("ForecastSeries", back_populates="runs")
    points = relationship("ForecastPoint", back_populates="run", cascade="all, delete-orphan", lazy="noload")

    __table_args__ = (
        Index("ix_forecast_runs_business_run_at", "business_id", "run_at"),
        Index("ix_forecast_runs_series_run_at", "series_id", "run_at"),
    )


class ForecastPoint(Base):
    __tablename__ = "forecast_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("forecast_runs.id", ondelete="CASCADE"),
                    nullable=False, index=True)
    series_id = Column(UUID(as_uuid=True), ForeignKey("forecast_series.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"),
                         nullable=False, index=True)

    target_date = Column(Date, nullable=False, index=True)
    horizon_step = Column(Integer, nullable=False)

    yhat = Column(Numeric(18, 4), nullable=False)
    q10 = Column(Numeric(18, 4), nullable=True)
    q50 = Column(Numeric(18, 4), nullable=True)
    q90 = Column(Numeric(18, 4), nullable=True)
    quantiles = Column(JSONB, default=dict, nullable=False)   # {"0.25": x, "0.75": y, ...}

    created_at = Column(DateTime(timezone=True), default=_utcnow)

    run = relationship("ForecastRun", back_populates="points")

    __table_args__ = (
        UniqueConstraint("run_id", "target_date", name="uq_forecast_point_run_date"),
        Index("ix_forecast_points_series_date", "series_id", "target_date"),
    )


class ForecastAccuracy(Base):
    __tablename__ = "forecast_accuracy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id = Column(UUID(as_uuid=True), ForeignKey("forecast_series.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("forecast_runs.id", ondelete="SET NULL"), nullable=True)

    evaluated_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    window_start = Column(Date, nullable=False)
    window_end = Column(Date, nullable=False)
    horizon_bucket = Column(String(16), nullable=False)   # "1-7", "8-14", "15-28"

    n = Column(Integer, default=0, nullable=False)
    wape = Column(Numeric(10, 3), nullable=True)
    mape = Column(Numeric(10, 3), nullable=True)
    mase = Column(Numeric(10, 4), nullable=True)
    bias = Column(Numeric(10, 4), nullable=True)
    rmse = Column(Numeric(18, 4), nullable=True)
    coverage = Column(Numeric(6, 4), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_forecast_accuracy_series_eval", "series_id", "evaluated_at"),
    )


FORECASTING_TABLES = [
    ForecastSeries.__table__,
    ForecastRun.__table__,
    ForecastPoint.__table__,
    ForecastAccuracy.__table__,
]
