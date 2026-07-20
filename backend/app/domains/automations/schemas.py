"""Automations Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ========== Workflow Schemas ==========

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    visual_data: Optional[Dict[str, Any]] = None
    status: str = "draft"


class WorkflowCreate(WorkflowBase):
    business_id: UUID


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    visual_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


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
    actions: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowVariantCreate(WorkflowVariantBase):
    is_control: bool = False
    is_active: Optional[bool] = True


class WorkflowVariantUpdate(BaseModel):
    variant_name: Optional[str] = None
    traffic_split: Optional[int] = None
    actions: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    is_control: Optional[bool] = None


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
    variants: List[Dict[str, Any]] = Field(default_factory=list)


# ========== Email Template Schemas ==========

class EmailTemplateBase(BaseModel):
    name: str
    subject: str
    body_html: Optional[str] = None
    body_text: str
    variables: List[str] = Field(default_factory=list)
    category: Optional[str] = None


class EmailTemplateCreate(EmailTemplateBase):
    business_id: UUID


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


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
    template_id: Optional[UUID] = None
    subject_override: Optional[str] = None
    body_override: Optional[str] = None
    condition: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)


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
    description: Optional[str] = None
    category: Optional[str] = None
    status: str = "draft"
    trigger_type: Optional[str] = None


class EmailSequenceCreate(EmailSequenceBase):
    business_id: UUID
    steps: List[SequenceStepCreate] = Field(default_factory=list)


class EmailSequenceResponse(EmailSequenceBase):
    id: UUID
    business_id: UUID
    is_active: bool
    sent_count: int
    opens_count: int
    clicks_count: int
    created_at: datetime
    updated_at: datetime
    steps: List[SequenceStepResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class EmailSequenceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    trigger_type: Optional[str] = None
    is_active: Optional[bool] = None


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
    last_sent_at: Optional[datetime] = None
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
    subject: Optional[str] = None
    status: str = "pending"


class SequenceEmailLogResponse(SequenceEmailLogBase):
    id: UUID
    business_id: UUID
    tracking_token: str
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
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
    sent_trend: List[Dict[str, Any]] = Field(default_factory=list)


# ========== Chatbot Rule Schemas ==========

class ChatbotRuleBase(BaseModel):
    name: str
    intent: str
    keywords: List[str] = Field(default_factory=list)
    response_template: str
    response_type: str = "text"
    priority: int = 0
    channel_filter: List[str] = Field(default_factory=list)
    requires_human: bool = False


class ChatbotRuleCreate(ChatbotRuleBase):
    business_id: UUID


class ChatbotRuleUpdate(BaseModel):
    name: Optional[str] = None
    intent: Optional[str] = None
    keywords: Optional[List[str]] = None
    response_template: Optional[str] = None
    response_type: Optional[str] = None
    priority: Optional[int] = None
    channel_filter: Optional[List[str]] = None
    requires_human: Optional[bool] = None
    is_active: Optional[bool] = None


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
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    generation_config: Dict[str, Any] = Field(default_factory=dict)
    source_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    text_content: Optional[str] = None
    variations: List[Dict[str, Any]] = Field(default_factory=list)
    platform: Optional[str] = None
    purpose: Optional[str] = None
    performance_data: Dict[str, Any] = Field(default_factory=dict)
    approval_status: str = "pending"
    feedback_notes: Optional[str] = None
    generation_cost: int = 0
    ai_model_used: Optional[str] = None


class GeneratedContentCreate(BaseModel):
    catalog_item_id: Optional[UUID] = None
    content_type: str
    agent_slug: str
    prompt: Optional[str] = None
    generation_config: Dict[str, Any] = Field(default_factory=dict)
    platform: Optional[str] = None
    purpose: Optional[str] = None


class GeneratedContentResponse(GeneratedContentBase):
    id: UUID
    business_id: UUID
    catalog_item_id: Optional[UUID] = None
    workflow_execution_id: Optional[UUID] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentCalendarBase(BaseModel):
    scheduled_at: datetime
    timezone: str = "UTC"
    status: str = "scheduled"
    platform: str
    content_format: str
    caption: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    alt_text: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    cta_text: Optional[str] = None
    link_in_bio: Optional[str] = None
    auto_publish: bool = False
    requires_approval: bool = True
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class ContentCalendarCreate(ContentCalendarBase):
    generated_content_id: Optional[UUID] = None
    catalog_item_id: Optional[UUID] = None
    channel_connection_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None


class ContentCalendarResponse(ContentCalendarBase):
    id: UUID
    business_id: UUID
    generated_content_id: Optional[UUID] = None
    catalog_item_id: Optional[UUID] = None
    channel_connection_id: Optional[UUID] = None
    published_at: Optional[datetime] = None
    published_by: Optional[UUID] = None
    external_post_id: Optional[str] = None
    external_url: Optional[str] = None
    reach: int = 0
    impressions: int = 0
    engagement: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: int = 0
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentGenerationRequest(BaseModel):
    catalog_item_id: Optional[UUID] = None
    content_type: str  # image, video, copy, carousel, thumbnail
    agent_slug: Optional[str] = None
    platform: Optional[str] = None
    purpose: Optional[str] = None
    prompt_override: Optional[str] = None
    generation_config: Dict[str, Any] = Field(default_factory=dict)


class ContentGenerationResponse(BaseModel):
    task_id: Optional[str] = None
    content_id: Optional[UUID] = None
    status: str
    message: str
    prompt: Optional[str] = None
    preview: Optional[str] = None
