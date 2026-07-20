"""Business Context Service"""

import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BusinessContext, BusinessType, SalesModel, GeographicReach, PresenceType
from .schemas import (
    BusinessContextCreate, BusinessContextUpdate, BusinessContextRead,
    ReachAnalysis, ChannelGapAnalysis, BusinessContextWizardState, BusinessContextWizardStep
)


class BusinessContextService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_context(self, user_id: uuid.UUID, business_id: Optional[uuid.UUID] = None) -> BusinessContext:
        query = select(BusinessContext).where(BusinessContext.user_id == user_id)
        if business_id:
            query = query.where(BusinessContext.business_id == business_id)
        result = await self.db.execute(query)
        ctx = result.scalar_one_or_none()
        if not ctx:
            ctx = BusinessContext(user_id=user_id, business_id=business_id)
            self.db.add(ctx)
            await self.db.commit()
            await self.db.refresh(ctx)
        return ctx

    async def update_context(self, user_id: uuid.UUID, context_id: uuid.UUID, data: BusinessContextUpdate) -> Optional[BusinessContext]:
        result = await self.db.execute(
            select(BusinessContext).where(BusinessContext.id == context_id, BusinessContext.user_id == user_id)
        )
        ctx = result.scalar_one_or_none()
        if not ctx:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ctx, key, value)
        await self.db.commit()
        await self.db.refresh(ctx)
        return ctx

    async def detect_context_from_business_data(self, user_id: uuid.UUID, business_id: uuid.UUID) -> BusinessContext:
        """Auto-detect business context from existing data."""
        ctx = await self.get_or_create_context(user_id, business_id)

        # Detect from catalog
        try:
            from app.domains.catalog.models import Product
            result = await self.db.execute(
                select(Product).where(Product.business_id == business_id).limit(10)
            )
            products = result.scalars().all()
            if products:
                # Determine business type from products
                has_digital = any(p.is_digital for p in products if hasattr(p, 'is_digital'))
                has_physical = any(not getattr(p, 'is_digital', False) for p in products)
                if has_digital and not has_physical:
                    ctx.business_type = BusinessType.DIGITAL_PRODUCTS
                elif has_physical:
                    ctx.business_type = BusinessType.PHYSICAL_PRODUCTS
        except Exception:
            pass

        # Detect from channels
        try:
            from app.domains.channels.models import ChannelConnection
            result = await self.db.execute(
                select(ChannelConnection).where(ChannelConnection.business_id == business_id)
            )
            channels = result.scalars().all()
            configured = {}
            for ch in channels:
                configured[ch.platform] = ch.status == "active"
            ctx.channels_configured = {**ctx.channels_configured, **configured}
        except Exception:
            pass

        # Detect from business model
        try:
            from app.domains.businesses.models import Business
            biz = await self.db.get(Business, business_id)
            if biz:
                ctx.city = getattr(biz, 'city', None) or ctx.city
                ctx.country = getattr(biz, 'country', None) or ctx.country
                ctx.industry = getattr(biz, 'industry', None) or ctx.industry
        except Exception:
            pass

        # Detect from orders
        try:
            from app.domains.orders.models import Order
            result = await self.db.execute(
                select(Order).where(Order.business_id == business_id).order_by(Order.created_at.desc()).limit(50)
            )
            orders = result.scalars().all()
            if orders:
                amounts = [o.total_amount for o in orders if getattr(o, 'total_amount', None)]
                if amounts:
                    avg = sum(amounts) / len(amounts)
                    ctx.average_ticket = int(avg)
                if len(orders) > 10:
                    ctx.sales_model = SalesModel.B2C
        except Exception:
            pass

        await self.db.commit()
        await self.db.refresh(ctx)
        return ctx

    async def analyze_reach(self, user_id: uuid.UUID, context_id: uuid.UUID) -> ReachAnalysis:
        ctx = await self.get_or_create_context(user_id, None)
        if ctx.id != context_id:
            result = await self.db.execute(
                select(BusinessContext).where(BusinessContext.id == context_id, BusinessContext.user_id == user_id)
            )
            ctx = result.scalar_one_or_none() or ctx

        current = ctx.geographic_reach.value if ctx.geographic_reach else "local"

        # Determine recommended reach
        if ctx.business_type in (BusinessType.SOFTWARE, BusinessType.DIGITAL_PRODUCTS):
            recommended = "global"
        elif ctx.business_type == BusinessType.CONSULTING:
            recommended = "national" if ctx.country == "Argentina" else "cross_border"
        elif ctx.presence_type == PresenceType.LOCAL_PHYSICAL:
            recommended = "regional"
        else:
            recommended = "national"

        local_seo = ctx.presence_type in (PresenceType.LOCAL_PHYSICAL, PresenceType.HYBRID) or ctx.has_physical_location
        cross_border = recommended in ("cross_border", "global")

        shipping_recs = []
        if ctx.does_delivery and not ctx.shipping_configured:
            shipping_recs.append("Configurar al menos 2 carriers de envío")
        if cross_border:
            shipping_recs.append("Activar envío internacional con DHL/FedEx")
        if ctx.presence_type == PresenceType.LOCAL_PHYSICAL:
            shipping_recs.append("Configurar envío local express (mismo día)")

        platform_recs = []
        if ctx.business_type == BusinessType.PHYSICAL_PRODUCTS:
            platform_recs.extend(["MercadoLibre", "Shopify", "Instagram Shopping"])
        elif ctx.business_type == BusinessType.FOOD_BEVERAGE:
            platform_recs.extend(["Rappi/UberEats", "Instagram", "Google Maps"])
        elif ctx.business_type in (BusinessType.SERVICES, BusinessType.CONSULTING):
            platform_recs.extend(["LinkedIn", "Calendly", "Google Local Ads"])
        elif ctx.business_type == BusinessType.SOFTWARE:
            platform_recs.extend(["Product Hunt", "LinkedIn Ads", "Google Search"])

        market_size = "pequeño" if current == "local" else "mediano" if current == "regional" else "grande" if current == "national" else "masivo"

        return ReachAnalysis(
            current_reach=current,
            recommended_reach=recommended,
            local_seo_priority=local_seo,
            cross_border_opportunity=cross_border,
            shipping_recommendations=shipping_recs,
            platform_recommendations=platform_recs,
            estimated_addressable_market=market_size,
        )

    async def analyze_channel_gaps(self, user_id: uuid.UUID, context_id: uuid.UUID) -> List[ChannelGapAnalysis]:
        ctx = await self.get_or_create_context(user_id, None)
        if ctx.id != context_id:
            result = await self.db.execute(
                select(BusinessContext).where(BusinessContext.id == context_id, BusinessContext.user_id == user_id)
            )
            ctx = result.scalar_one_or_none() or ctx

        all_channels = {
            "instagram": ("critical", "instagram_launch", "Presencia visual obligatoria"),
            "facebook": ("high", "meta_ads_funnel", "Comunidad y ads"),
            "whatsapp": ("critical", "full_automation_setup", "Canal de venta directa"),
            "shopify": ("high", "instagram_launch", "Tienda propia"),
            "mercadolibre": ("high", "cross_border_expansion", "Marketplace local"),
            "tiktok": ("medium", "tiktok_viral_launch", "Alcance orgánico"),
            "google_business": ("high", "google_local_seo", "SEO local"),
            "linkedin": ("medium", "consulting_b2b_lead_gen", "B2B networking"),
            "email": ("high", "email_marketing_setup", "Retención y nurturing"),
            "meta_ads": ("high", "meta_ads_funnel", "Publicidad pagada"),
            "google_ads": ("medium", "google_ads_search", "Búsqueda activa"),
        }

        gaps = []
        configured = ctx.channels_configured or {}
        for channel, (priority, playbook, impact) in all_channels.items():
            is_configured = configured.get(channel, False)
            if not is_configured:
                gaps.append(ChannelGapAnalysis(
                    channel=channel,
                    is_configured=False,
                    priority=priority,
                    impact_estimate=impact,
                    setup_difficulty="medium",
                    recommended_playbook=playbook,
                ))
        return sorted(gaps, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x.priority])

    async def generate_recommended_playbooks(self, user_id: uuid.UUID, context_id: uuid.UUID) -> List[str]:
        ctx = await self.get_or_create_context(user_id, None)
        if ctx.id != context_id:
            result = await self.db.execute(
                select(BusinessContext).where(BusinessContext.id == context_id, BusinessContext.user_id == user_id)
            )
            ctx = result.scalar_one_or_none() or ctx

        recs = []

        # Base playbooks for everyone
        if not ctx.channels_configured.get("instagram"):
            recs.append("instagram_launch")
        if not ctx.channels_configured.get("google_business"):
            recs.append("google_local_seo")

        # Business type specific
        type_playbooks = {
            BusinessType.PHYSICAL_PRODUCTS: ["cart_recovery_sequence", "meta_ads_funnel", "cross_border_expansion"],
            BusinessType.DIGITAL_PRODUCTS: ["lead_nurture_sequence", "google_ads_search", "email_marketing_setup"],
            BusinessType.SERVICES: ["pro_services_portfolio", "google_local_seo", "lead_nurture_sequence"],
            BusinessType.CONSULTING: ["consulting_b2b_lead_gen", "consulting_calendly_booking", "linkedin_outreach"],
            BusinessType.SOFTWARE: ["saas_product_hunt_launch", "saas_demo_scheduling", "google_ads_search"],
            BusinessType.FOOD_BEVERAGE: ["restaurant_delivery_apps", "restaurant_instagram_food", "restaurant_local_seo"],
            BusinessType.FASHION_BEAUTY: ["fashion_visual_content", "fashion_influencer_collabs", "instagram_launch"],
            BusinessType.HEALTH_WELLNESS: ["wellness_appointment_booking", "wellness_testimonial_videos", "google_local_seo"],
            BusinessType.HOME_DECOR: ["home_decor_pinterest_seo", "home_decor_before_after", "google_local_seo"],
            BusinessType.HANDCRAFT: ["handcraft_etsy_setup", "handcraft_mercadolibre", "handcraft_storytelling"],
        }
        if ctx.business_type in type_playbooks:
            recs.extend(type_playbooks[ctx.business_type])

        # Geographic reach
        reach_playbooks = {
            GeographicReach.LOCAL: ["google_local_seo", "meta_ads_funnel"],
            GeographicReach.REGIONAL: ["regional_expansion", "meta_ads_funnel"],
            GeographicReach.NATIONAL: ["national_expansion", "shipping_carriers_full"],
            GeographicReach.CROSS_BORDER: ["cross_border_latam", "cross_border_shipping"],
            GeographicReach.GLOBAL: ["global_expansion", "payment_processors_setup"],
        }
        if ctx.geographic_reach in reach_playbooks:
            recs.extend(reach_playbooks[ctx.geographic_reach])

        # Remove duplicates while preserving order
        seen = set()
        return [x for x in recs if not (x in seen or seen.add(x))]

    async def get_wizard_state(self, user_id: uuid.UUID, context_id: uuid.UUID) -> BusinessContextWizardState:
        ctx = await self.get_or_create_context(user_id, None)
        if ctx.id != context_id:
            result = await self.db.execute(
                select(BusinessContext).where(BusinessContext.id == context_id, BusinessContext.user_id == user_id)
            )
            ctx = result.scalar_one_or_none() or ctx

        steps = [
            BusinessContextWizardStep(
                step=1,
                title="Tipo de Negocio",
                description="¿Qué vendes y cómo?",
                fields=[
                    {"name": "business_type", "type": "select", "label": "Tipo de negocio", "options": [t.value for t in BusinessType]},
                    {"name": "sales_model", "type": "select", "label": "Modelo de venta", "options": [t.value for t in SalesModel]},
                    {"name": "industry", "type": "text", "label": "Industria/nicho"},
                ],
                is_completed=ctx.business_type != BusinessType.OTHER,
            ),
            BusinessContextWizardStep(
                step=2,
                title="Alcance y Ubicación",
                description="¿Dónde operas y a dónde quieres llegar?",
                fields=[
                    {"name": "geographic_reach", "type": "select", "label": "Alcance geográfico", "options": [t.value for t in GeographicReach]},
                    {"name": "presence_type", "type": "select", "label": "Tipo de presencia", "options": [t.value for t in PresenceType]},
                    {"name": "city", "type": "text", "label": "Ciudad"},
                    {"name": "country", "type": "text", "label": "País"},
                ],
                is_completed=ctx.city is not None and ctx.geographic_reach != GeographicReach.LOCAL,
            ),
            BusinessContextWizardStep(
                step=3,
                title="Canales Actuales",
                description="¿Qué plataformas ya tenés configuradas?",
                fields=[
                    {"name": "channels_configured", "type": "multi_select", "label": "Canales activos", "options": ["instagram", "facebook", "whatsapp", "tiktok", "linkedin", "shopify", "mercadolibre", "amazon"]},
                    {"name": "website_configured", "type": "boolean", "label": "¿Tenés sitio web?"},
                ],
                is_completed=bool(ctx.channels_configured),
            ),
            BusinessContextWizardStep(
                step=4,
                title="Marketing y Ads",
                description="¿Ya invertís en publicidad?",
                fields=[
                    {"name": "ads_configured", "type": "multi_select", "label": "Ads activos", "options": ["meta_ads", "google_ads", "tiktok_ads"]},
                    {"name": "seo_configured", "type": "boolean", "label": "¿SEO configurado?"},
                    {"name": "email_marketing_configured", "type": "boolean", "label": "¿Email marketing activo?"},
                ],
                is_completed=bool(ctx.ads_configured),
            ),
            BusinessContextWizardStep(
                step=5,
                title="Logística",
                description="¿Cómo entregás tus productos/servicios?",
                fields=[
                    {"name": "does_delivery", "type": "boolean", "label": "¿Hacés envíos?"},
                    {"name": "shipping_configured", "type": "multi_select", "label": "Carriers configurados", "options": ["andreani", "dhl", "fedex", "ups", "oca", "correo_argentino"]},
                    {"name": "shipping_radius_km", "type": "number", "label": "Radio de envío (km)"},
                ],
                is_completed=not ctx.does_delivery or bool(ctx.shipping_configured),
            ),
        ]

        current_step = 1
        for s in steps:
            if not s.is_completed:
                current_step = s.step
                break
        else:
            current_step = 5

        return BusinessContextWizardState(
            current_step=current_step,
            total_steps=5,
            steps=steps,
            context=BusinessContextRead.model_validate(ctx),
        )
