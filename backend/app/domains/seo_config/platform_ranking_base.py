"""Base interface for platform ranking-signal connectors.

Distinct from PlatformAnalyticsConnector (impressions/clicks/conversions):
ranking connectors fetch the specific signals each platform's algorithm is
documented (or strongly evidenced by public statements) to weight when
deciding visibility — seller reputation, listing completeness, watch time,
etc. Each signal is tagged measured=True (fetched from a real API response)
or measured=False (locally inferred/heuristic) so the composite scorer never
presents a guess as fact.
"""

from abc import ABC, abstractmethod
from typing import Any


class RankingSignal:
    """One platform-specific ranking signal value, with provenance."""

    def __init__(
        self,
        key: str,
        value: Any,
        measured: bool,
        unit: str = "",
        detail: str = "",
    ):
        self.key = key
        self.value = value
        self.measured = measured
        self.unit = unit
        self.detail = detail

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "measured": self.measured,
            "unit": self.unit,
            "detail": self.detail,
        }


class PlatformRankingConnector(ABC):
    """Base interface for fetching ranking/algorithm signals from a platform."""

    platform_name: str

    def __init__(self, credentials: dict[str, Any]):
        self.credentials = credentials

    @abstractmethod
    async def get_ranking_signals(self, external_id: str) -> list[RankingSignal]:
        """Fetch every ranking-relevant signal available for one listing/post.

        Implementations must never let one failing sub-call blank the whole
        result — catch per-signal and return what's available, using
        measured=False for anything that could not be fetched.
        """
        ...

    @abstractmethod
    async def validate_credentials(self) -> bool:
        ...

    @abstractmethod
    def score_signals(self, signal_map: dict[str, "RankingSignal"]) -> dict[str, float | None]:
        """Map fetched signals into the composite scorer's sub-score dict
        (reputation_score, conversion_score, price_competitiveness_score,
        listing_quality_score, logistics_score, engagement_score). A pillar
        this platform has no honest signal for stays None — never fabricated.
        """
        ...

    @abstractmethod
    def recommendation_rules(self, signal_map: dict[str, "RankingSignal"]) -> list[dict]:
        """Concrete, platform-specific recommendation rules triggered by
        signal values. Each rule dict: {signal_key, severity, message,
        current_value, target_value}. Messages must be concrete (real
        numbers/thresholds), never generic advice.
        """
        ...
