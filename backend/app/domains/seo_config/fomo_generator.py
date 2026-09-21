"""FOMO copy generation for publication links.

Integrates with brand_transformation.FOMOEngineAgent to generate
FOMO-optimized descriptions for each PublicationLink.
"""

import json
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.agent_guard import SEOAgentGuard
from app.domains.seo_config.brain_toggles import FOMO_PUBLICATIONS, is_brain_capability_enabled
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO, SEOConfig
from app.domains.brand_transformation.service import FOMOEngineAgent

logger = get_logger(__name__)


class PublicationFOMOGenerator:
    """Generate FOMO copy for publication links."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_fomo_generation_enabled(self, business_id: UUID) -> bool:
        """Check if FOMO generation is enabled: global SEO toggle AND the
        `automation.fomo_publications` Brain Map node (either one off stops it)."""
        result = await self.db.execute(
            select(SEOConfig).where(SEOConfig.business_id == business_id)
        )
        config = result.scalar_one_or_none()
        if config is not None and not config.global_seo_enabled:
            return False
        return await is_brain_capability_enabled(self.db, business_id, FOMO_PUBLICATIONS)

    async def _may_generate(self, business_id: UUID, link: PublicationLink) -> bool:
        """The full on/off check for generating FOMO for one link: the link's own
        switch, global SEO, the platform's SEO switch, and the Brain Map nodes
        (fomo_publications + the platform itself). Every generation path —
        cadence, auto-rotation, multi-language — goes through this."""
        if not link.seo_enabled:
            return False
        return await SEOAgentGuard(self.db).can_run_seo_agent(
            business_id, "fomo_engine",
            platform_id=link.connection_id, platform_name=link.platform_source,
        )

    async def generate_fomo_for_link(
        self, business_id: UUID, link: PublicationLink
    ) -> PublicationLinkFOMO | None:
        """Generate FOMO copy for a single publication link."""
        if not await self._may_generate(business_id, link):
            logger.info(f"FOMO generation skipped for link {link.id}: SEO disabled")
            return None

        try:
            # Call FOMOEngineAgent to generate FOMO copy
            # Pass the link URL + platform as context
            agent = FOMOEngineAgent(self.db)
            profile = {"what_they_sell": "Products and services"}  # Minimal profile

            context = {
                "url": link.url,
                "title": link.title,
                "platform": link.platform_source,
            }

            extra = f"Generate FOMO copy specifically for this publication: {link.title} ({link.url}). Focus on urgency and scarcity appropriate for {link.platform_source}."

            # Generate FOMO playbook (which includes mechanisms, triggers, copy hooks)
            fomo_playbook = await agent.run(business_id, profile, context, extra)

            # Parse the playbook to extract FOMO elements
            fomo_score = getattr(fomo_playbook, "fomo_intensity_score", 70)
            urgency = None
            scarcity = None
            social_proof = None
            call_to_action = "Get it now before it's gone"

            # Try to extract from mechanisms
            if hasattr(fomo_playbook, "mechanisms") and fomo_playbook.mechanisms:
                mechanisms = fomo_playbook.mechanisms
                if isinstance(mechanisms, dict):
                    urgency = mechanisms.get("urgency_trigger")
                    scarcity = mechanisms.get("scarcity_message")
                    social_proof = mechanisms.get("social_proof")
                    call_to_action = mechanisms.get("cta", call_to_action)

            # Generate full copy (summary of the playbook)
            generated_copy = f"{scarcity or ''}\n{social_proof or ''}\n{call_to_action}"

            # Save FOMO entry
            fomo_entry = PublicationLinkFOMO(
                business_id=business_id,
                link_id=link.id,
                urgency_trigger=urgency or "limited_time",
                social_proof_element=social_proof,
                scarcity_message=scarcity,
                call_to_action=call_to_action,
                generated_copy=generated_copy.strip(),
                fomo_score=float(fomo_score) if fomo_score else 70.0,
            )

            self.db.add(fomo_entry)
            await self.db.commit()
            await self.db.refresh(fomo_entry)

            logger.info(f"Generated FOMO copy for link {link.id} (score: {fomo_score})")
            return fomo_entry

        except Exception as e:
            logger.error(f"Error generating FOMO for link {link.id}: {str(e)[:200]}")
            return None

    async def generate_fomo_for_business(self, business_id: UUID) -> dict:
        """Generate FOMO copy for all active publication links in a business."""
        # Get all active links
        result = await self.db.execute(
            select(PublicationLink).where(
                PublicationLink.business_id == business_id,
                PublicationLink.seo_enabled == True,
            )
        )
        links = result.scalars().all()

        generated = 0
        failed = 0

        for link in links:
            fomo_entry = await self.generate_fomo_for_link(business_id, link)
            if fomo_entry:
                generated += 1
            else:
                failed += 1

        return {
            "business_id": str(business_id),
            "links_processed": len(links),
            "fomo_generated": generated,
            "failed": failed,
        }

    async def get_latest_fomo(self, link_id: UUID) -> PublicationLinkFOMO | None:
        """Get the most recent FOMO copy for a link."""
        result = await self.db.execute(
            select(PublicationLinkFOMO)
            .where(PublicationLinkFOMO.link_id == link_id)
            .order_by(PublicationLinkFOMO.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def generate_fomo_copy(
        self,
        business_id: UUID,
        link_id: UUID,
        platform: str,
        force_urgency: str | None = None,
        language: str = "es",
    ) -> PublicationLinkFOMO | None:
        """Generate FOMO copy with optional urgency override and language support."""
        # Get link
        result = await self.db.execute(
            select(PublicationLink).where(PublicationLink.id == link_id)
        )
        link = result.scalar_one_or_none()
        if not link:
            return None
        if not await self._may_generate(business_id, link):
            logger.info(f"FOMO generation skipped for link {link_id}: SEO disabled")
            return None

        try:
            agent = FOMOEngineAgent(self.db)
            profile = {"what_they_sell": "Products and services"}

            context = {
                "url": link.url,
                "title": link.title,
                "platform": platform,
                "language": language,
            }

            urgency_instruction = ""
            if force_urgency:
                urgency_instruction = f"\nForce urgency trigger: {force_urgency}"

            language_instruction = ""
            if language.lower() == "en":
                language_instruction = "\nGenerate in English."
            elif language.lower() == "pt":
                language_instruction = "\nGenerate in Portuguese (Brazilian)."

            extra = f"Generate FOMO copy for: {link.title} ({link.url}). Platform: {platform}.{urgency_instruction}{language_instruction}"

            fomo_playbook = await agent.run(business_id, profile, context, extra)

            fomo_score = getattr(fomo_playbook, "fomo_intensity_score", 70)
            urgency = force_urgency or getattr(fomo_playbook, "urgency_trigger", "limited_time")
            scarcity = None
            social_proof = None
            call_to_action = "Get it now before it's gone"

            if hasattr(fomo_playbook, "mechanisms") and fomo_playbook.mechanisms:
                mechanisms = fomo_playbook.mechanisms
                if isinstance(mechanisms, dict):
                    scarcity = mechanisms.get("scarcity_message")
                    social_proof = mechanisms.get("social_proof")
                    call_to_action = mechanisms.get("cta", call_to_action)

            generated_copy = f"{scarcity or ''}\n{social_proof or ''}\n{call_to_action}".strip()

            fomo_entry = PublicationLinkFOMO(
                business_id=business_id,
                link_id=link_id,
                urgency_trigger=urgency,
                social_proof_element=social_proof,
                scarcity_message=scarcity,
                call_to_action=call_to_action,
                generated_copy=generated_copy,
                fomo_score=float(fomo_score) if fomo_score else 70.0,
            )

            self.db.add(fomo_entry)
            await self.db.commit()
            await self.db.refresh(fomo_entry)

            logger.info(f"Generated FOMO copy for link {link_id} [{language}] (score: {fomo_score})")
            return fomo_entry

        except Exception as e:
            logger.error(f"Error generating FOMO for link {link_id}: {str(e)[:200]}")
            return None
