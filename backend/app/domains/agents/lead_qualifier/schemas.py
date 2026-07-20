"""Lead Qualifier Auto-Agent Schemas"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class BANTScore(BaseModel):
    budget: float = Field(default=0.0, ge=0.0, le=100.0)
    authority: float = Field(default=0.0, ge=0.0, le=100.0)
    need: float = Field(default=0.0, ge=0.0, le=100.0)
    timeline: float = Field(default=0.0, ge=0.0, le=100.0)


class BANTResponse(BaseModel):
    budget_range: Optional[str] = None
    authority_level: Optional[str] = None
    need_urgency: Optional[str] = None
    timeline: Optional[str] = None


class LeadQualificationBase(BaseModel):
    conversation_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    bant_score: BANTScore = Field(default_factory=BANTScore)
    qualification_score: float = Field(default=0.0, ge=0.0, le=100.0)
    status: str = "nurture"  # qualified | disqualified | nurture
    routing_destination: Optional[str] = None
    summary: Optional[str] = None


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
    routing_destination: Optional[str] = None
    summary: str
    next_question: Optional[str] = None


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
