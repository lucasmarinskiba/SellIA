"""Phase 10: Business model detection and adaptation."""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BusinessModel(str, Enum):
    PHYSICAL_STORE = "physical_store"
    ONLINE_ONLY = "online_only"
    HYBRID = "hybrid"
    SERVICE_AT_HOME = "service_at_home"
    B2B_CONSULTING = "b2b_consulting"
    MARKETPLACE = "marketplace"
    GLOBAL_ECOMMERCE = "global_ecommerce"
    PROFESSIONAL_SERVICES = "professional_services"
    SUBSCRIPTION = "subscription"
    MARKETPLACE_SELLER = "marketplace_seller"


class Channel(str, Enum):
    GOOGLE_MAPS = "google_maps"
    GOOGLE_SEARCH = "google_search"
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"
    EMAIL = "email"
    MARKETPLACE = "marketplace"
    REFERRALS = "referrals"
    CONTENT_MARKETING = "content_marketing"
    COMMUNITY = "community"
    OFFLINE_NETWORKING = "offline_networking"


@dataclass
class BusinessProfile:
    business_id: str
    name: str
    description: str
    model: BusinessModel
    primary_location: Optional[str] = None
    service_radius_km: Optional[int] = None
    is_b2b: bool = False
    is_b2c: bool = True
    target_audience: str = ""
    channels: List[Channel] = field(default_factory=list)
    primary_channel: Optional[Channel] = None
    revenue_model: str = "one_time"  # one_time, subscription, hybrid
    average_ticket_size: Optional[float] = None
    avg_sales_cycle_days: Optional[int] = None
    has_physical_location: bool = False
    has_online_presence: bool = False
    languages: List[str] = field(default_factory=lambda: ["es"])
    competitor_count: int = 0
    market_size_estimate: str = "unknown"
    growth_potential: str = "medium"  # low, medium, high
    custom_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LeadSource:
    name: str
    channel: Channel
    description: str
    estimated_leads_per_month: int
    effort_level: str  # low, medium, high
    cost_estimate: str  # free, low, medium, high
    setup_time_days: int


