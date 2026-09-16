"""Smart defaults — auto-create SEO config when platforms connect."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import PlatformSEOStatus

logger = get_logger(__name__)


class SmartDefaultsService:
    """Manage auto-created SEO configs for platforms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def auto_create_platform_seo_status(
        self,
        business_id: UUID,
        connection_id: UUID,
        platform_name: str,
    ) -> PlatformSEOStatus:
        """Auto-create PlatformSEOStatus when platform connects.

        Default: SEO enabled for new platforms.
        """
        # Check if already exists
        result = await self.db.execute(
            select(PlatformSEOStatus).where(
                PlatformSEOStatus.connection_id == connection_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"PlatformSEOStatus already exists for {connection_id}")
            return existing

        # Create new status with SEO enabled by default
        status = PlatformSEOStatus(
            business_id=business_id,
            connection_id=connection_id,
            platform_name=platform_name,
            seo_enabled=True,  # Smart default: enable SEO for new platforms
        )

        self.db.add(status)
        await self.db.commit()
        await self.db.refresh(status)

        logger.info(
            f"Auto-created PlatformSEOStatus for {platform_name} (connection={connection_id})"
        )

        return status
