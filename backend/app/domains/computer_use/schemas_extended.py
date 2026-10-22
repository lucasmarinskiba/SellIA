"""Computer Use Agents — Schemas Extendidos"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# ========== Templates ==========


class ComputerUseTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    task_description: str = Field(..., min_length=1, max_length=2000)
    start_url: str | None = Field(None, max_length=2048)
    tags: list[str] = Field(default_factory=list)
    is_public: bool = False


class ComputerUseTemplateResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    task_description: str
    start_url: str | None
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
    start_url: str | None = Field(None, max_length=2048)
    cron_expression: str = Field(..., min_length=1, max_length=100)
    timezone: str = "America/Argentina/Buenos_Aires"
    provider: str = "auto"
    max_steps: int = 30


class ComputerUseScheduledTaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    task_description: str
    start_url: str | None
    cron_expression: str
    timezone: str
    provider: str
    is_active: bool
    max_steps: int
    last_run_at: datetime | None
    last_session_id: UUID | None
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
    x_coordinate: int | None = None
    y_coordinate: int | None = None
    color: str = "#f59e0b"


class ComputerUseAnnotationResponse(BaseModel):
    id: UUID
    session_id: UUID
    step_number: int
    user_id: UUID
    content: str
    x_coordinate: int | None
    y_coordinate: int | None
    color: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Browser Profiles ==========


class ComputerUseBrowserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    viewport_width: int = 1280
    viewport_height: int = 720
    user_agent: str | None = None
    locale: str = "es-ES"
    timezone_id: str = "America/Argentina/Buenos_Aires"
    cookies: list[dict] = Field(default_factory=list)
    local_storage: dict[str, Any] = Field(default_factory=dict)
    geolocation: dict[str, float] | None = None
    is_default: bool = False


class ComputerUseBrowserProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    viewport_width: int
    viewport_height: int
    user_agent: str | None
    locale: str
    timezone_id: str
    cookies: list[dict]
    local_storage: dict[str, Any]
    geolocation: dict[str, float] | None
    is_default: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Proxy Configs ==========


class ComputerUseProxyConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    proxy_type: str = Field("http", pattern="^(http|https|socks5)$")
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    username: str | None = None
    password: str | None = None
    rotation_url: str | None = None


class ComputerUseProxyConfigResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    proxy_type: str
    host: str
    port: int
    username: str | None
    rotation_url: str | None
    is_active: bool
    last_used_at: datetime | None
    use_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Session Sharing ==========


class ComputerUseSessionShareCreate(BaseModel):
    shared_with_email: str | None = None
    shared_with_user_id: UUID | None = None
    permission: str = Field("view", pattern="^(view|comment|control)$")
    expires_days: int | None = Field(None, ge=1, le=365)


class ComputerUseSessionShareResponse(BaseModel):
    id: UUID
    session_id: UUID
    shared_by_user_id: UUID
    shared_with_user_id: UUID | None
    shared_with_email: str | None
    permission: str
    token: str
    expires_at: datetime | None
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
    started_at: datetime | None
    completed_at: datetime | None

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
    secret: str | None = None


class ComputerUseWebhookResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    url: str
    events: list[str]
    is_active: bool
    last_triggered_at: datetime | None
    last_status_code: int | None
    failure_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Export / Replay ==========


class ComputerUseExportRequest(BaseModel):
    format: str = Field("pdf", pattern="^(pdf|csv|json)$")
    include_screenshots: bool = True
    step_range: tuple[int, int] | None = None  # (start, end)


class ComputerUseReplayStep(BaseModel):
    step_number: int
    screenshot_url: str | None
    action_type: str
    action_params: dict[str, Any]
    reason: str | None
    execution_result: str | None
    execution_ms: int | None
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
    avg_session_duration_seconds: float | None
    most_used_provider: str | None
    most_common_action: str | None
    sessions_today: int
    sessions_this_week: int
    sessions_this_month: int


class ComputerUseSessionFilter(BaseModel):
    status: str | None = None
    tag: str | None = None
    provider: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = None


# ========== Import Schemas (whitelist para evitar mass assignment) ==========


class ComputerUseTemplateImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    task_description: str = Field(..., min_length=1, max_length=2000)
    start_url: str | None = Field(None, max_length=2048)
    tags: list[str] = Field(default_factory=list)
    is_public: bool = False


class ComputerUseBrowserProfileImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    viewport_width: int = 1280
    viewport_height: int = 720
    user_agent: str | None = Field(None, max_length=500)
    locale: str = "es-ES"
    timezone_id: str = "America/Argentina/Buenos_Aires"
    cookies: list[Any] = Field(default_factory=list)
    local_storage: dict[str, Any] = Field(default_factory=dict)
    geolocation: dict[str, Any] | None = None
    is_default: bool = False


class ComputerUseProxyConfigImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    proxy_type: str = "http"
    host: str = Field(..., max_length=255)
    port: int = Field(..., ge=1, le=65535)
    username: str | None = Field(None, max_length=255)
    password_encrypted: str | None = Field(None, max_length=500)
    rotation_url: str | None = Field(None, max_length=2048)
    is_active: bool = True


class ComputerUseWebhookImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., max_length=2048)
    events: list[str] = Field(default_factory=list)
    secret: str | None = Field(None, max_length=255)
    is_active: bool = True
