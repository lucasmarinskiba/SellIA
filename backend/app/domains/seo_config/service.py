"""SEO Config service."""

from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.seo_config.models import SEOConfig, PlatformSEOStatus, PublicationLink
from app.domains.integrations.integration_models import IntegrationConnection


class SEOConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_seo_config(self, business_id: UUID) -> SEOConfig:
        """Get or create global SEO config for business."""
        result = await self.db.execute(
            select(SEOConfig).where(SEOConfig.business_id == business_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            config = SEOConfig(business_id=business_id)
            self.db.add(config)
            await self.db.flush()

        return config

    async def toggle_global_seo(self, business_id: UUID, enabled: bool) -> SEOConfig:
        """Toggle global SEO on/off."""
        config = await self.get_or_create_seo_config(business_id)
        config.global_seo_enabled = enabled
        await self.db.commit()
        return config

    async def get_platform_seo_status(self, connection_id: UUID) -> PlatformSEOStatus | None:
        """Get SEO status for a specific platform connection."""
        result = await self.db.execute(
            select(PlatformSEOStatus).where(PlatformSEOStatus.connection_id == connection_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_platform_seo_status(
        self, business_id: UUID, connection_id: UUID, platform_name: str
    ) -> PlatformSEOStatus:
        """Get or create platform SEO status."""
        result = await self.db.execute(
            select(PlatformSEOStatus).where(
                PlatformSEOStatus.connection_id == connection_id
            )
        )
        status = result.scalar_one_or_none()

        if not status:
            status = PlatformSEOStatus(
                business_id=business_id,
                connection_id=connection_id,
                platform_name=platform_name,
            )
            self.db.add(status)
            await self.db.flush()

        return status

    async def toggle_platform_seo(self, connection_id: UUID, enabled: bool) -> PlatformSEOStatus | None:
        """Toggle SEO for a specific platform."""
        status = await self.get_platform_seo_status(connection_id)
        if status:
            status.seo_enabled = enabled
            await self.db.commit()
        return status

    async def list_business_platforms_with_seo(self, business_id: UUID) -> list[dict]:
        """List all connected platforms with their SEO status."""
        result = await self.db.execute(
            select(
                IntegrationConnection.id,
                IntegrationConnection.connection_status,
                IntegrationConnection.last_sync_at,
                PlatformSEOStatus.platform_name,
                PlatformSEOStatus.seo_enabled,
            ).outerjoin(
                PlatformSEOStatus,
                IntegrationConnection.id == PlatformSEOStatus.connection_id,
            ).where(
                IntegrationConnection.business_id == business_id,
                IntegrationConnection.connection_status == "active",
            )
        )

        platforms = []
        for row in result.fetchall():
            conn_id, conn_status, last_sync, platform_name, seo_enabled = row
            # If no PlatformSEOStatus exists yet, default to enabled
            platforms.append({
                "connection_id": str(conn_id),
                "platform_name": platform_name or "unknown",
                "status": conn_status,
                "last_sync": last_sync.isoformat() if last_sync else None,
                "seo_enabled": seo_enabled if seo_enabled is not None else True,
            })

        return platforms


class PublicationLinkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_publication_link(
        self,
        business_id: UUID,
        url: str,
        title: str,
        platform_source: str,
        product_id: UUID | None = None,
        connection_id: UUID | None = None,
    ) -> PublicationLink:
        """Create a new publication link."""
        link = PublicationLink(
            business_id=business_id,
            url=url,
            title=title,
            platform_source=platform_source,
            product_id=product_id,
            connection_id=connection_id,
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def get_publication_link(self, link_id: UUID) -> PublicationLink | None:
        """Get a publication link by ID."""
        result = await self.db.execute(
            select(PublicationLink).where(PublicationLink.id == link_id)
        )
        return result.scalar_one_or_none()

    async def list_business_publication_links(self, business_id: UUID) -> list[PublicationLink]:
        """List all publication links for a business."""
        result = await self.db.execute(
            select(PublicationLink)
            .where(PublicationLink.business_id == business_id)
            .order_by(PublicationLink.created_at.desc())
        )
        return result.scalars().all()

    async def toggle_publication_link_seo(self, link_id: UUID, enabled: bool) -> PublicationLink | None:
        """Toggle SEO for a specific publication link."""
        link = await self.get_publication_link(link_id)
        if link:
            link.seo_enabled = enabled
            await self.db.commit()
            await self.db.refresh(link)
        return link

    async def delete_publication_link(self, link_id: UUID) -> bool:
        """Delete a publication link."""
        link = await self.get_publication_link(link_id)
        if link:
            await self.db.delete(link)
            await self.db.commit()
            return True
        return False
