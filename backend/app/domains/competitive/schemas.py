"""
Competitive Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BattlecardBase(BaseModel):
    competitor_name: str
    competitor_url: Optional[str] = None
    our_strengths: list[str] = []
    our_weaknesses: list[str] = []
    their_strengths: list[str] = []
    their_weaknesses: list[str] = []
    price_comparison: Optional[str] = None
    feature_comparison: dict = {}
    market_share_estimate: Optional[str] = None
    notes: Optional[str] = None


class BattlecardCreate(BattlecardBase):
    pass


class BattlecardUpdate(BaseModel):
    competitor_name: Optional[str] = None
    competitor_url: Optional[str] = None
    our_strengths: Optional[list[str]] = None
    our_weaknesses: Optional[list[str]] = None
    their_strengths: Optional[list[str]] = None
    their_weaknesses: Optional[list[str]] = None
    price_comparison: Optional[str] = None
    feature_comparison: Optional[dict] = None
    market_share_estimate: Optional[str] = None
    notes: Optional[str] = None


class BattlecardOut(BattlecardBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class BattlecardCompareOut(BaseModel):
    competitor_name: str
    competitor_url: Optional[str] = None
    our_strengths: list[str]
    our_weaknesses: list[str]
    their_strengths: list[str]
    their_weaknesses: list[str]
    price_comparison: Optional[str] = None
    feature_comparison: dict
    market_share_estimate: Optional[str] = None
    notes: Optional[str] = None
    comparison_summary: dict


# ═══════════════════════════════════════════════════════
#   Competitive Intelligence Monitor Schemas
# ═══════════════════════════════════════════════════════

class MonitorCreate(BaseModel):
    business_id: UUID
    competitor_name: str
    competitor_url: str
    products_to_track: list[str] = []


class MonitorUpdate(BaseModel):
    competitor_name: Optional[str] = None
    competitor_url: Optional[str] = None
    products_to_track: Optional[list[str]] = None
    status: Optional[str] = None


class MonitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    competitor_name: str
    competitor_url: str
    products_to_track: list[str]
    last_scraped_at: Optional[datetime] = None
    last_snapshot: dict
    status: str
    created_at: datetime
    updated_at: datetime


class ScrapeResult(BaseModel):
    monitor_id: UUID
    prices_found: dict
    scraped_at: datetime
    status: str


class ChangeItem(BaseModel):
    change_type: str
    severity: str
    competitor_name: str
    product_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    diff_percent: Optional[float] = None
    detected_at: datetime


class StrategySuggestion(BaseModel):
    change: ChangeItem
    suggestion: str
    options: list[str]
    risk_note: Optional[str] = None


class IntelligenceDashboard(BaseModel):
    monitors: list[MonitorOut]
    recent_changes: list[ChangeItem]
    alerts_count: int
    unread_alerts: int
    strategies: list[StrategySuggestion]
