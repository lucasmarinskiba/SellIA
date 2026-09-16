"""Base interface for platform analytics connectors."""

from abc import ABC, abstractmethod
from typing import Any
from datetime import date

from app.core.logger import get_logger

logger = get_logger(__name__)


class PlatformAnalyticsConnector(ABC):
    """Base interface for fetching metrics from platform APIs."""

    platform_name: str

    def __init__(self, credentials: dict[str, Any]):
        self.credentials = credentials

    @abstractmethod
    async def get_listing_metrics(
        self, external_id: str, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """Fetch metrics for a listing from the platform API.

        Args:
            external_id: Listing ID on platform
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dict with keys: impressions, clicks, conversions, revenue (optional)
        """
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Verify API credentials are valid."""
        pass
