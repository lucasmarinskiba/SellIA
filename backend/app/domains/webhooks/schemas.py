"""
Webhook Pydantic Schemas (v2)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WebhookSubscriptionBase(BaseModel):
    url: str
    events: list[str]
    secret: str
    active: bool = True


class WebhookSubscriptionCreate(WebhookSubscriptionBase):
    pass


class WebhookSubscriptionUpdate(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    secret: str | None = None
    active: bool | None = None


class WebhookSubscriptionResponse(WebhookSubscriptionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookDeliveryBase(BaseModel):
    event_type: str
    payload: dict
    response_status: int | None = None
    response_body: str | None = None
    delivered_at: datetime
    retry_count: int
    success: bool


class WebhookDeliveryResponse(WebhookDeliveryBase):
    id: uuid.UUID
    subscription_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
