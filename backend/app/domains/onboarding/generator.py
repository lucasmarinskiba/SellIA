"""Onboarding Mágico — Generator de entidades"""

import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import get_logger
from app.domains.businesses.models import Business, BusinessType
from app.domains.business_context.models import BusinessContext as BizCtxModel
from app.domains.catalogs.models import CatalogItem, CatalogItemType
from app.domains.agents.models import AgentPersonality, AgentConfig
from app.domains.automations.models import Workflow
from app.domains.onboarding.schemas import BusinessDiscovery

logger = get_logger(__name__)


class OnboardingGenerator:
    """Crea automáticamente business, catálogo, agentes y workflows desde un descubrimiento IA."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, user_id: uuid.UUID, discovery: BusinessDiscovery) -> dict[str, Any]:
        """Genera todas las entidades y devuelve resumen."""
        business = await self._create_business(user_id, discovery)
        await self._create_business_context(user_id, business.id, discovery)
        catalog_count = await self._create_catalog(business.id, discovery)
        agent_count = await self._create_agents(business.id, discovery)
        workflow_count = await self._create_workflows(business.id, discovery)

        await self.db.commit()

        return {
            "business_id": business.id,
            "catalog_items_count": catalog_count,
            "agents_count": agent_count,
            "workflows_count": workflow_count,
            "message": f"¡{business.name} está listo! Se crearon {catalog_count} productos, {agent_count} agentes y {workflow_count} automatizaciones.",
        }

    async def _create_business(self, user_id: uuid.UUID, discovery: BusinessDiscovery) -> Business:
        btype = BusinessType.SERVICES
        try:
            btype = BusinessType(discovery.type)
        except ValueError:
            pass

        from app.domains.businesses.models import DEFAULT_CONFIGS
        config = DEFAULT_CONFIGS.get(btype, {})
        if discovery.tone_of_voice:
            config["tone_of_voice"] = discovery.tone_of_voice
        if discovery.brand_colors:
            config["brand_colors"] = discovery.brand_colors
        if discovery.target_audience:
            config["target_audience"] = discovery.target_audience

        business = Business(
            id=uuid.uuid4(),
            user_id=user_id,
            name=discovery.name,
            type=btype,
            description=discovery.description,
            config=config,
        )
        self.db.add(business)
        await self.db.flush()
        logger.info(f"Onboarding: business creado {business.id}")
        return business

    async def _create_business_context(
        self,
        user_id: uuid.UUID,
        business_id: uuid.UUID,
        discovery: BusinessDiscovery,
    ) -> None:
        """Create an initial BusinessContext from onboarding discovery data."""
        # Map generic BusinessType to specific BusinessContext type
        btype_str = discovery.type
        specific_type = BizCtxModel.BusinessType.OTHER
        type_mapping = {
            "services": BizCtxModel.BusinessType.SERVICES,
            "goods": BizCtxModel.BusinessType.PHYSICAL_PRODUCTS,
            "digital": BizCtxModel.BusinessType.DIGITAL_PRODUCTS,
            "mixed": BizCtxModel.BusinessType.OTHER,
        }
        try:
            specific_type = type_mapping.get(btype_str, BizCtxModel.BusinessType.OTHER)
        except Exception:
            pass

        ctx = BizCtxModel(
            id=uuid.uuid4(),
            user_id=user_id,
            business_id=business_id,
            business_type=specific_type,
            sales_model=BizCtxModel.SalesModel.B2C,
            geographic_reach=BizCtxModel.GeographicReach.LOCAL,
            presence_type=BizCtxModel.PresenceType.ONLINE_ONLY,
            target_audience=discovery.target_audience,
            value_proposition=discovery.description,
            industry=discovery.industry or discovery.type,
            is_active=True,
        )
        self.db.add(ctx)
        await self.db.flush()
        logger.info(f"Onboarding: BusinessContext creado para {business_id}")

    async def _create_catalog(self, business_id: uuid.UUID, discovery: BusinessDiscovery) -> int:
        count = 0
        for p in discovery.products:
            item = CatalogItem(
                id=uuid.uuid4(),
                business_id=business_id,
                type=CatalogItemType.SERVICE if discovery.type == "services" else CatalogItemType.PRODUCT,
                name=p.name,
                description=p.description or "",
                price=p.price or 0,
                currency=p.currency or "ARS",
                stock=p.price is not None,
                is_available=True,
                tags=[p.category] if p.category else [],
                extra_data={"category": p.category, "auto_generated": True},
                images=[],
            )
            self.db.add(item)
            count += 1
        await self.db.flush()
        logger.info(f"Onboarding: {count} items de catálogo creados")
        return count

    async def _create_agents(self, business_id: uuid.UUID, discovery: BusinessDiscovery) -> int:
        count = 0
        for agent_def in discovery.suggested_agents:
            slug = agent_def.get("slug", f"agent-{count}")
            result = await self.db.execute(
                select(AgentPersonality).where(AgentPersonality.slug == slug)
            )
            personality = result.scalar_one_or_none()
            if not personality:
                personality = AgentPersonality(
                    id=uuid.uuid4(),
                    slug=slug,
                    name=agent_def.get("name", "Agente IA"),
                    emoji=agent_def.get("emoji", "🤖"),
                    tagline=agent_def.get("tagline", "Listo para ayudar"),
                    description=agent_def.get("description", ""),
                    expertise=agent_def.get("expertise", []),
                    color=agent_def.get("color", "#FF6B35"),
                    display_order=count,
                    is_active=True,
                )
                self.db.add(personality)
                await self.db.flush()

            config = AgentConfig(
                id=uuid.uuid4(),
                business_id=business_id,
                personality_id=personality.id,
                is_enabled=True,
                custom_instructions=agent_def.get("custom_instructions"),
                tone_override=discovery.tone_of_voice,
                extra_data={"auto_generated": True, "source": "onboarding_magico"},
            )
            self.db.add(config)
            count += 1

        logger.info(f"Onboarding: {count} agentes creados")
        return count

    async def _create_workflows(self, business_id: uuid.UUID, discovery: BusinessDiscovery) -> int:
        count = 0
        for wf_def in discovery.suggested_workflows:
            workflow = Workflow(
                id=uuid.uuid4(),
                business_id=business_id,
                name=wf_def.get("name", "Automatización"),
                description=wf_def.get("description", ""),
                trigger_type=wf_def.get("trigger_type", "manual"),
                trigger_config=wf_def.get("trigger_config", {}),
                actions=wf_def.get("actions", []),
                status="active",
                is_active=True,
                execution_count=0,
                conversion_count=0,
            )
            self.db.add(workflow)
            count += 1
        await self.db.flush()
        logger.info(f"Onboarding: {count} workflows creados")
        return count
