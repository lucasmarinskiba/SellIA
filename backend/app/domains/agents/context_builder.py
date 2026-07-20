"""Context Builder — Construye contexto completo del negocio para agentes IA.

Recolecta catálogo, configuración del negocio, BusinessContext enriquecido,
instrucciones personalizadas y las inyecta en el system prompt.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.catalogs.models import CatalogItem
from app.domains.businesses.models import Business, DEFAULT_CONFIGS
from app.domains.business_context.models import BusinessContext
from app.domains.agents.models import AgentConfig, AgentPersonality
from app.domains.agents.business_type_registry import BusinessTypeRegistry


class BusinessContextBuilder:
    """Construye contexto enriquecido de un negocio para agentes IA."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_context(
        self,
        business_id: Any,
        personality_id: Optional[Any] = None,
        personality_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Construir contexto completo de negocio."""
        result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        if not business:
            return {}

        context = {
            "name": business.name,
            "type": business.type.value if business.type else "unknown",
            "description": business.description or "",
        }

        # Configuración específica por tipo de negocio
        business_config = business.config or {}
        context["config"] = business_config

        # Catálogo activo
        catalog_items = await self._get_catalog_summary(business_id)
        context["catalog_summary"] = catalog_items
        context["catalog_count"] = len(catalog_items)

        # BusinessContext enriquecido (tipo específico: fashion, software, etc.)
        enriched = await self._get_business_context(business_id)
        if enriched:
            context["enriched"] = enriched

        # Configuración del agente (si existe)
        if personality_id or personality_slug:
            agent_config = await self._get_agent_config(
                business_id, personality_id, personality_slug
            )
            if agent_config:
                context["agent_config"] = agent_config

        return context

    async def _get_catalog_summary(self, business_id: Any) -> List[Dict[str, Any]]:
        """Obtener resumen del catálogo del negocio."""
        result = await self.db.execute(
            select(CatalogItem).where(
                CatalogItem.business_id == business_id,
                CatalogItem.is_available == True,
                CatalogItem.is_active == True,
            )
        )
        items = result.scalars().all()

        summary = []
        for item in items:
            summary.append({
                "name": item.name,
                "type": item.type.value if item.type else "unknown",
                "price": float(item.price) if item.price else 0,
                "currency": item.currency or "ARS",
                "description": (item.description or "")[:200],
                "stock": item.stock,
                "tags": item.tags or [],
            })
        return summary

    async def _get_business_context(self, business_id: Any) -> Optional[Dict[str, Any]]:
        """Cargar BusinessContext enriquecido si existe."""
        result = await self.db.execute(
            select(BusinessContext).where(
                BusinessContext.business_id == business_id,
                BusinessContext.is_active == True,
            )
        )
        bc = result.scalar_one_or_none()
        if not bc:
            return None

        return {
            "business_type": bc.business_type.value if bc.business_type else None,
            "sales_model": bc.sales_model.value if bc.sales_model else None,
            "geographic_reach": bc.geographic_reach.value if bc.geographic_reach else None,
            "presence_type": bc.presence_type.value if bc.presence_type else None,
            "industry": bc.industry,
            "target_audience": bc.target_audience,
            "value_proposition": bc.value_proposition,
            "price_range": bc.price_range,
            "average_ticket": bc.average_ticket,
            "city": bc.city,
            "state_province": bc.state_province,
            "country": bc.country,
            "has_physical_location": bc.has_physical_location,
            "does_delivery": bc.does_delivery,
            "does_pickup": bc.does_pickup,
            "shipping_radius_km": bc.shipping_radius_km,
            "channels_configured": bc.channels_configured or {},
            "ads_configured": bc.ads_configured or {},
            "shipping_configured": bc.shipping_configured or {},
            "website_configured": bc.website_configured,
            "seo_configured": bc.seo_configured,
            "email_marketing_configured": bc.email_marketing_configured,
            "primary_goal": bc.primary_goal,
            "monthly_revenue_goal": bc.monthly_revenue_goal,
            "monthly_leads_goal": bc.monthly_leads_goal,
            "target_countries": bc.target_countries or [],
            "ai_recommended_playbooks": bc.ai_recommended_playbooks or [],
            "ai_priority_actions": bc.ai_priority_actions or [],
            "ai_brand_voice": bc.ai_brand_voice,
        }

    async def _get_agent_config(
        self,
        business_id: Any,
        personality_id: Optional[Any] = None,
        personality_slug: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Obtener configuración personalizada del agente, incluyendo voz experta."""
        from sqlalchemy.orm import joinedload

        query = select(AgentConfig).where(
            AgentConfig.business_id == business_id,
            AgentConfig.is_enabled == True,
        )
        if personality_id:
            query = query.where(AgentConfig.personality_id == personality_id)
        elif personality_slug:
            # Buscar personality por slug primero
            p_result = await self.db.execute(
                select(AgentPersonality).where(AgentPersonality.slug == personality_slug)
            )
            personality = p_result.scalar_one_or_none()
            if personality:
                query = query.where(AgentConfig.personality_id == personality.id)
            else:
                return None
        else:
            return None

        # Eager load voice personality
        query = query.options(joinedload(AgentConfig.voice_personality))

        result = await self.db.execute(query)
        config = result.scalar_one_or_none()
        if not config:
            return None

        voice_slug = None
        if config.voice_personality:
            voice_slug = config.voice_personality.slug

        return {
            "custom_instructions": config.custom_instructions,
            "tone_override": config.tone_override,
            "voice_personality_slug": voice_slug,
            "extra_data": config.extra_data,
        }

    async def build_system_prompt_context(
        self,
        business_id: Any,
        personality_id: Optional[Any] = None,
        personality_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Construir el dict business_context compatible con get_system_prompt."""
        ctx = await self.build_context(business_id, personality_id, personality_slug)

        # Formatear catálogo como string legible
        catalog_str = ""
        if ctx.get("catalog_summary"):
            lines = []
            for item in ctx["catalog_summary"][:10]:  # Max 10 items para no saturar token
                stock_info = f" (Stock: {item['stock']})" if item['stock'] is not None else ""
                lines.append(f"- {item['name']} ({item['type']}) — {item['currency']} {item['price']}{stock_info}: {item['description'][:100]}")
            catalog_str = "\n".join(lines)

        # Extraer custom instructions del agent config
        custom_instructions = None
        voice_personality_slug = None
        if ctx.get("agent_config"):
            custom_instructions = ctx["agent_config"].get("custom_instructions")
            voice_personality_slug = ctx["agent_config"].get("voice_personality_slug")

        # Construir enriched context string
        enriched = ctx.get("enriched", {})
        enriched_str = ""
        if enriched:
            parts = []
            if enriched.get("business_type"):
                parts.append(f"Specific Type: {enriched['business_type']}")
            if enriched.get("industry"):
                parts.append(f"Industry: {enriched['industry']}")
            if enriched.get("target_audience"):
                parts.append(f"Target Audience: {enriched['target_audience']}")
            if enriched.get("value_proposition"):
                parts.append(f"Value Proposition: {enriched['value_proposition']}")
            if enriched.get("sales_model"):
                parts.append(f"Sales Model: {enriched['sales_model']}")
            if enriched.get("geographic_reach"):
                parts.append(f"Geographic Reach: {enriched['geographic_reach']}")
            if enriched.get("presence_type"):
                parts.append(f"Presence: {enriched['presence_type']}")
            if enriched.get("primary_goal"):
                parts.append(f"Primary Goal: {enriched['primary_goal']}")
            if enriched.get("monthly_revenue_goal"):
                parts.append(f"Revenue Goal: {enriched['monthly_revenue_goal']}")
            if enriched.get("average_ticket"):
                parts.append(f"Average Ticket: {enriched['average_ticket']}")
            if enriched.get("does_delivery"):
                parts.append(f"Delivery: yes (radius {enriched.get('shipping_radius_km', '?')}km)")
            if enriched.get("has_physical_location"):
                parts.append("Has physical location")
            if enriched.get("channels_configured"):
                active_channels = [k for k, v in enriched["channels_configured"].items() if v]
                if active_channels:
                    parts.append(f"Active Channels: {', '.join(active_channels)}")
            if enriched.get("ads_configured"):
                active_ads = [k for k, v in enriched["ads_configured"].items() if v]
                if active_ads:
                    parts.append(f"Active Ads: {', '.join(active_ads)}")
            if enriched.get("ai_brand_voice"):
                parts.append(f"Brand Voice: {enriched['ai_brand_voice']}")
            if enriched.get("ai_priority_actions"):
                actions = enriched["ai_priority_actions"]
                if isinstance(actions, list) and actions:
                    parts.append(f"Priority Actions: {', '.join(str(a) for a in actions[:3])}")
            if parts:
                enriched_str = "\n".join(parts)

        # Prompt adaptation según tipo de negocio específico
        prompt_adaptation = ""
        if enriched and enriched.get("business_type"):
            try:
                from app.domains.business_context.models import BusinessType
                bt = BusinessType(enriched["business_type"])
                prompt_adaptation = BusinessTypeRegistry.get_prompt_adaptation(bt)
            except (ValueError, KeyError):
                pass

        return {
            "name": ctx.get("name", ""),
            "type": ctx.get("type", ""),
            "description": ctx.get("description", ""),
            "catalog_summary": catalog_str,
            "custom_instructions": custom_instructions,
            "voice_personality_slug": voice_personality_slug,
            "enriched": enriched_str,
            "prompt_adaptation": prompt_adaptation,
        }
