"""Computer Use Agents — Pydantic Schemas"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ========== Acciones ==========

class ComputerUseAction(BaseModel):
    action_type: str = Field(..., description="Tipo de acción: click, type, scroll, navigate, wait, done, error")
    params: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="", description="Razón por la que se tomó esta acción")


# ========== Sesiones ==========

class ComputerUseSessionCreate(BaseModel):
    task_description: str = Field(..., min_length=1, max_length=2000)
    start_url: Optional[str] = Field(None, max_length=2048)
    business_id: Optional[UUID] = None
    browser_type: str = Field("chromium", pattern="^(chromium|firefox|webkit)$")
    profile_id: Optional[UUID] = None
    proxy_config_id: Optional[UUID] = None
    mode: str = Field("supervised", pattern="^(supervised|autopilot)$")


class ComputerUseSessionUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Optional[dict] = None


class ComputerUseSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    business_id: Optional[UUID]
    task_description: str
    status: str
    current_url: Optional[str]
    result_data: Optional[dict]
    error_message: Optional[str]
    total_steps: int
    browser_type: str
    provider_used: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
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
    screenshot_path: Optional[str]
    action_type: str
    action_params: dict[str, Any]
    reason: Optional[str] = None
    execution_result: Optional[str]
    execution_ms: Optional[int]
    executed_at: Optional[datetime]
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
