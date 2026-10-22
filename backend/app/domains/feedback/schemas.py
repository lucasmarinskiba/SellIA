"""Feedback Hub Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domains.feedback.models import FeedbackSeverity, FeedbackStatus, FeedbackType

# ===== Feedback Schemas =====


class FeedbackCreate(BaseModel):
    type: FeedbackType
    title: str = Field(..., max_length=255)
    description: str
    category: str | None = Field(None, max_length=50)
    severity: FeedbackSeverity = FeedbackSeverity.MEDIUM
    screenshots: list[str] | None = None


class FeedbackUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    severity: FeedbackSeverity | None = None
    status: FeedbackStatus | None = None
    target_plan: str | None = None


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    business_id: uuid.UUID | None = None
    type: FeedbackType
    category: str | None = None
    severity: FeedbackSeverity
    status: FeedbackStatus
    title: str
    description: str
    screenshots: list[str] | None = None
    ai_analysis: str | None = None
    ai_solution_proposal: str | None = None
    ai_confidence: float | None = None
    votes_count: int
    comments_count: int
    target_plan: str | None = None
    estimated_effort_hours: int | None = None
    created_at: datetime
    updated_at: datetime
    user_voted: bool | None = False

    model_config = ConfigDict(from_attributes=True)


class FeedbackListResponse(BaseModel):
    items: list[FeedbackResponse]
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
    affected_modules: list[str]
    implementation_details: str | None = None
    difficulty: str | None = None
    estimated_hours: int | None = None
    target_plan: str
    status: str
    feature_flag_name: str | None = None
    deployed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Roadmap Schema =====


class RoadmapResponse(BaseModel):
    planned: list[SystemImprovementResponse]
    in_progress: list[SystemImprovementResponse]
    shipped: list[SystemImprovementResponse]


# ===== Feature Flag Schemas =====


class FeatureFlagResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    enabled_plans: list[str]
    rollout_percentage: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Changelog Schema =====


class ChangelogEntry(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    affected_modules: list[str]
    deployed_at: datetime
    target_plan: str
