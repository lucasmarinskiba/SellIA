"""Instagram ranking-signal connector.

Fetches the signals Instagram's own Head of Instagram (Adam Mosseri) has
publicly named as the core ranking inputs: watch time, sends-per-reach (DM
shares — weighted several times heavier than likes for reaching
non-followers), and likes-per-reach. Reels specifically ranks on watch time
+ replay rate, not raw view count. Hashtags are explicitly de-weighted by
Meta; caption/bio keyword relevance now drives Search/Explore discovery.

Credential shape differs from Mercado Libre: Instagram Graph API identifies
the connected account by ig_user_id (a Business/Creator account), not a
seller_id, and there is no public post URL -> media ID parsing — the media
ID must be resolved by matching the stored PublicationLink.url against the
account's own media list.
"""

from typing import Any
import httpx

from app.core.logger import get_logger
from app.domains.seo_config.platform_ranking_base import PlatformRankingConnector, RankingSignal

logger = get_logger(__name__)


class InstagramRankingConnector(PlatformRankingConnector):
    """Fetch ranking/algorithm signals from Instagram Graph API."""

    platform_name = "instagram"
    API_BASE = "https://graph.facebook.com/v19.0"

    def __init__(self, credentials: dict[str, Any]):
        super().__init__(credentials)
        self.access_token = credentials.get("access_token")
        self.ig_user_id = credentials.get("ig_user_id")
        self._media_cache: dict[str, str] | None = None  # permalink -> media_id, per-call cache

    async def validate_credentials(self) -> bool:
        if not self.access_token or not self.ig_user_id:
            logger.error("Instagram ranking: missing access_token or ig_user_id")
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.API_BASE}/{self.ig_user_id}",
                    params={"fields": "id", "access_token": self.access_token},
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Instagram ranking credentials validation failed: {str(e)[:100]}")
            return False

    async def resolve_media_id(self, client: httpx.AsyncClient, url: str) -> str | None:
        """Resolve a PublicationLink.url (post permalink) to its Graph API media id.

        Instagram gives no ID-from-URL parsing the way ML's item URLs do —
        this walks the account's own media list looking for a matching
        permalink, cached per connector-instance call.
        """
        if self._media_cache is None:
            self._media_cache = {}
            try:
                resp = await client.get(
                    f"{self.API_BASE}/{self.ig_user_id}/media",
                    params={"fields": "id,permalink", "access_token": self.access_token, "limit": 100},
                    timeout=10,
                )
                if resp.status_code == 200:
                    for item in resp.json().get("data", []):
                        permalink = item.get("permalink")
                        if permalink:
                            self._media_cache[permalink.rstrip("/")] = item["id"]
            except Exception as e:
                logger.warning(f"Instagram ranking: media list fetch failed: {str(e)[:100]}")

        return self._media_cache.get(url.rstrip("/"))

    async def get_ranking_signals(self, external_id: str) -> list[RankingSignal]:
        """external_id here is expected to already be a resolved media id
        (callers should use resolve_media_id() first if they only have a URL)."""
        if not self.access_token or not self.ig_user_id:
            return [RankingSignal("credentials_missing", True, measured=True)]

        signals: list[RankingSignal] = []
        async with httpx.AsyncClient() as client:
            insights = await self._fetch_insights(client, external_id)
            media = await self._fetch_media_fields(client, external_id)

            signals.extend(self._engagement_signals(insights))
            signals.extend(self._reels_signals(insights))
            signals.extend(self._content_signals(media))

        return signals

    async def _fetch_insights(self, client: httpx.AsyncClient, media_id: str) -> dict[str, Any]:
        metrics = "reach,likes,comments,saved,shares,ig_reels_avg_watch_time,ig_reels_video_view_total_time,plays"
        try:
            resp = await client.get(
                f"{self.API_BASE}/{media_id}/insights",
                params={"metric": metrics, "access_token": self.access_token},
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning(f"Instagram ranking: insights returned {resp.status_code} for {media_id}")
                return {}
            out: dict[str, Any] = {}
            for entry in resp.json().get("data", []):
                values = entry.get("values") or []
                out[entry["name"]] = values[0]["value"] if values else None
            return out
        except Exception as e:
            logger.warning(f"Instagram ranking: insights fetch failed: {str(e)[:100]}")
            return {}

    async def _fetch_media_fields(self, client: httpx.AsyncClient, media_id: str) -> dict[str, Any]:
        try:
            resp = await client.get(
                f"{self.API_BASE}/{media_id}",
                params={"fields": "caption,alt_text,media_type", "access_token": self.access_token},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"Instagram ranking: media fields fetch failed: {str(e)[:100]}")
        return {}

    def _engagement_signals(self, insights: dict[str, Any]) -> list[RankingSignal]:
        reach = insights.get("reach")
        if not reach:
            return [
                RankingSignal("sends_per_reach", None, measured=False, detail="no reach data"),
                RankingSignal("likes_per_reach", None, measured=False, detail="no reach data"),
                RankingSignal("saves_per_reach", None, measured=False, detail="no reach data"),
                RankingSignal("comments_per_reach", None, measured=False, detail="no reach data"),
            ]

        shares = insights.get("shares") or 0
        likes = insights.get("likes") or 0
        saved = insights.get("saved") or 0
        comments = insights.get("comments") or 0

        return [
            RankingSignal(
                "sends_per_reach", round(shares / reach, 4), measured=True,
                detail="Meta's #1 stated ranking signal for reaching non-followers, weighted ~3-5x likes",
            ),
            RankingSignal("likes_per_reach", round(likes / reach, 4), measured=True),
            RankingSignal("saves_per_reach", round(saved / reach, 4), measured=True),
            RankingSignal("comments_per_reach", round(comments / reach, 4), measured=True),
        ]

    def _reels_signals(self, insights: dict[str, Any]) -> list[RankingSignal]:
        watch_time = insights.get("ig_reels_avg_watch_time")
        total_watch_time = insights.get("ig_reels_video_view_total_time")
        plays = insights.get("plays")

        out = [RankingSignal(
            "watch_time_seconds", watch_time, measured=watch_time is not None,
            unit="s", detail="Reels ranks primarily on watch time, not view count",
        )]

        if total_watch_time and plays:
            replay_rate = round(total_watch_time / (plays * (watch_time or 1)), 4) if watch_time else None
            out.append(RankingSignal(
                "replay_rate_pct", replay_rate, measured=replay_rate is not None,
                detail="replays relative to plays; not applicable to static image posts",
            ))
        else:
            out.append(RankingSignal("replay_rate_pct", None, measured=False, detail="not a Reel or insufficient data"))

        return out

    def _content_signals(self, media: dict[str, Any]) -> list[RankingSignal]:
        caption = media.get("caption") or ""
        alt_text = media.get("alt_text")
        hashtag_count = caption.count("#")

        return [
            RankingSignal(
                "alt_text_present", bool(alt_text), measured=True,
                detail="alt text feeds Instagram Search/discovery keyword relevance",
            ),
            RankingSignal(
                "hashtag_count", hashtag_count, measured=True,
                detail="downgraded ranking signal per Meta's own public statements — informational only, not scored",
            ),
            RankingSignal(
                "caption_keyword_coverage", None, measured=False,
                detail="requires a target-keyword list from the business profile to score — not computed here",
            ),
        ]

    # Note: posting_cadence_days is NOT computed here — it needs the business's
    # full PublicationLink history (platform_source="instagram"), which lives
    # outside this connector. PositioningScoreService computes it locally.

    # ── Scoring (moved from PositioningScoreService — identical formulas) ──

    def score_signals(self, signal_map: dict[str, RankingSignal]) -> dict[str, float | None]:
        return {
            "reputation_score": None,
            "conversion_score": None,
            "price_competitiveness_score": None,
            "listing_quality_score": self._content_quality_score(signal_map),
            "logistics_score": None,
            "engagement_score": self._engagement_score(signal_map),
        }

    def _engagement_score(self, signals: dict[str, RankingSignal]) -> float | None:
        sends = signals.get("sends_per_reach")
        likes = signals.get("likes_per_reach")
        saves = signals.get("saves_per_reach")
        comments = signals.get("comments_per_reach")

        if not sends or not sends.measured or sends.value is None:
            return None

        # Weighted per Mosseri's public statements: sends carry several times
        # the weight of likes for reaching non-followers.
        raw = (
            (sends.value or 0) * 4.0
            + (likes.value or 0) * 1.0
            + (saves.value or 0) * 1.5
            + (comments.value or 0) * 1.5
        )
        # Normalize against a rough reference ceiling (per-reach ratios are
        # small fractions; this is a defensible default, not an IG-published
        # scale — a business-specific rolling median would be more accurate
        # but requires the caller to supply trailing history, which is out
        # of scope for a single-link score).
        return round(min(100.0, raw * 500), 1)

    def _content_quality_score(self, signals: dict[str, RankingSignal]) -> float | None:
        alt_text = signals.get("alt_text_present")
        if not alt_text or not alt_text.measured:
            return None
        return 100.0 if alt_text.value else 50.0

    def recommendation_rules(self, signal_map: dict[str, RankingSignal]) -> list[dict]:
        signals = signal_map
        rules: list[dict] = []

        sends = signals.get("sends_per_reach")
        likes = signals.get("likes_per_reach")
        if (
            sends and sends.measured and sends.value is not None
            and likes and likes.measured and likes.value is not None
            and sends.value < likes.value * 0.1
        ):
            rules.append({
                "signal_key": "sends_per_reach",
                "severity": "warning",
                "message": (
                    "Tus envíos por DM son muy bajos respecto a tus likes — es la señal #1 "
                    "de ranking de Instagram, priorizala sobre likes en tu próximo contenido."
                ),
                "current_value": f"{sends.value:.4f}",
                "target_value": "> likes_per_reach * 0.1",
            })

        alt_text = signals.get("alt_text_present")
        if alt_text and alt_text.measured and not alt_text.value:
            rules.append({
                "signal_key": "alt_text_present",
                "severity": "info",
                "message": "Tu post no tiene alt text — agregalo, ahora alimenta el discovery de Instagram Search.",
                "current_value": "sin alt text",
                "target_value": "con alt text",
            })

        return rules
