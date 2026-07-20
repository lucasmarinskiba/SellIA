"""Market Analyst Schemas"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompetitorSnapshotBase(BaseModel):
    name: str
    url: Optional[str] = None
    price_range: Optional[str] = None
    key_features: List[str] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    sentiment_score: Optional[float] = None
    raw_data: Dict[str, Any] = {}


class CompetitorSnapshotOut(CompetitorSnapshotBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    created_at: datetime


class MarketAnalysisJobBase(BaseModel):
    target_market: str


class MarketAnalysisJobCreate(MarketAnalysisJobBase):
    competitors_list: List[Dict[str, Any]] = []  # [{"name": "X", "url": "Y"}, ...]


class MarketAnalysisJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    status: str
    target_market: str
    competitors_analyzed: int
    trends_found: int
    report_url: Optional[str] = None
    report_data: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class MarketAnalysisJobDetailOut(MarketAnalysisJobOut):
    snapshots: List[CompetitorSnapshotOut] = []


class MarketReportOut(BaseModel):
    job_id: UUID
    target_market: str
    competitors: List[CompetitorSnapshotOut] = []
    trends: List[Dict[str, Any]] = []
    gaps: List[Dict[str, Any]] = []
    opportunities: List[Dict[str, Any]] = []
    charts_data: Dict[str, Any] = {}
    generated_at: datetime
