"""Bulk import listings from platforms → auto-create publication links + FOMO."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink
from app.domains.seo_config.fomo_generator import PublicationFOMOGenerator

logger = get_logger(__name__)


class BulkListingImporter:
    """Import multiple listings from platform → create PublicationLinks + generate FOMO."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_listings_from_platform(
        self,
        business_id: UUID,
        listings: list[dict],
        platform_source: str,
    ) -> dict:
        """Import multiple listings and create PublicationLinks + FOMO.

        Args:
            business_id: Business owner
            listings: List of {url, title, product_id (optional)}
            platform_source: Platform name (mercado-libre, shopify, etc.)

        Returns:
            {imported: N, fomo_generated: M, failed: K}
        """
        imported = 0
        fomo_generated = 0
        failed = 0

        fomo_gen = PublicationFOMOGenerator(self.db)

        for listing in listings:
            try:
                url = listing.get("url")
                title = listing.get("title", url.split("/")[-1])
                product_id = listing.get("product_id")

                if not url:
                    failed += 1
                    continue

                # Create PublicationLink
                link = PublicationLink(
                    business_id=business_id,
                    url=url,
                    title=title,
                    platform_source=platform_source,
                    product_id=product_id,
                    seo_enabled=True,
                )
                self.db.add(link)
                await self.db.flush()
                imported += 1

                # Auto-generate FOMO
                if await fomo_gen.is_fomo_generation_enabled(business_id):
                    fomo = await fomo_gen.generate_fomo_for_link(business_id, link)
                    if fomo:
                        fomo_generated += 1

            except Exception as e:
                logger.error(f"Failed to import listing {listing.get('url')}: {str(e)[:100]}")
                failed += 1

        await self.db.commit()
        logger.info(
            f"Bulk import complete: {imported} links, {fomo_generated} FOMO generated, {failed} failed"
        )

        return {
            "imported": imported,
            "fomo_generated": fomo_generated,
            "failed": failed,
        }
