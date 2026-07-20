"""
Webhook Pydantic Schemas (v2)
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class WebhookSubscriptionBase(BaseModel):
    url: str
    events: List[str]
    secret: str
    active: bool = True


class WebhookSubscriptionCreate(WebhookSubscriptionBase):
    pass


class WebhookSubscriptionUpdate(BaseModel):
    url: Optional[str] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    active: Optional[bool] = None


class WebhookSubscriptionResponse(WebhookSubscriptionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookDeliveryBase(BaseModel):
    event_type: str
    payload: dict
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    delivered_at: datetime
    retry_count: int
    success: bool


class WebhookDeliveryResponse(WebhookDeliveryBase):
    id: uuid.UUID
    subscription_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
