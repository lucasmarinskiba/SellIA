"""Feedback Hub Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from app.domains.feedback.models import FeedbackType, FeedbackSeverity, FeedbackStatus


# ===== Feedback Schemas =====

class FeedbackCreate(BaseModel):
    type: FeedbackType
    title: str = Field(..., max_length=255)
    description: str
    category: Optional[str] = Field(None, max_length=50)
    severity: FeedbackSeverity = FeedbackSeverity.MEDIUM
    screenshots: Optional[List[str]] = None


class FeedbackUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    severity: Optional[FeedbackSeverity] = None
    status: Optional[FeedbackStatus] = None
    target_plan: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    business_id: Optional[uuid.UUID] = None
    type: FeedbackType
    category: Optional[str] = None
    severity: FeedbackSeverity
    status: FeedbackStatus
    title: str
    description: str
    screenshots: Optional[List[str]] = None
    ai_analysis: Optional[str] = None
    ai_solution_proposal: Optional[str] = None
    ai_confidence: Optional[float] = None
    votes_count: int
    comments_count: int
    target_plan: Optional[str] = None
    estimated_effort_hours: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    user_voted: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class FeedbackListResponse(BaseModel):
    items: List[FeedbackResponse]
    total: int


# ===== Vote Schemas =====

class VoteResponse(BaseModel):
    id: uuid.UUID
    feedback_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Comment Schemas =====

class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: uuid.UUID
    feedback_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== System Improvement Schemas =====

class SystemImprovementResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    affected_modules: List[str]
    implementation_details: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_hours: Optional[int] = None
    target_plan: str
    status: str
    feature_flag_name: Optional[str] = None
    deployed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Roadmap Schema =====

class RoadmapResponse(BaseModel):
    planned: List[SystemImprovementResponse]
    in_progress: List[SystemImprovementResponse]
    shipped: List[SystemImprovementResponse]


# ===== Feature Flag Schemas =====

class FeatureFlagResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    enabled_plans: List[str]
    rollout_percentage: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Changelog Schema =====

class ChangelogEntry(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    affected_modules: List[str]
    deployed_at: datetime
    target_plan: str
