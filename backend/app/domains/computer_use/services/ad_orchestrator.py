"""Ad Orchestrator — Auto-generate + launch ads across platforms.

Genera copy + creatives + lanza A/B tests en Meta/Google.
Monitorea performance → optimiza budget automáticamente.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from app.domains.computer_use.integrations import (
    MetaAdsConnector,
    GoogleAdsConnector,
    get_meta_ads_connector,
    get_google_ads_connector,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class AdPlatform(str, Enum):
    """Plataformas de ads soportadas."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    GOOGLE_SEARCH = "google_search"
    GOOGLE_DISPLAY = "google_display"
    TIKTOK = "tiktok"


class AdFormat(str, Enum):
    """Formatos de ads."""
    SINGLE_IMAGE = "single_image"
    CAROUSEL = "carousel"
    VIDEO = "video"
    TEXT_ONLY = "text_only"
    COLLECTION = "collection"


class CopyTone(str, Enum):
    """Tonalidad del copy."""
    URGENT = "urgent"  # Limited time, scarcity
    EDUCATIONAL = "educational"  # Learn, discover
    LIFESTYLE = "lifestyle"  # Aspirational, dream
    DISCOUNT = "discount"  # Price-focused
    SOCIAL_PROOF = "social_proof"  # Testimonials, results


@dataclass
class AdCopy:
    """Variante de ad copy."""

    headline: str  # Max 30 chars
    body: str  # Max 125 chars
    cta: str  # Call to action (Learn More, Shop Now, etc)
    tone: CopyTone
    version: int  # A, B, C, D, E = 1, 2, 3, 4, 5


@dataclass
class AdCreative:
    """Asset creativo para ad."""

    type: str  # image_url, video_url, text_only
    content_url: Optional[str] = None
    description: Optional[str] = None
    dimensions: Optional[str] = None  # 1200x628, 1080x1080, etc


