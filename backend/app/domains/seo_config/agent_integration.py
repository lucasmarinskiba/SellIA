"""Integration hooks for brand transformation agents.

Wraps PositioningAgent and FOMOEngineAgent to respect SEO toggles.
Call these before the actual agent methods.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.agent_guard import SEOAgentGuard

logger = get_logger(__name__)


class SEOAwareAgentWrapper:
    """Wrapper that checks SEO toggles before running positioning/FOMO agents."""

    def __init__(self, db: AsyncSession):
        self.guard = SEOAgentGuard(db)

    async def should_run_positioning_agent(self, business_id: UUID) -> bool:
        """Check if PositioningAgent should run for this business.

        The PositioningAgent generates positioning statements that drive
        SEO copy, keywords, and messaging across listings.
        """
        can_run = await self.guard.can_run_seo_agent(business_id, "positioning_agent")
        if not can_run:
            await self.guard.log_agent_execution(business_id, "positioning_agent", False)
        return can_run

    async def should_run_fomo_engine_agent(
        self, business_id: UUID, platform_id: UUID | None = None
    ) -> bool:
        """Check if FOMOEngineAgent should run.

        The FOMOEngineAgent generates FOMO copy, scarcity messaging, and
        urgency triggers for product listings.
        """
        can_run = await self.guard.can_run_seo_agent(
            business_id, "fomo_engine_agent", platform_id
        )
        if not can_run:
            await self.guard.log_agent_execution(
                business_id, "fomo_engine_agent", False, platform_id
            )
        return can_run

    async def log_positioning_execution(
        self, business_id: UUID, result_summary: str
    ) -> None:
        """Log that PositioningAgent ran successfully."""
        await self.guard.log_agent_execution(
            business_id, "positioning_agent", True, result_summary=result_summary
        )

    async def log_fomo_execution(
        self, business_id: UUID, platform_id: UUID | None, result_summary: str
    ) -> None:
        """Log that FOMOEngineAgent ran successfully."""
        await self.guard.log_agent_execution(
            business_id, "fomo_engine_agent", True, platform_id, result_summary
        )
