"""Simulation / Training Engine — Pydantic Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SimulationScenarioCreate(BaseModel):
    name: str
    description: str | None = None
    difficulty: str = "beginner"
    objective: str = "close_sale"
    customer_persona: dict[str, Any]
    agent_type: str
    success_criteria: dict[str, Any] | None = None
    business_id: UUID | None = None


class SimulationScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID | None = None
    name: str
    description: str | None = None
    difficulty: str
    objective: str
    customer_persona: dict[str, Any]
    agent_type: str
    success_criteria: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SimulationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    user_id: UUID
    agent_config: dict[str, Any]
    status: str
    messages: list[dict[str, Any]]
    score: int | None = None
    outcome: str | None = None
    skills_tested: dict[str, Any]
    feedback: str | None = None
    duration_seconds: int | None = None
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime


class SimulationLeaderboardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    agent_type: str
    total_runs: int
    avg_score: float
    best_score: int
    success_rate: float
    updated_at: datetime


class QuickSimulationCreate(BaseModel):
    agent_type: str
    agent_config: dict[str, Any] | None = None


class RunSimulationCreate(BaseModel):
    agent_config: dict[str, Any] | None = None
