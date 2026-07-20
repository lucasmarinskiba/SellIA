"""Computer Use Agents — Schemas Extendidos"""

from datetime import datetime
from typing import Optional, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


# ========== Templates ==========

class ComputerUseTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    task_description: str = Field(..., min_length=1, max_length=2000)
    start_url: Optional[str] = Field(None, max_length=2048)
    tags: list[str] = Field(default_factory=list)
    is_public: bool = False


class ComputerUseTemplateResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    task_description: str
    start_url: Optional[str]
    tags: list[str]
    is_public: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComputerUseTemplateListResponse(BaseModel):
    items: list[ComputerUseTemplateResponse]
    total: int


# ========== Scheduled Tasks ==========

class ComputerUseScheduledTaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    task_description: str = Field(..., min_length=1, max_length=2000)
    start_url: Optional[str] = Field(None, max_length=2048)
    cron_expression: str = Field(..., min_length=1, max_length=100)
    timezone: str = "America/Argentina/Buenos_Aires"
    provider: str = "auto"
    max_steps: int = 30


class ComputerUseScheduledTaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    task_description: str
    start_url: Optional[str]
    cron_expression: str
    timezone: str
    provider: str
    is_active: bool
    max_steps: int
    last_run_at: Optional[datetime]
    last_session_id: Optional[UUID]
    total_runs: int
    success_count: int
    fail_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComputerUseScheduledTaskListResponse(BaseModel):
    items: list[ComputerUseScheduledTaskResponse]
    total: int


# ========== Annotations ==========

class ComputerUseAnnotationCreate(BaseModel):
    step_number: int = Field(..., ge=1)
    content: str = Field(..., min_length=1, max_length=2000)
    x_coordinate: Optional[int] = None
    y_coordinate: Optional[int] = None
    color: str = "#f59e0b"


class ComputerUseAnnotationResponse(BaseModel):
    id: UUID
    session_id: UUID
    step_number: int
    user_id: UUID
    content: str
    x_coordinate: Optional[int]
    y_coordinate: Optional[int]
    color: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Browser Profiles ==========

class ComputerUseBrowserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    viewport_width: int = 1280
    viewport_height: int = 720
    user_agent: Optional[str] = None
    locale: str = "es-ES"
    timezone_id: str = "America/Argentina/Buenos_Aires"
    cookies: list[dict] = Field(default_factory=list)
    local_storage: dict[str, Any] = Field(default_factory=dict)
    geolocation: Optional[dict[str, float]] = None
    is_default: bool = False


class ComputerUseBrowserProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    viewport_width: int
    viewport_height: int
    user_agent: Optional[str]
    locale: str
    timezone_id: str
    cookies: list[dict]
    local_storage: dict[str, Any]
    geolocation: Optional[dict[str, float]]
    is_default: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Proxy Configs ==========

class ComputerUseProxyConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    proxy_type: str = Field("http", pattern="^(http|https|socks5)$")
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    rotation_url: Optional[str] = None


class ComputerUseProxyConfigResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    proxy_type: str
    host: str
    port: int
    username: Optional[str]
    rotation_url: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    use_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Session Sharing ==========

class ComputerUseSessionShareCreate(BaseModel):
    shared_with_email: Optional[str] = None
    shared_with_user_id: Optional[UUID] = None
    permission: str = Field("view", pattern="^(view|comment|control)$")
    expires_days: Optional[int] = Field(None, ge=1, le=365)


class ComputerUseSessionShareResponse(BaseModel):
    id: UUID
    session_id: UUID
    shared_by_user_id: UUID
    shared_with_user_id: Optional[UUID]
    shared_with_email: Optional[str]
    permission: str
    token: str
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Batch Jobs ==========

class ComputerUseBatchJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    task_description: str = Field(..., min_length=1, max_length=2000)
    urls: list[str] = Field(..., min_length=1)
    provider: str = "auto"
    max_steps_per_url: int = 30
    concurrency: int = 3


class ComputerUseBatchJobResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    task_description: str
    urls: list[str]
    provider: str
    max_steps_per_url: int
    concurrency: int
    status: str
    completed_count: int
    failed_count: int
    total_count: int
    results_summary: dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ========== Session Tags ==========

class ComputerUseSessionTagCreate(BaseModel):
    tag: str = Field(..., min_length=1, max_length=50)
    color: str = "#3b82f6"


class ComputerUseSessionTagResponse(BaseModel):
    id: UUID
    session_id: UUID
    tag: str
    color: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Webhooks ==========

class ComputerUseSessionBookmarkCreate(BaseModel):
    step_number: int = Field(..., ge=1)
    label: str = Field(..., min_length=1, max_length=200)
    color: str = "#3b82f6"


class ComputerUseSessionBookmarkResponse(BaseModel):
    id: UUID
    session_id: UUID
    step_number: int
    user_id: UUID
    label: str
    color: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComputerUseSessionNoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    is_pinned: bool = False


class ComputerUseSessionNoteResponse(BaseModel):
    id: UUID
    session_id: UUID
    user_id: UUID
    content: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComputerUseWebhookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: HttpUrl
    events: list[str] = Field(default_factory=list)
    secret: Optional[str] = None


class ComputerUseWebhookResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    url: str
    events: list[str]
    is_active: bool
    last_triggered_at: Optional[datetime]
    last_status_code: Optional[int]
    failure_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Export / Replay ==========

class ComputerUseExportRequest(BaseModel):
    format: str = Field("pdf", pattern="^(pdf|csv|json)$")
    include_screenshots: bool = True
    step_range: Optional[tuple[int, int]] = None  # (start, end)


class ComputerUseReplayStep(BaseModel):
    step_number: int
    screenshot_url: Optional[str]
    action_type: str
    action_params: dict[str, Any]
    reason: Optional[str]
    execution_result: Optional[str]
    execution_ms: Optional[int]
    annotations: list[ComputerUseAnnotationResponse] = Field(default_factory=list)


class ComputerUseReplayResponse(BaseModel):
    session_id: UUID
    task_description: str
    status: str
    total_steps: int
    steps: list[ComputerUseReplayStep]


# ========== Analytics ==========

class ComputerUseAnalyticsSummary(BaseModel):
    total_sessions: int
    completed_sessions: int
    failed_sessions: int
    stopped_sessions: int
    avg_steps_per_session: float
    avg_session_duration_seconds: Optional[float]
    most_used_provider: Optional[str]
    most_common_action: Optional[str]
    sessions_today: int
    sessions_this_week: int
    sessions_this_month: int


class ComputerUseSessionFilter(BaseModel):
    status: Optional[str] = None
    tag: Optional[str] = None
    provider: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None


# ========== Import Schemas (whitelist para evitar mass assignment) ==========

class ComputerUseTemplateImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    task_description: str = Field(..., min_length=1, max_length=2000)
    start_url: Optional[str] = Field(None, max_length=2048)
    tags: list[str] = Field(default_factory=list)
    is_public: bool = False


class ComputerUseBrowserProfileImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    viewport_width: int = 1280
    viewport_height: int = 720
    user_agent: Optional[str] = Field(None, max_length=500)
    locale: str = "es-ES"
    timezone_id: str = "America/Argentina/Buenos_Aires"
    cookies: list[Any] = Field(default_factory=list)
    local_storage: dict[str, Any] = Field(default_factory=dict)
    geolocation: Optional[dict[str, Any]] = None
    is_default: bool = False


class ComputerUseProxyConfigImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    proxy_type: str = "http"
    host: str = Field(..., max_length=255)
    port: int = Field(..., ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=255)
    password_encrypted: Optional[str] = Field(None, max_length=500)
    rotation_url: Optional[str] = Field(None, max_length=2048)
    is_active: bool = True


class ComputerUseWebhookImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., max_length=2048)
    events: list[str] = Field(default_factory=list)
    secret: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
