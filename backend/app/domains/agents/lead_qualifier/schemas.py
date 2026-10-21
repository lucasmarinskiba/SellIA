"""Lead Qualifier Auto-Agent Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BANTScore(BaseModel):
    budget: float = Field(default=0.0, ge=0.0, le=100.0)
    authority: float = Field(default=0.0, ge=0.0, le=100.0)
    need: float = Field(default=0.0, ge=0.0, le=100.0)
    timeline: float = Field(default=0.0, ge=0.0, le=100.0)


class BANTResponse(BaseModel):
    budget_range: str | None = None
    authority_level: str | None = None
    need_urgency: str | None = None
    timeline: str | None = None


class LeadQualificationBase(BaseModel):
    conversation_id: UUID | None = None
    customer_id: UUID | None = None
    bant_score: BANTScore = Field(default_factory=BANTScore)
    qualification_score: float = Field(default=0.0, ge=0.0, le=100.0)
    status: str = "nurture"  # qualified | disqualified | nurture
    routing_destination: str | None = None
    summary: str | None = None


class LeadQualificationCreate(LeadQualificationBase):
    business_id: UUID


class LeadQualificationOut(LeadQualificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    created_at: datetime


class QualifyLeadOut(BaseModel):
    qualification_id: UUID
    bant_score: BANTScore
    qualification_score: float
    status: str
    routing_destination: str | None = None
    summary: str
    next_question: str | None = None


class QualifyingQuestionOut(BaseModel):
    conversation_id: UUID
    question: str
    bant_dimension: str  # budget | authority | need | timeline


class RouteLeadIn(BaseModel):
    routing_destination: str


class RouteLeadOut(BaseModel):
    qualification_id: UUID
    routing_destination: str
    status: str
