"""FOMO copy generation for publication links.

Integrates with brand_transformation.FOMOEngineAgent to generate
FOMO-optimized descriptions for each PublicationLink.
"""

import json
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO, SEOConfig
from app.domains.brand_transformation.service import FOMOEngineAgent

logger = get_logger(__name__)


class PublicationFOMOGenerator:
    """Generate FOMO copy for publication links."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_fomo_generation_enabled(self, business_id: UUID) -> bool:
        """Check if FOMO generation is enabled (SEO config global toggle)."""
        result = await self.db.execute(
            select(SEOConfig).where(SEOConfig.business_id == business_id)
        )
        config = result.scalar_one_or_none()
        return config.global_seo_enabled if config else True

    async def generate_fomo_for_link(
        self, business_id: UUID, link: PublicationLink
    ) -> PublicationLinkFOMO | None:
        """Generate FOMO copy for a single publication link."""
        # Check if FOMO generation is enabled
        if not await self.is_fomo_generation_enabled(business_id):
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
