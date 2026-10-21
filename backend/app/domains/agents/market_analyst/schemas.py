"""Market Analyst Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompetitorSnapshotBase(BaseModel):
    name: str
    url: str | None = None
    price_range: str | None = None
    key_features: list[str] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    sentiment_score: float | None = None
    raw_data: dict[str, Any] = {}


class CompetitorSnapshotOut(CompetitorSnapshotBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    created_at: datetime


class MarketAnalysisJobBase(BaseModel):
    target_market: str


class MarketAnalysisJobCreate(MarketAnalysisJobBase):
    competitors_list: list[dict[str, Any]] = []  # [{"name": "X", "url": "Y"}, ...]


class MarketAnalysisJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    status: str
    target_market: str
    competitors_analyzed: int
    trends_found: int
    report_url: str | None = None
    report_data: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class MarketAnalysisJobDetailOut(MarketAnalysisJobOut):
    snapshots: list[CompetitorSnapshotOut] = []


class MarketReportOut(BaseModel):
    job_id: UUID
    target_market: str
    competitors: list[CompetitorSnapshotOut] = []
    trends: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    opportunities: list[dict[str, Any]] = []
    charts_data: dict[str, Any] = {}
    generated_at: datetime
