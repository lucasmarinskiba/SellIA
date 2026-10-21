"""Computer Use Agents — Pydantic Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ========== Acciones ==========


class ComputerUseAction(BaseModel):
    action_type: str = Field(
        ...,
        description="Tipo de acción: click, type, scroll, navigate, wait, done, error",
    )
    params: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="", description="Razón por la que se tomó esta acción")


# ========== Sesiones ==========


class ComputerUseSessionCreate(BaseModel):
    task_description: str = Field(..., min_length=1, max_length=2000)
    start_url: str | None = Field(None, max_length=2048)
    business_id: UUID | None = None
    browser_type: str = Field("chromium", pattern="^(chromium|firefox|webkit)$")
    profile_id: UUID | None = None
    proxy_config_id: UUID | None = None
    mode: str = Field("supervised", pattern="^(supervised|autopilot)$")


class ComputerUseSessionUpdate(BaseModel):
    status: str | None = None
    error_message: str | None = None
    result_data: dict | None = None


class ComputerUseSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    business_id: UUID | None
    task_description: str
    status: str
    current_url: str | None
    result_data: dict | None
    error_message: str | None
    total_steps: int
    browser_type: str
    provider_used: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComputerUseSessionListResponse(BaseModel):
    items: list[ComputerUseSessionResponse]
    total: int


# ========== Steps ==========


class ComputerUseStepResponse(BaseModel):
    id: UUID
    session_id: UUID
    step_number: int
    screenshot_path: str | None
    action_type: str
    action_params: dict[str, Any]
    reason: str | None = None
    execution_result: str | None
    execution_ms: int | None
    executed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Mensajes de supervisión ==========


class ComputerUseMessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|agent|system)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ComputerUseMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== WebSocket Protocol ==========


class WSMessageScreenshot(BaseModel):
    type: str = "screenshot"
    data: dict[str, Any]


class WSMessageAction(BaseModel):
    type: str = "action"
    data: dict[str, Any]


class WSMessageStatus(BaseModel):
    type: str = "status"
    data: dict[str, Any]


class WSMessageChat(BaseModel):
    type: str = "chat"
    data: dict[str, Any]


class WSMessageError(BaseModel):
    type: str = "error"
    data: dict[str, Any]


class WSMessageCompleted(BaseModel):
    type: str = "completed"
    data: dict[str, Any]


class WSClientControl(BaseModel):
    type: str = "control"
    action: str = Field(..., pattern="^(pause|resume|stop)$")


class WSClientChat(BaseModel):
    type: str = "chat"
    message: str = Field(..., min_length=1, max_length=2000)


# ========== Orchestrator Integration ==========


class ComputerUseOrchestratorResult(BaseModel):
    action: str = "COMPUTER_USE"
    response: str
    session_id: UUID
    ws_url: str
    task: str