@dataclass
class AdCampaign:
    """Campaña de ads."""

    campaign_id: str
    name: str
    platform: AdPlatform
    format: AdFormat
    copies: List[AdCopy]
    creatives: List[AdCreative]
    target_audience: Dict[str, Any]
    daily_budget: float
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "draft"  # draft, running, paused, completed
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "platform": self.platform.value,
            "format": self.format.value,
            "copies": [
                {
                    "headline": c.headline,
                    "body": c.body,
                    "cta": c.cta,
                    "tone": c.tone.value,
                    "version": c.version,
                }
                for c in self.copies
            ],
            "creatives": len(self.creatives),
            "target_audience": self.target_audience,
            "daily_budget": self.daily_budget,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class AdCopyGenerator:
    """Genera variantes de ad copy."""

    COPY_TEMPLATES = {
        CopyTone.URGENT: {
            "headlines": [
                "⏰ Last {count} spots available",
                "Only {days} days left to get {discount}% off",
                "Don't miss out - ending soon",
                "{count} people bought today",
                "⚡ Limited time offer",
            ],
            "bodies": [
                "Join {count}+ customers who already {result}. Don't be left behind.",
                "Price goes up in {days}. Lock in your rate today.",
                "This deal expires {when}. Secure yours now.",
                "The fastest {time_period} {count} people made this decision.",
                "{percentage}% off for the first {count} customers.",
            ],
            "ctas": ["Claim Your Spot", "Grab Yours Now", "Secure Access", "Lock In Price", "Act Now"],
        },
        CopyTone.EDUCATIONAL: {
            "headlines": [
                "Learn the {topic} secret",
                "Discover how to {benefit}",
                "The ultimate guide to {topic}",
                "Stop struggling with {pain}",
                "Master {skill} in {time}",
            ],
            "bodies": [
                "Free masterclass: {topic}. Expert-led. Actionable. Join {count}+ students.",
                "See exactly how we help {audience} achieve {result}.",
                "Tired of {pain}? Here's the {solution}.",
                "Get the playbook {successful_people} use for {outcome}.",
                "Download: The {topic} blueprint used by {creators}.",
            ],
            "ctas": ["Watch Free", "Learn More", "Get Access", "Download Now", "Enroll Free"],
        },
        CopyTone.LIFESTYLE: {
            "headlines": [
                "Imagine {dream_outcome}",
                "The {luxury} life starts here",
                "Be the person who {achievement}",
                "Your {goal} story begins",
                "{aspirational_statement}",
            ],
            "bodies": [
                "{count}+ people are already living {dream}. What's stopping you?",
                "See how {influencer_type} use {product} to {result}.",
                "Your transformation starts here. {testimonial_preview}.",
                "The {time_period} that changes everything. Real stories from {community}.",
                "Stop dreaming. Start doing. {CTA} today.",
            ],
            "ctas": ["Start My Journey", "See Transformation", "Join Community", "Begin Today", "Get Started"],
        },
        CopyTone.DISCOUNT: {
            "headlines": [
                "{discount}% off {product}",
                "Save {amount} on {category}",
                "{discount}% sale ends soon",
                "Flash sale: {discount}% off everything",
                "Biggest sale of the {time_period}",
            ],
            "bodies": [
                "{discount}% off + free shipping. Code: {code}. Ends {when}.",
                "Save {amount} when you buy {quantity}. Limited time.",
                "Best price guaranteed. {discount}% off for {audience}.",
                "{percentage} of customers save over {amount}.",
                "This price won't last. Stock limited. {discount}% off now.",
            ],
            "ctas": ["Shop Now", "Claim Discount", "Use Code", "Buy Now", "Grab Deal"],
        },
        CopyTone.SOCIAL_PROOF: {
            "headlines": [
                "{count}+ people trust us",
                "{rating}★ rated by {count}+ users",
                "See why {count}+ chose us",
                "{testimonial_short}",
                "Loved by {audience_type}",
            ],
            "bodies": [
                '"{result}" - {user_type}. See {count}+ reviews.',
                "{count}+ customers report {benefit}. Real results.",
                "⭐⭐⭐⭐⭐ {testimonial_full}",
                "Join {count}+ {audience} who {outcome}.",
                "{expert_type} recommend us. Here's why {count}+ agree.",
            ],
            "ctas": ["Read Reviews", "See Stories", "Join {count}+", "Start Free", "Learn How"],
        },
    }

    def __init__(self):
        self.logger = logger

    async def generate_ad_copies(
        self,
        product_info: Dict[str, Any],
        tone: CopyTone,
        count: int = 5,
    ) -> List[AdCopy]:
        """
        Genera múltiples variantes de ad copy.

        Retorna: list de AdCopy con diferentes ángulos.
        """
        templates = self.COPY_TEMPLATES.get(tone, self.COPY_TEMPLATES[CopyTone.URGENT])

        copies = []

        for i in range(min(count, 5)):
            # Seleccionar template elements
            headline = templates["headlines"][i % len(templates["headlines"])]
            body = templates["bodies"][i % len(templates["bodies"])]
            cta = templates["ctas"][i % len(templates["ctas"])]

            # Reemplazar variables
            headline = self._fill_template(headline, product_info)
            body = self._fill_template(body, product_info)
            cta = self._fill_template(cta, product_info)

            copy = AdCopy(
                headline=headline[:30],  # Max 30
                body=body[:125],  # Max 125
                cta=cta,
                tone=tone,
                version=i + 1,
            )

            copies.append(copy)

        self.logger.info(f"Generated {len(copies)} ad copies | tone={tone.value}")

        return copies

    def _fill_template(self, template: str, context: Dict[str, Any]) -> str:
        """Reemplaza variables en template con valores del contexto."""
        replacements = {
            "{product}": context.get("product_name", "product"),
            "{discount}": str(context.get("discount_pct", "20")),
            "{percentage}": str(context.get("discount_pct", "20")),
            "{amount}": f"${context.get('discount_amount', '50')}",
            "{count}": str(context.get("customer_count", "1000")),
            "{days}": str(context.get("urgency_days", "7")),
            "{time_period}": context.get("time_period", "year"),
            "{benefit}": context.get("main_benefit", "succeed"),
            "{result}": context.get("result", "succeeded"),
            "{topic}": context.get("topic", "success"),
            "{pain}": context.get("pain_point", "struggle"),
            "{code}": context.get("promo_code", "SAVE20"),
            "{when}": context.get("deadline", "Friday"),
            "{rating}": str(context.get("rating", "5")),
            "{audience}": context.get("audience", "customers"),
        }

        result = template
        for key, value in replacements.items():
            result = result.replace(key, str(value))

        return result


