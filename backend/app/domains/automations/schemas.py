"""Automations Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ========== Workflow Schemas ==========

class WorkflowBase(BaseModel):
    name: str
    description: str | None = None
    trigger_type: str
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    visual_data: dict[str, Any] | None = None
    status: str = "draft"


class WorkflowCreate(WorkflowBase):
    business_id: UUID


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_type: str | None = None
    trigger_config: dict[str, Any] | None = None
    actions: list[dict[str, Any]] | None = None
    visual_data: dict[str, Any] | None = None
    status: str | None = None
    is_active: bool | None = None


class WorkflowResponse(WorkflowBase):
    id: UUID
    business_id: UUID
    execution_count: int
    conversion_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Workflow Variant Schemas ==========

class WorkflowVariantBase(BaseModel):
    variant_name: str
    traffic_split: int = 50
    actions: list[dict[str, Any]] = Field(default_factory=list)


class WorkflowVariantCreate(WorkflowVariantBase):
    is_control: bool = False
    is_active: bool | None = True


class WorkflowVariantUpdate(BaseModel):
    variant_name: str | None = None
    traffic_split: int | None = None
    actions: list[dict[str, Any]] | None = None
    is_active: bool | None = None
    is_control: bool | None = None


class WorkflowVariantResponse(WorkflowVariantBase):
    id: UUID
    workflow_id: UUID
    business_id: UUID
    execution_count: int
    conversion_count: int
    is_control: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowABTestResult(BaseModel):
    workflow_id: UUID
    total_executions: int
    total_conversions: int
    overall_conversion_rate: float
    variants: list[dict[str, Any]] = Field(default_factory=list)


# ========== Email Template Schemas ==========

class EmailTemplateBase(BaseModel):
    name: str
    subject: str
    body_html: str | None = None
    body_text: str
    variables: list[str] = Field(default_factory=list)
    category: str | None = None


class EmailTemplateCreate(EmailTemplateBase):
    business_id: UUID


class EmailTemplateUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    variables: list[str] | None = None
    category: str | None = None
    is_active: bool | None = None


class EmailTemplateResponse(EmailTemplateBase):
    id: UUID
    business_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Email Sequence Schemas ==========

class SequenceStepBase(BaseModel):
    step_order: int
    delay_hours: int = 0
    delay_minutes: int = 0
    template_id: UUID | None = None
    subject_override: str | None = None
    body_override: str | None = None
    condition: str | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class SequenceStepCreate(SequenceStepBase):
    pass


class SequenceStepResponse(SequenceStepBase):
    id: UUID
    sequence_id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailSequenceBase(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None
    status: str = "draft"
    trigger_type: str | None = None


class EmailSequenceCreate(EmailSequenceBase):
    business_id: UUID
    steps: list[SequenceStepCreate] = Field(default_factory=list)


class EmailSequenceResponse(EmailSequenceBase):
    id: UUID
    business_id: UUID
    is_active: bool
    sent_count: int
    opens_count: int
    clicks_count: int
    created_at: datetime
    updated_at: datetime
    steps: list[SequenceStepResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class EmailSequenceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    status: str | None = None
    trigger_type: str | None = None
    is_active: bool | None = None


# ========== Sequence Subscription Schemas ==========

class SequenceSubscriptionBase(BaseModel):
    sequence_id: UUID
    conversation_id: UUID
    current_step_index: int = 0
    status: str = "active"


class SequenceSubscriptionResponse(SequenceSubscriptionBase):
    id: UUID
    business_id: UUID
    started_at: datetime
    last_sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Sequence Email Log Schemas ==========

class SequenceEmailLogBase(BaseModel):
    subscription_id: UUID
    sequence_id: UUID
    step_id: UUID
    conversation_id: UUID
    recipient_email: str
    subject: str | None = None
    status: str = "pending"


class SequenceEmailLogResponse(SequenceEmailLogBase):
    id: UUID
    business_id: UUID
    tracking_token: str
    sent_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Sequence Analytics Schemas ==========

class SequenceAnalytics(BaseModel):
    sequence_id: UUID
    total_subscribers: int
    total_sent: int
    total_opens: int
    total_clicks: int
    open_rate: float
    click_rate: float
    sent_trend: list[dict[str, Any]] = Field(default_factory=list)


# ========== Chatbot Rule Schemas ==========

class ChatbotRuleBase(BaseModel):
    name: str
    intent: str
    keywords: list[str] = Field(default_factory=list)
    response_template: str
    response_type: str = "text"
    priority: int = 0
    channel_filter: list[str] = Field(default_factory=list)
    requires_human: bool = False


class ChatbotRuleCreate(ChatbotRuleBase):
    business_id: UUID


class ChatbotRuleUpdate(BaseModel):
    name: str | None = None
    intent: str | None = None
    keywords: list[str] | None = None
    response_template: str | None = None
    response_type: str | None = None
    priority: int | None = None
    channel_filter: list[str] | None = None
    requires_human: bool | None = None
    is_active: bool | None = None


class ChatbotRuleResponse(ChatbotRuleBase):
    id: UUID
    business_id: UUID
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Content Generation Schemas ==========

class GeneratedContentBase(BaseModel):
    content_type: str
    agent_slug: str
    status: str = "pending"
    prompt: str | None = None
    negative_prompt: str | None = None
    generation_config: dict[str, Any] = Field(default_factory=dict)
    source_url: str | None = None
    thumbnail_url: str | None = None
    text_content: str | None = None
    variations: list[dict[str, Any]] = Field(default_factory=list)
    platform: str | None = None
    purpose: str | None = None
    performance_data: dict[str, Any] = Field(default_factory=dict)
    approval_status: str = "pending"
    feedback_notes: str | None = None
    generation_cost: int = 0
    ai_model_used: str | None = None


class GeneratedContentCreate(BaseModel):
    catalog_item_id: UUID | None = None
    content_type: str
    agent_slug: str
    prompt: str | None = None
    generation_config: dict[str, Any] = Field(default_factory=dict)
    platform: str | None = None
    purpose: str | None = None


class GeneratedContentResponse(GeneratedContentBase):
    id: UUID
    business_id: UUID
    catalog_item_id: UUID | None = None
    workflow_execution_id: UUID | None = None
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentCalendarBase(BaseModel):
    scheduled_at: datetime
    timezone: str = "UTC"
    status: str = "scheduled"
    platform: str
    content_format: str
    caption: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    alt_text: str | None = None
    media_urls: list[str] = Field(default_factory=list)
    cta_text: str | None = None
    link_in_bio: str | None = None
    auto_publish: bool = False
    requires_approval: bool = True
    extra_data: dict[str, Any] = Field(default_factory=dict)


class ContentCalendarCreate(ContentCalendarBase):
    generated_content_id: UUID | None = None
    catalog_item_id: UUID | None = None
    channel_connection_id: UUID | None = None
    workflow_id: UUID | None = None


class ContentCalendarResponse(ContentCalendarBase):
    id: UUID
    business_id: UUID
    generated_content_id: UUID | None = None
    catalog_item_id: UUID | None = None
    channel_connection_id: UUID | None = None
    published_at: datetime | None = None
    published_by: UUID | None = None
    external_post_id: str | None = None
    external_url: str | None = None
    reach: int = 0
    impressions: int = 0
    engagement: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: int = 0
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentGenerationRequest(BaseModel):
    catalog_item_id: UUID | None = None
    content_type: str  # image, video, copy, carousel, thumbnail
    agent_slug: str | None = None
    platform: str | None = None
    purpose: str | None = None
    prompt_override: str | None = None
    generation_config: dict[str, Any] = Field(default_factory=dict)


class ContentGenerationResponse(BaseModel):
    task_id: str | None = None
    content_id: UUID | None = None
    status: str
    message: str
    prompt: str | None = None
    preview: str | None = None


# ========== Automation Toggles Schemas ==========

class AutomationToggleBase(BaseModel):
    toggle_key: str
    category: str  # "agent" | "automation" | "feature" | "integration"
    display_name: str
    description: str | None = None
    icon: str | None = None


class AutomationToggleCreate(AutomationToggleBase):
    is_enabled: bool = True
    monthly_limit: int | None = None


class AutomationToggleUpdate(BaseModel):
    is_enabled: bool | None = None
    monthly_limit: int | None = None


class AutomationToggleResponse(AutomationToggleBase):
    id: UUID
    business_id: UUID
    is_enabled: bool
    monthly_limit: int | None
    current_month_usage: int
    enabled_at: datetime | None
    disabled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToggleAuditLogResponse(BaseModel):
    id: UUID
    toggle_id: UUID
    action: str
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    changed_by_email: str | None
    reason: str | None
    leads_affected: int | None
    estimated_impact_pct: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToggleDashboardStats(BaseModel):
    category: str
    total: int
    enabled: int
    usage: int


class ToggleDashboardResponse(BaseModel):
    by_category: list[ToggleDashboardStats]
    timestamp: datetime


# ========== Toggle Schedule Schemas ==========

class ToggleScheduleBase(BaseModel):
    toggle_id: UUID
    start_time: datetime
    timezone: str = "UTC"
    recurring: bool = False
    recurrence_rule: str | None = None
    action: str  # "enable" | "disable"
    reason: str | None = None


class ToggleScheduleCreate(ToggleScheduleBase):
    pass


class ToggleScheduleUpdate(BaseModel):
    start_time: datetime | None = None
    timezone: str | None = None
    recurring: bool | None = None
    recurrence_rule: str | None = None
    action: str | None = None
    reason: str | None = None
    is_active: bool | None = None


class ToggleScheduleResponse(ToggleScheduleBase):
    id: UUID
    business_id: UUID
    is_active: bool
    last_executed_at: datetime | None
    next_execution_at: datetime | None
    execution_count: int
    failed_count: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Toggle Notification Schemas ==========

class ToggleNotificationRuleBase(BaseModel):
    toggle_id: UUID
    event_type: str  # "enabled" | "disabled" | "usage_limit_reached" | "usage_threshold" | "schedule_executed"
    usage_threshold_pct: int | None = None
    notify_via_email: bool = True
    notify_via_webhook: bool = False
    notify_via_inapp: bool = True
    email_recipients: list[str] = Field(default_factory=list)
    webhook_url: str | None = None
    webhook_secret: str | None = None


class ToggleNotificationRuleCreate(ToggleNotificationRuleBase):
    pass


class ToggleNotificationRuleUpdate(BaseModel):
    event_type: str | None = None
    usage_threshold_pct: int | None = None
    notify_via_email: bool | None = None
    notify_via_webhook: bool | None = None
    notify_via_inapp: bool | None = None
    email_recipients: list[str] | None = None
    webhook_url: str | None = None
    webhook_secret: str | None = None
    is_active: bool | None = None


class ToggleNotificationRuleResponse(ToggleNotificationRuleBase):
    id: UUID
    business_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToggleNotificationLogResponse(BaseModel):
    id: UUID
    toggle_id: UUID
    rule_id: UUID
    event_type: str
    channels_sent: list[str]
    status: str
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
