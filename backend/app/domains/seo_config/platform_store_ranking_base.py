"""Base interface for STORE-level positioning connectors.

Separate from PlatformRankingConnector on purpose: that interface scores one
listing/post identified by an external id; this one scores a whole storefront
or brand presence (e.g. an Amazon Brand Store). The unit differs, and for
Amazon so do the credentials (Ads API, not SP-API), so forcing both through
one interface would blur two different auth surfaces.

RankingSignal is reused as-is — the "never present a guess as fact"
measured=True/False discipline applies identically.

Not implemented, on purpose — Mercado Libre "Tienda Oficial": the official-store
badge/page exists, and Mercado Libre's own marketing says it helps search
placement, but no public analytics API for it was confirmed. It needs a
dedicated research pass against developers.mercadolibre.com before any
connector is written; a guessed one would just fabricate signals.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.domains.seo_config.platform_ranking_base import RankingSignal


class StorePositioningConnector(ABC):
    """Fetch and score store/brand-level presence signals for one platform."""

    platform_name: str

    def __init__(self, credentials: dict[str, Any]):
        self.credentials = credentials

    @abstractmethod
    async def get_store_signals(self, store_external_id: str | None = None) -> list[RankingSignal]:
        """Fetch store-level signals. Every sub-call independently try/excepted —
        one missing permission yields measured=False for that signal only."""
        ...

    @abstractmethod
    async def validate_credentials(self) -> bool:
        ...

    @abstractmethod
    def score_signals(self, signal_map: dict[str, RankingSignal]) -> dict[str, float | None]:
        """Map signals into StorePositioningScore sub-scores (traffic_score,
        engagement_score, new_visitor_score, content_performance_score).
        A pillar with no honest signal stays None."""
        ...

    @abstractmethod
    def recommendation_rules(self, signal_map: dict[str, RankingSignal]) -> list[dict]:
        """Concrete rules: {signal_key, severity, message, current_value, target_value}."""
        ...
