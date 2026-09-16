from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.integrations.integration_models import IntegrationApp, IntegrationConnection, IntegrationEvent
from app.domains.seo_config.smart_defaults import SmartDefaultsService

logger = get_logger(__name__)


class IntegrationService:
    """Manage platform integrations + auto-create SEO configs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_connection(
        self,
        business_id: UUID,
        app_id: UUID,
        auth_token: str | None = None,
        auth_metadata: dict | None = None,
        platform_name: str | None = None,
    ) -> IntegrationConnection:
        """Create platform connection + auto-create SEO config.

        Calls SmartDefaultsService to auto-enable SEO for new platforms.
        """
        # Create connection
        connection = IntegrationConnection(
            business_id=business_id,
            app_id=app_id,
            auth_token=auth_token,
            auth_metadata=auth_metadata,
            connection_status="active",
        )
        self.db.add(connection)
        await self.db.flush()

        # Auto-create SEO config for this platform
        if platform_name:
            smart_defaults = SmartDefaultsService(self.db)
            try:
                await smart_defaults.auto_create_platform_seo_status(
                    business_id=business_id,
                    connection_id=connection.id,
                    platform_name=platform_name,
                )
                logger.info(f"Auto-created SEO config for {platform_name}")
            except Exception as e:
                logger.error(f"Failed to auto-create SEO config: {str(e)[:100]}")
                # Don't fail the connection creation if SEO config fails

        await self.db.commit()
        await self.db.refresh(connection)

        return connection

    async def get_connection(self, connection_id: UUID) -> IntegrationConnection | None:
        """Get integration connection by ID."""
        result = await self.db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.id == connection_id
            )
        )
        return result.scalar_one_or_none()

    async def list_business_connections(self, business_id: UUID) -> list[IntegrationConnection]:
        """List all connections for a business."""
        result = await self.db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.business_id == business_id
            )
        )
        return result.scalars().all()

    async def update_connection(
        self,
        connection_id: UUID,
        auth_token: str | None = None,
        auth_metadata: dict | None = None,
        connection_status: str | None = None,
    ) -> IntegrationConnection | None:
        """Update connection credentials or status."""
        connection = await self.get_connection(connection_id)
        if not connection:
            return None

        if auth_token:
            connection.auth_token = auth_token
        if auth_metadata:
            connection.auth_metadata = auth_metadata
        if connection_status:
            connection.connection_status = connection_status

        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)

        return connection
