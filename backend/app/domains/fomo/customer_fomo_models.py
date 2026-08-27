"""Customer FOMO Campaign Models"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid


class CampaignType(str, Enum):
    LIVE_VISITOR_COUNT = "live_visitor_count"
    PURCHASE_NOTIFICATIONS = "purchase_notifications"
    COUNTDOWN_TIMER = "countdown_timer"
    STOCK_SCARCITY = "stock_scarcity"
    CART_ABANDONMENT = "cart_abandonment"
    FLASH_SALE = "flash_sale"
    LIMITED_OFFER = "limited_offer"
    SOCIAL_PROOF = "social_proof"


class WidgetType(str, Enum):
    VISITOR_COUNTER = "visitor_counter"
    PURCHASE_FEED = "purchase_feed"
    COUNTDOWN = "countdown"
    STOCK_BADGE = "stock_badge"
    URGENCY_BANNER = "urgency_banner"
    TRUST_BADGE = "trust_badge"


class AutomationType(str, Enum):
    CART_ABANDONMENT = "cart_abandonment"
    FLASH_SALE = "flash_sale"
    INVENTORY_LOW = "inventory_low"
    TIME_LIMITED = "time_limited"
    COMPETITOR_FOMO = "competitor_fomo"


class CustomerFOMOCampaignConfig(BaseModel):
    campaign_type: CampaignType
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    target_pages: List[str] = []
    target_products: List[str] = []
    messaging: Dict[str, str] = {}
    color_scheme: Dict[str, str] = {"primary": "#FF6B6B", "secondary": "#4ECDC4"}
    enabled_widgets: List[WidgetType] = []
    automations: List[AutomationType] = []


class CustomerFOMOWidgetConfig(BaseModel):
    widget_type: WidgetType
    position: str = "bottom-right"
    size: str = "medium"
    animation: str = "slide-in"
    update_frequency_seconds: int = 10
    colors: Dict[str, str] = {}
    text_overrides: Dict[str, str] = {}
    tracking_enabled: bool = True


class CustomerFOMOAutomationConfig(BaseModel):
    automation_type: AutomationType
    trigger: str
    delay_minutes: int = 0
    channels: List[str] = ["email", "sms"]
    message_templates: Dict[str, str] = {}
    max_frequency_per_user: int = 3
    exclude_returning_customers: bool = False


class CustomerFOMOAnalyticsData(BaseModel):
    date: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: Decimal = Decimal("0.00")
    avg_conversion_lift: Decimal = Decimal("0.00")
    roi: Decimal = Decimal("0.00")
    ctr: float = 0.0
    conversion_rate: float = 0.0


class CustomerFOMOCampaignResponse(BaseModel):
    id: str
    name: str
    campaign_type: CampaignType
    status: str
    performance: Dict[str, Any] = {}
    widgets_count: int = 0
    automations_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerFOMOEventData(BaseModel):
    event_type: str
    user_id: Optional[str] = None
    product_id: Optional[str] = None
    value: Optional[float] = None
    metadata: Dict[str, Any] = {}


class FOMOCampaignTemplate(BaseModel):
    name: str
    description: str
    campaign_type: CampaignType
    preset_config: CustomerFOMOCampaignConfig
    widgets: List[CustomerFOMOWidgetConfig]
    automations: List[CustomerFOMOAutomationConfig]
    expected_conversion_lift: float
    setup_time_minutes: int


# SQLAlchemy Models
class CustomerFOMOCampaign:
    __tablename__ = "customer_fomo_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business.id"), nullable=False)
    name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), nullable=False)
    status = Column(String(20), default="draft")
    config = Column(JSONB, nullable=False)
    performance = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class CustomerFOMOWidget:
    __tablename__ = "customer_fomo_widgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("customer_fomo_campaigns.id"))
    widget_type = Column(String(50), nullable=False)
    config = Column(JSONB, nullable=False)
    embed_code = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class CustomerFOMOEvent:
    __tablename__ = "customer_fomo_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("customer_fomo_campaigns.id"))
    event_type = Column(String(50), nullable=False)
    data = Column(JSONB, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)


class CustomerFOMOAutomation:
    __tablename__ = "customer_fomo_automations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("customer_fomo_campaigns.id"))
    automation_type = Column(String(50), nullable=False)
    trigger = Column(String(100), nullable=False)
    config = Column(JSONB, nullable=False)
    active = Column(Boolean, default=True)
    executions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class CustomerFOMOAnalytics:
    __tablename__ = "customer_fomo_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("customer_fomo_campaigns.id"))
    date = Column(String(10), nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    avg_conversion_lift = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
