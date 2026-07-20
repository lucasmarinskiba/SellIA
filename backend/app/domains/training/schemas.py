"""Simulation / Training Engine — Pydantic Schemas (v2)"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# SimulationScenario
# ---------------------------------------------------------------------------

class SimulationScenarioBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    difficulty: str = Field(default="medium", pattern=r"^(easy|medium|hard|expert)$")
    customer_persona: dict[str, Any] = Field(default_factory=dict)
    objective: str = Field(default="close_sale", pattern=r"^(close_sale|set_appointment|gather_info|handle_complaint)$")
    success_criteria: dict[str, Any] = Field(default_factory=dict)
    agent_type: str = Field(default="general", max_length=50)
    is_active: bool = True


class SimulationScenarioCreate(SimulationScenarioBase):
    business_id: UUID


class SimulationScenarioUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    difficulty: Optional[str] = Field(default=None, pattern=r"^(easy|medium|hard|expert)$")
    customer_persona: Optional[dict[str, Any]] = None
    objective: Optional[str] = Field(default=None, pattern=r"^(close_sale|set_appointment|gather_info|handle_complaint)$")
    success_criteria: Optional[dict[str, Any]] = None
    agent_type: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None


class SimulationScenarioOut(SimulationScenarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# SimulationRun
# ---------------------------------------------------------------------------

class SimulationMessage(BaseModel):
    role: str  # agent | customer | system
    content: str
    turn: int
    timestamp: Optional[str] = None


class SimulationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    agent_id: Optional[UUID] = None
    status: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    score: Optional[int] = None
    objective_achieved: Optional[bool] = None
    time_to_close_seconds: Optional[int] = None
    customer_satisfaction: Optional[float] = None
    skills_tested: dict[str, Any] = Field(default_factory=dict)
    feedback: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class SimulationStartRequest(BaseModel):
    scenario_id: UUID
    agent_id: Optional[UUID] = None  # if None, uses scenario.agent_type


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

class LeaderboardEntry(BaseModel):
    run_id: UUID
    scenario_id: UUID
    scenario_name: str
    agent_type: str
    score: int
    objective_achieved: bool
    customer_satisfaction: Optional[float] = None
    created_at: datetime