class AdOrchestrator:
    """Orquestador de ads — lanza campaigns en múltiples plataformas."""

    def __init__(self):
        self.copy_generator = AdCopyGenerator()
        self.logger = logger
        self.campaigns: Dict[str, AdCampaign] = {}  # campaign_id → AdCampaign

        # Real API connectors
        self.meta_ads_connector = (
            get_meta_ads_connector(
                access_token=settings.META_ACCESS_TOKEN,
                ad_account_id=settings.META_AD_ACCOUNT_ID,
            ) if hasattr(settings, 'META_ACCESS_TOKEN') else None
        )
        self.google_ads_connector = (
            get_google_ads_connector(
                client_id=settings.GOOGLE_ADS_CLIENT_ID,
                client_secret=settings.GOOGLE_ADS_CLIENT_SECRET,
                refresh_token=settings.GOOGLE_ADS_REFRESH_TOKEN,
                developer_token=settings.GOOGLE_ADS_DEVELOPER_TOKEN,
                customer_id=settings.GOOGLE_ADS_CUSTOMER_ID,
            ) if hasattr(settings, 'GOOGLE_ADS_DEVELOPER_TOKEN') else None
        )

    async def create_campaign(
        self,
        campaign_name: str,
        product_info: Dict[str, Any],
        platforms: List[AdPlatform],
        daily_budget: float,
        duration_days: int = 7,
        target_audience: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Crea campaign: genera copy + creatives + lanza en plataformas.

        Retorna: (success, campaign_ids)
        """
        campaign_ids = []

        try:
            # 1. Generar copies (5 variantes, tonos rotativos)
            all_copies = []

            for tone in [CopyTone.URGENT, CopyTone.SOCIAL_PROOF, CopyTone.LIFESTYLE]:
                copies = await self.copy_generator.generate_ad_copies(
                    product_info=product_info,
                    tone=tone,
                    count=2,
                )
                all_copies.extend(copies)

            # 2. Generar creatives (placeholder)
            creatives = self._generate_placeholder_creatives()

            # 3. Crear campaigns por plataforma
            for platform in platforms:
                campaign_id = f"camp_{platform.value}_{datetime.utcnow().strftime('%Y%m%d%H%M')}"

                campaign = AdCampaign(
                    campaign_id=campaign_id,
                    name=f"{campaign_name} - {platform.value}",
                    platform=platform,
                    format=self._select_format(platform),
                    copies=all_copies[:5],  # Max 5 copies
                    creatives=creatives,
                    target_audience=target_audience or self._default_audience(),
                    daily_budget=daily_budget,
                    start_date=datetime.utcnow(),
                    end_date=datetime.utcnow() + timedelta(days=duration_days),
                )

                self.campaigns[campaign_id] = campaign
                campaign_ids.append(campaign_id)

                # 4. Lanzar campaign (placeholder)
                await self._launch_campaign(campaign)

            self.logger.info(f"Campaigns created: {len(campaign_ids)} | platforms: {[p.value for p in platforms]}")

            return True, campaign_ids

        except Exception as e:
            self.logger.error(f"Error creating campaign: {e}")
            return False, []

    async def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """Obtiene metrics de performance (placeholder)."""
        campaign = self.campaigns.get(campaign_id)

        if not campaign:
            return {}

        # Placeholder metrics
        return {
            "campaign_id": campaign_id,
            "status": campaign.status,
            "impressions": 10000,
            "clicks": 250,
            "ctr": 0.025,
            "conversions": 15,
            "cpc": 0.80,
            "cpa": 50.00,
            "spend": 200.00,
            "revenue": 750.00,
            "roas": 3.75,
        }

    async def optimize_campaigns(
        self,
        user_id: str,
        campaigns: List[str],
    ) -> Tuple[int, List[str]]:
        """
        Optimiza campaigns basado en performance.

        Pausa underperformers, boosted winners.

        Retorna: (optimizations_made, paused_campaigns)
        """
        paused = []

        for campaign_id in campaigns:
            perf = await self.get_campaign_performance(campaign_id)

            if not perf:
                continue

            # Si ROAS < 2 → pausa
            if perf.get("roas", 0) < 2.0:
                campaign = self.campaigns.get(campaign_id)
                if campaign:
                    campaign.status = "paused"
                    paused.append(campaign_id)

                    self.logger.info(f"Campaign paused (low ROAS): {campaign_id} | roas={perf.get('roas')}")

        return len(paused), paused

    # ── Private Methods ──────────────────────────────────────────

    def _select_format(self, platform: AdPlatform) -> AdFormat:
        """Selecciona formato óptimo por plataforma."""
        if platform == AdPlatform.TIKTOK:
            return AdFormat.VIDEO
        elif platform == AdPlatform.INSTAGRAM:
            return AdFormat.CAROUSEL
        elif platform in (AdPlatform.GOOGLE_SEARCH, AdPlatform.GOOGLE_DISPLAY):
            return AdFormat.SINGLE_IMAGE
        else:
            return AdFormat.SINGLE_IMAGE

    def _generate_placeholder_creatives(self, count: int = 3) -> List[AdCreative]:
        """Genera creatives placeholder."""
        return [
            AdCreative(
                type="image_url",
                content_url=f"https://placeholder.com/1200x628?text=Creative+{i}",
                description=f"Creative variant {i}",
                dimensions="1200x628",
            )
            for i in range(1, count + 1)
        ]

    def _default_audience(self) -> Dict[str, Any]:
        """Audience targeting por defecto."""
        return {
            "age_min": 18,
            "age_max": 65,
            "interests": ["business", "marketing", "sales"],
            "languages": ["en", "es"],
            "regions": ["US", "CA", "MX"],
        }

    async def _launch_campaign(self, campaign: AdCampaign) -> bool:
        """Lanza campaign en plataforma REAL (Meta o Google)."""
        try:
            if campaign.platform in (AdPlatform.FACEBOOK, AdPlatform.INSTAGRAM) and self.meta_ads_connector:
                return await self._launch_meta_campaign(campaign)
            elif campaign.platform in (AdPlatform.GOOGLE_SEARCH, AdPlatform.GOOGLE_DISPLAY) and self.google_ads_connector:
                return await self._launch_google_campaign(campaign)
            else:
                self.logger.warning(f"No connector for platform {campaign.platform.value}")
                campaign.status = "draft"
                return False
        except Exception as e:
            self.logger.error(f"Error launching campaign: {e}")
            campaign.status = "draft"
            return False

    async def _launch_meta_campaign(self, campaign: AdCampaign) -> bool:
        """Lanza en Meta Ads (Facebook/Instagram)."""
        try:
            budget_micros = int(campaign.daily_budget * 100 * 1000)  # Convertir a microdólares

            success, campaign_id = await self.meta_ads_connector.create_campaign(
                campaign_name=campaign.name,
                daily_budget=campaign.daily_budget,
                objective="CONVERSIONS",
            )

            if not success:
                return False

            # Crear adset
            adset_success, adset_id = await self.meta_ads_connector.create_adset(
                campaign_id=campaign_id,
                adset_name=f"AdSet - {campaign.name}",
                daily_budget=campaign.daily_budget,
                targeting=campaign.target_audience,
            )

            if not adset_success:
                return False

            # Crear ads
            for copy in campaign.copies[:3]:  # Max 3 ads por adset
                ad_success, ad_id = await self.meta_ads_connector.create_ad(
                    adset_id=adset_id,
                    ad_name=f"{campaign.name} - v{copy.version}",
                    creative_id=None,  # O usar creative upload
                    headline=copy.headline,
                    body=copy.body,
                    cta_type=copy.cta,
                )

                if not ad_success:
                    self.logger.warning(f"Failed to create ad variant {copy.version}")

            campaign.status = "running"
            campaign.campaign_id = campaign_id

            self.logger.info(f"Meta campaign launched: {campaign_id} | budget: ${campaign.daily_budget}/day")
            return True

        except Exception as e:
            self.logger.error(f"Error launching Meta campaign: {e}")
            return False

    async def _launch_google_campaign(self, campaign: AdCampaign) -> bool:
        """Lanza en Google Ads (Search/Display)."""
        try:
            # Crear campaign
            campaign_success, campaign_id = await self.google_ads_connector.create_search_campaign(
                campaign_name=campaign.name,
                budget_micros=int(campaign.daily_budget * 1_000_000),  # Convertir a microdólares
                keywords=[k for k in campaign.target_audience.get("keywords", [])],
            )

            if not campaign_success:
                return False

            # Crear ad group
            adgroup_success, adgroup_id = await self.google_ads_connector.create_ad_group(
                campaign_id=campaign_id,
                ad_group_name=f"AdGroup - {campaign.name}",
                cpc_bid_micros=int(0.50 * 1_000_000),  # $0.50 CPC default
            )

            if not adgroup_success:
                return False

            # Crear ads
            for copy in campaign.copies[:3]:
                ad_success, ad_id = await self.google_ads_connector.create_text_ad(
                    ad_group_id=adgroup_id,
                    headline1=copy.headline,
                    headline2=f"v{copy.version}",
                    description=copy.body,
                    final_url=campaign.target_audience.get("landing_page_url", "https://yoursite.com"),
                )

                if not ad_success:
                    self.logger.warning(f"Failed to create Google ad variant {copy.version}")

            campaign.status = "running"
            campaign.campaign_id = campaign_id

            self.logger.info(f"Google campaign launched: {campaign_id} | budget: ${campaign.daily_budget}/day")
            return True

        except Exception as e:
            self.logger.error(f"Error launching Google campaign: {e}")
            return False


def get_ad_orchestrator() -> AdOrchestrator:
    return AdOrchestrator()
