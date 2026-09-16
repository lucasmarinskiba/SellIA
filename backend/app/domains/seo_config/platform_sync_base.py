"""Base classes for platform listing sync connectors."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)


class PlatformListingSyncConnector(ABC):
    """Base interface for syncing FOMO copy to platform APIs."""

    platform_name: str

    def __init__(self, credentials: dict[str, Any]):
        """Initialize with platform API credentials."""
        self.credentials = credentials

    @abstractmethod
    async def update_listing_title(self, external_id: str, title: str) -> dict[str, Any]:
        """Update listing title on platform.

        Args:
            external_id: Listing ID on the platform
            title: New title with FOMO copy

        Returns:
            Response dict with status, optional error_message
        """
        pass

    @abstractmethod
    async def update_listing_description(self, external_id: str, description: str) -> dict[str, Any]:
        """Update listing description/body on platform.

        Args:
            external_id: Listing ID on the platform
            description: New description (FOMO copy)

        Returns:
            Response dict with status, optional error_message
        """
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Verify credentials are valid."""
        pass

    @abstractmethod
    async def extract_listing_id(self, url: str) -> str | None:
        """Extract platform's listing ID from URL.

        Args:
            url: Publication link URL

        Returns:
            Listing ID or None if can't extract
        """
        pass
