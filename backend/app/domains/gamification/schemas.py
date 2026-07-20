"""Gamification Pydantic Schemas"""

import uuid
from datetime import datetime
from typing import Optional, Any, List, Dict
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class GamificationProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    level: int
    level_title: str
    total_xp: int
    xp_to_next_level: int
    progress_pct: Decimal
    current_login_streak: int
    max_login_streak: int
    autopilot_trust_streak: int
    total_achievements: int
    total_sales_closed: int
    total_revenue_generated: Decimal
    total_leads_acquired: int
    total_content_published: int
    total_reviews_collected: int
    total_referrals_generated: int
    garden_state: dict
    companion_name: str
    companion_mood: str
    user_mood_today: Optional[str]
    created_at: datetime
    updated_at: datetime


class AchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str
    category: str
    tier: str
    xp_reward: int
    icon: str
    color: str
    animation: str


class UserAchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    achievement_id: uuid.UUID
    achievement: Optional[AchievementResponse]
    unlocked_at: datetime
    was_celebrated: bool


class CelebrationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    event_title: str
    event_description: Optional[str]
    event_value: Optional[Decimal]
    intensity: str
    companion_message: Optional[str]
    companion_emotion: str
    was_shown: bool
    created_at: datetime


class GardenStateResponse(BaseModel):
    garden: dict
    level: int
    level_title: str


class CompanionMessageResponse(BaseModel):
    message: str
    mood: str
    context: str


class MoodCheckinRequest(BaseModel):
    mood: str
    energy_level: int = 5
    notes: Optional[str] = ""


class MoodCheckinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mood: str
    energy_level: int
    ai_response: Optional[str]
    created_at: datetime


class SaleRecordedResponse(BaseModel):
    xp_gained: int
    new_achievements: List[Dict[str, Any]]
    celebration_intensity: str
    new_level: Optional[int] = None
    new_level_title: Optional[str] = None


class LoginResponse(BaseModel):
    streak: int
    xp_gained: int
    new_achievements: List[Dict[str, Any]]
    welcome_message: str


class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: str
    full_name: str
    email: str
    level: int
    total_xp: int
    total_sales_closed: int
    total_revenue_generated: float
    total_referrals_generated: int
    current_login_streak: int
    total_achievements: int


class UserRankResponse(BaseModel):
    rank: Optional[int]
    total_members: int
    user_id: str
    full_name: str
    email: str
    level: int
    total_xp: int
    total_sales_closed: int
    total_revenue_generated: float
    total_referrals_generated: int
    current_login_streak: int
    total_achievements: int


class NearbyUsersResponse(BaseModel):
    user_rank: Optional[int]
    metric: str
    nearby: List[LeaderboardEntryResponse]


class TeamStatsResponse(BaseModel):
    total_members: int
    total_sales: int
    total_revenue: float
    avg_streak: float
    top_performer_name: Optional[str]
    top_performer_xp: int