class BusinessModelDetector:
    def __init__(self):
        self.model_keywords = {
            BusinessModel.PHYSICAL_STORE: [
                "tienda", "store", "local", "retail", "boutique", "shop", "comercio"
            ],
            BusinessModel.ONLINE_ONLY: [
                "ecommerce", "online store", "digital", "web shop", "tienda online"
            ],
            BusinessModel.SERVICE_AT_HOME: [
                "plomero", "pintor", "electricista", "servicios hogar", "fontanería",
                "limpieza", "reparación", "instalación", "mantenimiento"
            ],
            BusinessModel.B2B_CONSULTING: [
                "consultoría", "asesoramiento", "consultor", "coaching", "training",
                "agencia", "software development", "business consultant"
            ],
            BusinessModel.PROFESSIONAL_SERVICES: [
                "abogado", "contador", "psicólogo", "médico", "dentista", "consultor"
            ],
            BusinessModel.SUBSCRIPTION: [
                "suscripción", "subscription", "membresía", "SaaS", "software as service"
            ]
        }

    def detect_model(
        self, business_description: str, website: str = "", socials: Dict = None
    ) -> BusinessProfile:
        """Detecta modelo de negocio"""

        combined_text = f"{business_description} {website}".lower()
        if socials:
            combined_text += f" {str(socials)}".lower()

        model = self._match_model(combined_text)

        channels = self._determine_channels(model, business_description)
        primary_channel = channels[0] if channels else Channel.GOOGLE_SEARCH

        location = self._extract_location(business_description)
        is_b2b = self._detect_b2b(combined_text)

        profile = BusinessProfile(
            business_id="auto_detected",
            name="Negocio",
            description=business_description,
            model=model,
            primary_location=location,
            service_radius_km=self._estimate_service_radius(model, location),
            is_b2b=is_b2b,
            is_b2c=not is_b2b,
            channels=channels,
            primary_channel=primary_channel,
            has_physical_location=model in [
                BusinessModel.PHYSICAL_STORE,
                BusinessModel.HYBRID
            ],
            has_online_presence=model in [
                BusinessModel.ONLINE_ONLY,
                BusinessModel.HYBRID,
                BusinessModel.SUBSCRIPTION
            ]
        )

        logger.info(f"Business model detected: {model.value}")
        return profile

    def _match_model(self, text: str) -> BusinessModel:
        """Match texto a modelo de negocio"""
        scores = {}

        for model, keywords in self.model_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[model] = score

        best_match = max(scores, key=scores.get) if scores else BusinessModel.HYBRID
        logger.debug(f"Model match scores: {scores}")
        return best_match

    def _determine_channels(
        self, model: BusinessModel, description: str
    ) -> List[Channel]:
        """Determina canales de venta por modelo"""

        channels_by_model = {
            BusinessModel.PHYSICAL_STORE: [
                Channel.GOOGLE_MAPS,
                Channel.INSTAGRAM,
                Channel.WHATSAPP,
                Channel.FACEBOOK_ADS,
                Channel.REFERRALS
            ],
            BusinessModel.ONLINE_ONLY: [
                Channel.GOOGLE_SEARCH,
                Channel.GOOGLE_ADS,
                Channel.CONTENT_MARKETING,
                Channel.INSTAGRAM,
                Channel.EMAIL
            ],
            BusinessModel.SERVICE_AT_HOME: [
                Channel.GOOGLE_MAPS,
                Channel.GOOGLE_SEARCH,
                Channel.WHATSAPP,
                Channel.REFERRALS,
                Channel.FACEBOOK_ADS
            ],
            BusinessModel.B2B_CONSULTING: [
                Channel.LINKEDIN,
                Channel.EMAIL,
                Channel.CONTENT_MARKETING,
                Channel.OFFLINE_NETWORKING,
                Channel.GOOGLE_ADS
            ],
            BusinessModel.PROFESSIONAL_SERVICES: [
                Channel.LINKEDIN,
                Channel.GOOGLE_MAPS,
                Channel.REFERRALS,
                Channel.EMAIL,
                Channel.CONTENT_MARKETING
            ],
            BusinessModel.SUBSCRIPTION: [
                Channel.CONTENT_MARKETING,
                Channel.EMAIL,
                Channel.GOOGLE_ADS,
                Channel.COMMUNITY,
                Channel.REFERRALS
            ],
            BusinessModel.MARKETPLACE: [
                Channel.MARKETPLACE,
                Channel.INSTAGRAM,
                Channel.GOOGLE_ADS,
                Channel.EMAIL
            ],
            BusinessModel.GLOBAL_ECOMMERCE: [
                Channel.MARKETPLACE,
                Channel.GOOGLE_SEARCH,
                Channel.CONTENT_MARKETING,
                Channel.EMAIL,
                Channel.INSTAGRAM
            ],
            BusinessModel.MARKETPLACE_SELLER: [
                Channel.MARKETPLACE,
                Channel.EMAIL,
                Channel.INSTAGRAM,
                Channel.FACEBOOK_ADS
            ]
        }

        return channels_by_model.get(model, [Channel.GOOGLE_SEARCH, Channel.INSTAGRAM])

    def _extract_location(self, description: str) -> Optional[str]:
        """Extrae ubicación de descripción"""
        # Simple extraction - en producción usar geocoding
        keywords = ["en ", "de ", "en la ciudad de ", "ubicado en"]
        for kw in keywords:
            if kw in description.lower():
                idx = description.lower().find(kw)
                location = description[idx + len(kw):idx + len(kw) + 50].split(",")[0].strip()
                if location and len(location) < 50:
                    return location
        return None

    def _estimate_service_radius(self, model: BusinessModel, location: str) -> Optional[int]:
        """Estima radio de servicio por modelo"""
        if model == BusinessModel.SERVICE_AT_HOME:
            return 10  # km
        elif model == BusinessModel.PHYSICAL_STORE:
            return 5
        elif model == BusinessModel.HYBRID:
            return 20
        return None

    def _detect_b2b(self, text: str) -> bool:
        """Detecta si es B2B"""
        b2b_keywords = ["b2b", "empresa", "empresa a empresa", "empresas", "b2c a b2b",
                        "soluciones empresariales", "corporativo", "business"]
        return any(kw in text for kw in b2b_keywords)

    def get_relevant_channels(self, profile: BusinessProfile) -> List[LeadSource]:
        """Retorna lead sources relevantes"""
        sources = []

        if Channel.GOOGLE_MAPS in profile.channels:
            sources.append(LeadSource(
                name="Google Maps Optimization",
                channel=Channel.GOOGLE_MAPS,
                description="Local search + reviews + direct contact",
                estimated_leads_per_month=20,
                effort_level="medium",
                cost_estimate="free",
                setup_time_days=3
            ))

        if Channel.GOOGLE_SEARCH in profile.channels:
            sources.append(LeadSource(
                name="SEO + Organic Search",
                channel=Channel.GOOGLE_SEARCH,
                description="Rank for relevant keywords",
                estimated_leads_per_month=15,
                effort_level="high",
                cost_estimate="free",
                setup_time_days=30
            ))

        if Channel.LINKEDIN in profile.channels:
            sources.append(LeadSource(
                name="LinkedIn Outreach",
                channel=Channel.LINKEDIN,
                description="Direct messaging + connection building",
                estimated_leads_per_month=10,
                effort_level="medium",
                cost_estimate="low",
                setup_time_days=2
            ))

        if Channel.INSTAGRAM in profile.channels:
            sources.append(LeadSource(
                name="Instagram + Reels",
                channel=Channel.INSTAGRAM,
                description="Visual content + engagement",
                estimated_leads_per_month=8,
                effort_level="medium",
                cost_estimate="free",
                setup_time_days=1
            ))

        if Channel.WHATSAPP in profile.channels:
            sources.append(LeadSource(
                name="WhatsApp Business",
                channel=Channel.WHATSAPP,
                description="Direct messaging + automation",
                estimated_leads_per_month=5,
                effort_level="low",
                cost_estimate="free",
                setup_time_days=1
            ))

        if Channel.MARKETPLACE in profile.channels:
            sources.append(LeadSource(
                name="Marketplace Listings",
                channel=Channel.MARKETPLACE,
                description="Amazon, eBay, Shopify, Mercado Libre, etc",
                estimated_leads_per_month=30,
                effort_level="medium",
                cost_estimate="medium",
                setup_time_days=5
            ))

        if Channel.EMAIL in profile.channels:
            sources.append(LeadSource(
                name="Email Outreach",
                channel=Channel.EMAIL,
                description="Personalized cold email + nurture",
                estimated_leads_per_month=12,
                effort_level="medium",
                cost_estimate="low",
                setup_time_days=3
            ))

        return sources
