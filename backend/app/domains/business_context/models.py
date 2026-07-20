"""Business Context Models"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class BusinessType(str, enum.Enum):
    PHYSICAL_PRODUCTS = "physical_products"      # Vende productos físicos
    DIGITAL_PRODUCTS = "digital_products"        # Ebooks, cursos, templates
    SERVICES = "services"                        # Servicios profesionales
    CONSULTING = "consulting"                    # Consultoría / coaching
    SOFTWARE = "software"                        # Apps, SaaS, sistemas
    FOOD_BEVERAGE = "food_beverage"             # Restaurante, café, delivery
    FASHION_BEAUTY = "fashion_beauty"           # Ropa, accesorios, belleza
    HEALTH_WELLNESS = "health_wellness"         # Salud, fitness, bienestar
    HOME_DECOR = "home_decor"                   # Decoración, muebles, hogar
    HANDCRAFT = "handcraft"                     # Artesanías, productos hechos a mano
    OTHER = "other"


class SalesModel(str, enum.Enum):
    B2C = "b2c"                                  # Directo al consumidor
    B2B = "b2b"                                  # Empresa a empresa
    B2B2C = "b2b2c"                             # Híbrido
    D2C = "d2c"                                  # Direct to consumer (marca propia)
    MARKETPLACE = "marketplace"                  # Vende en marketplaces


class GeographicReach(str, enum.Enum):
    LOCAL = "local"                              # Barrio/ciudad
    REGIONAL = "regional"                        # Provincia/estado/región
    NATIONAL = "national"                        # Todo el país
    CROSS_BORDER = "cross_border"               # Países vecinos
    GLOBAL = "global"                            # Mundial


class PresenceType(str, enum.Enum):
    LOCAL_PHYSICAL = "local_physical"           # Tienda física
    HOME_OFFICE = "home_office"                 # Trabaja desde casa
    SHOWROOM = "showroom"                       # Showroom/atelier
    ONLINE_ONLY = "online_only"                 # 100% online
    HYBRID = "hybrid"                           # Mixto


class BusinessContext(Base):
    __tablename__ = "business_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)

    # Core business identity
    business_type = Column(Enum(BusinessType), nullable=False, default=BusinessType.OTHER)
    sales_model = Column(Enum(SalesModel), nullable=False, default=SalesModel.B2C)
    geographic_reach = Column(Enum(GeographicReach), nullable=False, default=GeographicReach.LOCAL)
    presence_type = Column(Enum(PresenceType), nullable=False, default=PresenceType.ONLINE_ONLY)

    # Detailed info
    industry = Column(String(100), nullable=True)                    # Ej: "indumentaria femenina"
    target_audience = Column(Text, nullable=True)                    # Ej: "mujeres 25-40, clase media-alta"
    value_proposition = Column(Text, nullable=True)                  # Propuesta de valor única
    price_range = Column(String(50), nullable=True)                  # "low", "medium", "premium", "luxury"
    average_ticket = Column(Integer, nullable=True)                  # Ticket promedio en centavos/moneda local

    # Location (for local SEO and shipping)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True, default="Argentina")
    address = Column(Text, nullable=True)
    has_physical_location = Column(Boolean, default=False)
    serves_home_office = Column(Boolean, default=False)
    does_delivery = Column(Boolean, default=False)
    does_pickup = Column(Boolean, default=False)
    shipping_radius_km = Column(Integer, nullable=True)              # Radio de envío en km

    # Current channels status
    channels_configured = Column(JSONB, default=dict)                # {"instagram": true, "shopify": false, ...}
    ads_configured = Column(JSONB, default=dict)                     # {"meta_ads": false, "google_ads": false, ...}
    shipping_configured = Column(JSONB, default=dict)                # {"andreani": false, "dhl": false, ...}
    website_configured = Column(Boolean, default=False)
    seo_configured = Column(Boolean, default=False)
    email_marketing_configured = Column(Boolean, default=False)

    # Goals
    primary_goal = Column(String(50), nullable=True)                 # "more_sales", "more_leads", "more_traffic", "brand_awareness", "expansion"
    monthly_revenue_goal = Column(Integer, nullable=True)            # Meta mensual en moneda local
    monthly_leads_goal = Column(Integer, nullable=True)
    target_countries = Column(JSONB, default=list)                   # Para cross-border

    # AI-generated insights
    ai_recommended_playbooks = Column(JSONB, default=list)
    ai_priority_actions = Column(JSONB, default=list)
    ai_brand_voice = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
