"""Simulation / Training Engine — Pydantic Schemas (v2)"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# SimulationScenario
# ---------------------------------------------------------------------------


class SimulationScenarioBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: str | None = None
    difficulty: str = Field(default="medium", pattern=r"^(easy|medium|hard|expert)$")
    customer_persona: dict[str, Any] = Field(default_factory=dict)
    objective: str = Field(
        default="close_sale",
        pattern=r"^(close_sale|set_appointment|gather_info|handle_complaint)$",
    )
    success_criteria: dict[str, Any] = Field(default_factory=dict)
    agent_type: str = Field(default="general", max_length=50)
    is_active: bool = True


class SimulationScenarioCreate(SimulationScenarioBase):
    business_id: UUID


class SimulationScenarioUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    difficulty: str | None = Field(default=None, pattern=r"^(easy|medium|hard|expert)$")
    customer_persona: dict[str, Any] | None = None
    objective: str | None = Field(
        default=None,
        pattern=r"^(close_sale|set_appointment|gather_info|handle_complaint)$",
    )
    success_criteria: dict[str, Any] | None = None
    agent_type: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


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
    timestamp: str | None = None


class SimulationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    agent_id: UUID | None = None
    status: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    score: int | None = None
    objective_achieved: bool | None = None
    time_to_close_seconds: int | None = None
    customer_satisfaction: float | None = None
    skills_tested: dict[str, Any] = Field(default_factory=dict)
    feedback: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class SimulationStartRequest(BaseModel):
    scenario_id: UUID
    agent_id: UUID | None = None  # if None, uses scenario.agent_type


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
    customer_satisfaction: float | None = None
    created_at: datetime
