"""Service to sync FOMO copy to platform APIs."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO, PlatformSyncLog
from app.domains.seo_config.platform_sync_mercadolibre import MercadoLibreListingSync
from app.domains.seo_config.platform_sync_base import PlatformListingSyncConnector
from app.domains.seo_config.platform_algorithm_knowledge import canonical_platform

logger = get_logger(__name__)

# Map platform_source to connector class
PLATFORM_CONNECTORS = {
    "mercado-libre": MercadoLibreListingSync,
    # "shopify": ShopifyListingSync,
    # "instagram": InstagramListingSync,
    # Add more as implemented
}


class PlatformListingSyncService:
    """Sync FOMO copy to external platform APIs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_connector(
        self, platform_name: str, connection_id: UUID
    ) -> PlatformListingSyncConnector | None:
        """Get appropriate connector for platform.

        Fetches credentials from IntegrationConnection.
        """
        platform_name = canonical_platform(platform_name) or platform_name
        if platform_name not in PLATFORM_CONNECTORS:
            logger.warning(f"No connector implemented for platform: {platform_name}")
            return None

        try:
            # Get connection credentials from integrations table
            from app.domains.integrations.integration_models import IntegrationConnection

            result = await self.db.execute(
                select(IntegrationConnection).where(
                    IntegrationConnection.id == connection_id
                )
            )
            connection = result.scalar_one_or_none()

            if not connection:
                logger.error(f"Integration connection {connection_id} not found")
                return None

            # Parse credentials
            credentials = connection.auth_metadata or {}
            if connection.auth_token:
                credentials["access_token"] = connection.auth_token

            # Instantiate connector
            connector_class = PLATFORM_CONNECTORS[platform_name]
            connector = connector_class(credentials)

            # Validate
            if not await connector.validate_credentials():
                logger.error(f"Credentials validation failed for {platform_name}")
                return None

            return connector

        except Exception as e:
            logger.error(f"Error getting connector for {platform_name}: {str(e)[:200]}")
            return None

    async def sync_fomo_to_listing(
        self,
        business_id: UUID,
        link: PublicationLink,
        fomo: PublicationLinkFOMO,
        connection_id: UUID | None = None,
    ) -> PlatformSyncLog:
        """Sync FOMO copy to a single publication link on its platform."""
        sync_log = PlatformSyncLog(
            business_id=business_id,
            link_id=link.id,
            fomo_id=fomo.id if fomo else None,
            platform_name=link.platform_source,
            sync_type="description_update",
            status="pending",
        )

        try:
            # Extract listing ID from URL
            connector = await self.get_connector(link.platform_source, connection_id)
            if not connector:
                sync_log.status = "skipped"
                sync_log.error_message = f"No connector for {link.platform_source}"
                self.db.add(sync_log)
                await self.db.commit()
                return sync_log

            external_id = await connector.extract_listing_id(link.url)
            if not external_id:
                sync_log.status = "skipped"
                sync_log.error_message = "Could not extract listing ID from URL"
                self.db.add(sync_log)
                await self.db.commit()
                return sync_log

            sync_log.external_listing_id = external_id

            # Sync description (FOMO copy)
            if fomo:
                desc_result = await connector.update_listing_description(
                    external_id,
                    fomo.generated_copy,
                )

                sync_log.data_sent = {
                    "description": fomo.generated_copy,
                    "fomo_score": fomo.fomo_score,
                }
                sync_log.response_data = desc_result

                if desc_result.get("status") == "synced":
                    sync_log.status = "synced"
                    sync_log.synced_at = None  # Set by DB
                else:
                    sync_log.status = "failed"
                    sync_log.error_message = desc_result.get("error_message")

            logger.info(
                f"Synced FOMO to {link.platform_source}/{external_id}: {sync_log.status}"
            )

        except Exception as e:
            sync_log.status = "failed"
            sync_log.error_message = str(e)[:200]
            logger.error(f"Sync failed for link {link.id}: {str(e)[:200]}")

        self.db.add(sync_log)
        await self.db.commit()
        await self.db.refresh(sync_log)
        return sync_log

    async def sync_all_links(
        self, business_id: UUID
    ) -> dict:
        """Sync FOMO copy for all active links in a business."""
        result = await self.db.execute(
            select(PublicationLink).where(
                PublicationLink.business_id == business_id,
                PublicationLink.seo_enabled == True,
            )
        )
        links = result.scalars().all()

        synced = 0
        failed = 0
        skipped = 0

        for link in links:
            # Get latest FOMO for this link
            fomo_result = await self.db.execute(
                select(PublicationLinkFOMO)
                .where(PublicationLinkFOMO.link_id == link.id)
                .order_by(PublicationLinkFOMO.created_at.desc())
                .limit(1)
            )
            fomo = fomo_result.scalar_one_or_none()

            if not fomo:
                skipped += 1
                continue

            log = await self.sync_fomo_to_listing(business_id, link, fomo)

            if log.status == "synced":
                synced += 1
            elif log.status == "failed":
                failed += 1
            else:
                skipped += 1

        return {
            "business_id": str(business_id),
            "links_processed": len(links),
            "synced": synced,
            "failed": failed,
            "skipped": skipped,
        }
