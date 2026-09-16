"""SEO Agent Guard — enforces SEO toggles before AI optimizations run."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import SEOConfig, PlatformSEOStatus

logger = get_logger(__name__)


class SEOAgentGuard:
    """Gate for SEO-sensitive agents (Positioning, FOMO).

    Checks if SEO is enabled before letting agents modify:
    - Product positioning/messaging
    - FOMO copy & descriptions
    - Platform-specific optimizations
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def can_run_seo_agent(
        self,
        business_id: UUID,
        agent_name: str,
        platform_id: UUID | None = None,
    ) -> bool:
        """Check if agent can run for this business/platform.

        Args:
            business_id: The business
            agent_name: 'positioning' or 'fomo_engine' (SEO-sensitive agents)
            platform_id: Optional platform (if modifying platform-specific copy)

        Returns:
            True if agent can run, False if SEO is disabled.
        """
        # Get global config
        result = await self.db.execute(
            select(SEOConfig).where(SEOConfig.business_id == business_id)
        )
        config = result.scalar_one_or_none()

        # Default to enabled if no config exists
        global_enabled = config.global_seo_enabled if config else True

        if not global_enabled:
            logger.info(
                f"SEO agent guard: {agent_name} BLOCKED for business {business_id} (global SEO disabled)"
            )
            return False

        # If platform-specific check needed, verify platform SEO status
        if platform_id:
            platform_result = await self.db.execute(
                select(PlatformSEOStatus).where(
                    PlatformSEOStatus.connection_id == platform_id
                )
            )
            platform_status = platform_result.scalar_one_or_none()

            if platform_status and not platform_status.seo_enabled:
                logger.info(
                    f"SEO agent guard: {agent_name} BLOCKED for platform {platform_status.platform_name} (platform SEO disabled)"
                )
                return False

        logger.info(f"SEO agent guard: {agent_name} ALLOWED for business {business_id}")
        return True

    async def log_agent_execution(
        self,
        business_id: UUID,
        agent_name: str,
        executed: bool,
        platform_id: UUID | None = None,
        result_summary: str | None = None,
    ) -> None:
        """Log agent execution for audit trail.

        Args:
            business_id: The business
            agent_name: Agent that ran (or was skipped)
            executed: True if agent ran, False if skipped due to disabled SEO
            platform_id: Optional platform being modified
            result_summary: Brief summary of what the agent produced
        """
        status = "EXECUTED" if executed else "SKIPPED (SEO disabled)"
        logger.info(
            f"SEO agent audit: {agent_name} [{status}] business={business_id} platform={platform_id} summary={result_summary}"
        )
