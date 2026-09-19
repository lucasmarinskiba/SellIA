"""Mercado Libre ranking-signal connector.

Fetches the signals Mercado Libre's own seller help center / developer docs
document as tied to search visibility and the reputation ("termómetro")
system: reputation health gauge, claims/cancellation rate, catalog Buy Box
status, question response latency, shipping tier, and listing completeness.

None of this is ML's published ranking-weights formula (ML has never
published one) — it's the set of concrete, API-fetchable signals that the
seller community consistently treats as the drivers of exposure. Each call
is independent and try/excepted so one missing scope/permission doesn't
blank the whole signal set.
"""

from typing import Any
import httpx

from app.core.logger import get_logger
from app.domains.seo_config.platform_ranking_base import PlatformRankingConnector, RankingSignal

logger = get_logger(__name__)


class MercadoLibreRankingConnector(PlatformRankingConnector):
    """Fetch ranking/algorithm signals from Mercado Libre."""

    platform_name = "mercado-libre"
    API_BASE = "https://api.mercadolibre.com"

    def __init__(self, credentials: dict[str, Any]):
        super().__init__(credentials)
        self.access_token = credentials.get("access_token")
        self.seller_id = credentials.get("seller_id")

    async def validate_credentials(self) -> bool:
        if not self.access_token or not self.seller_id:
            logger.error("MercadoLibre ranking: missing access_token or seller_id")
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.API_BASE}/users/{self.seller_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"MercadoLibre ranking credentials validation failed: {str(e)[:100]}")
            return False

    async def get_ranking_signals(self, external_id: str) -> list[RankingSignal]:
        if not self.access_token or not self.seller_id:
            return [RankingSignal("credentials_missing", True, measured=True)]

        signals: list[RankingSignal] = []
        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            item_data = await self._fetch_item(client, headers, external_id)
            signals.extend(await self._reputation_signals(client, headers))
            signals.extend(self._buy_box_signal(item_data))
            signals.extend(self._shipping_signal(item_data))
            signals.extend(await self._question_signals(client, headers, external_id))
            signals.extend(await self._listing_completeness_signals(client, headers, item_data))
            signals.extend(self._title_and_photo_signals(item_data))

        return signals

    async def _fetch_item(
        self, client: httpx.AsyncClient, headers: dict, external_id: str
    ) -> dict[str, Any] | None:
        try:
            resp = await client.get(
                f"{self.API_BASE}/items/{external_id}", headers=headers, timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"MercadoLibre ranking: item fetch failed for {external_id}: {str(e)[:100]}")
        return None

    async def _reputation_signals(
        self, client: httpx.AsyncClient, headers: dict
    ) -> list[RankingSignal]:
        out: list[RankingSignal] = []
        try:
            resp = await client.get(
                f"{self.API_BASE}/users/{self.seller_id}", headers=headers, timeout=10
            )
            if resp.status_code != 200:
                out.append(RankingSignal(
                    "reputation_health_gauge", None, measured=False,
                    detail=f"seller lookup returned {resp.status_code}",
                ))
                return out

            data = resp.json()
            reputation = data.get("seller_reputation") or {}
            metrics = reputation.get("metrics") or {}
            claims = (metrics.get("claims") or {}).get("rate")
            cancellations = (metrics.get("cancellations") or {}).get("rate")
            level_id = reputation.get("level_id")

            out.append(RankingSignal(
                "seller_claims_rate",
                round(claims * 100, 2) if claims is not None else None,
                measured=claims is not None,
                unit="%",
                detail="ML reputation threshold: keep below 3% (1% for top tier)",
            ))
            out.append(RankingSignal(
                "seller_cancellation_rate",
                round(cancellations * 100, 2) if cancellations is not None else None,
                measured=cancellations is not None,
                unit="%",
            ))
            out.append(RankingSignal(
                "seller_reputation_level",
                level_id,
                measured=level_id is not None,
                detail="e.g. 5_green = top tier, 1_red = lowest",
            ))
        except Exception as e:
            logger.warning(f"MercadoLibre ranking: reputation fetch failed: {str(e)[:100]}")
            out.append(RankingSignal("seller_claims_rate", None, measured=False, detail=str(e)[:100]))

        # Reputation Health Gauge is a documented, per-item query parameter on
        # the items/search endpoint (unhealthy/warning/healthy exposure risk).
        try:
            gauge_resp = await client.get(
                f"{self.API_BASE}/users/{self.seller_id}/items/search",
                headers=headers,
                timeout=10,
                params={"reputation_health_gauge": "unhealthy"},
            )
            if gauge_resp.status_code == 200:
                unhealthy_ids = set(gauge_resp.json().get("results", []))
                out.append(RankingSignal(
                    "seller_has_unhealthy_items",
                    len(unhealthy_ids) > 0,
                    measured=True,
                    detail=f"{len(unhealthy_ids)} item(s) flagged unhealthy by ML's exposure-risk gauge",
                ))
            else:
                out.append(RankingSignal("seller_has_unhealthy_items", None, measured=False))
        except Exception as e:
            logger.warning(f"MercadoLibre ranking: reputation gauge fetch failed: {str(e)[:100]}")
            out.append(RankingSignal("seller_has_unhealthy_items", None, measured=False, detail=str(e)[:100]))

        return out

    def _buy_box_signal(self, item_data: dict[str, Any] | None) -> list[RankingSignal]:
        if not item_data:
            return [RankingSignal("buy_box_winner", None, measured=False, detail="item not fetched")]

        catalog_product_id = item_data.get("catalog_product_id")
        if not catalog_product_id:
            return [RankingSignal(
                "buy_box_winner", None, measured=False,
                detail="not catalog-eligible (no catalog_product_id)",
            )]

        catalog_listing = item_data.get("catalog_listing", False)
        return [RankingSignal(
            "buy_box_winner",
            bool(catalog_listing),
            measured=True,
            detail="whether this listing is the featured/winning offer for its catalog product",
        )]

    def _shipping_signal(self, item_data: dict[str, Any] | None) -> list[RankingSignal]:
        if not item_data:
            return [RankingSignal("shipping_tier", None, measured=False, detail="item not fetched")]

        logistic_type = (item_data.get("shipping") or {}).get("logistic_type")
        tier_map = {
            "fulfillment": "full",
            "cross_docking": "flex",
            "drop_off": "flex",
        }
        tier = tier_map.get(logistic_type, "standard") if logistic_type else None
        return [RankingSignal(
            "shipping_tier", tier, measured=tier is not None,
            detail="Full/Flex listings carry preferential shipping badges per ML docs",
        )]

    async def _question_signals(
        self, client: httpx.AsyncClient, headers: dict, external_id: str
    ) -> list[RankingSignal]:
        try:
            resp = await client.get(
                f"{self.API_BASE}/questions/search",
                headers=headers,
                timeout=10,
                params={"item": external_id, "api_version": 4},
            )
            if resp.status_code != 200:
                return [
                    RankingSignal(
                        "question_response_latency_minutes", None, measured=False,
                        detail=f"questions API returned {resp.status_code} (likely missing questions_read scope)",
                    ),
                    RankingSignal("question_answer_rate_pct", None, measured=False),
                ]

            questions = resp.json().get("questions", [])
            if not questions:
                return [
                    RankingSignal("question_response_latency_minutes", None, measured=False, detail="no questions yet"),
                    RankingSignal("question_answer_rate_pct", None, measured=False, detail="no questions yet"),
                ]

            answered = [q for q in questions if q.get("answer")]
            latencies = []
            for q in answered:
                try:
                    from datetime import datetime
                    asked = datetime.fromisoformat(q["date_created"].replace("Z", "+00:00"))
                    replied = datetime.fromisoformat(q["answer"]["date_created"].replace("Z", "+00:00"))
                    latencies.append((replied - asked).total_seconds() / 60)
                except Exception:
                    continue

            avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else None
            answer_rate = round(len(answered) / len(questions) * 100, 1)

            return [
                RankingSignal(
                    "question_response_latency_minutes", avg_latency, measured=avg_latency is not None,
                    unit="min", detail="community best practice: keep average under 60min",
                ),
                RankingSignal(
                    "question_answer_rate_pct", answer_rate, measured=True,
                    unit="%", detail="community best practice: answer >90% of questions",
                ),
            ]
        except Exception as e:
            logger.warning(f"MercadoLibre ranking: question signals failed: {str(e)[:100]}")
            return [
                RankingSignal("question_response_latency_minutes", None, measured=False, detail=str(e)[:100]),
                RankingSignal("question_answer_rate_pct", None, measured=False, detail=str(e)[:100]),
            ]

    async def _listing_completeness_signals(
        self, client: httpx.AsyncClient, headers: dict, item_data: dict[str, Any] | None
    ) -> list[RankingSignal]:
        if not item_data:
            return [RankingSignal("listing_completeness_pct", None, measured=False, detail="item not fetched")]

        category_id = item_data.get("category_id")
        if not category_id:
            return [RankingSignal("listing_completeness_pct", None, measured=False, detail="no category_id on item")]

        try:
            resp = await client.get(
                f"{self.API_BASE}/categories/{category_id}/attributes",
                headers=headers,
                timeout=10,
            )
            if resp.status_code != 200:
                return [RankingSignal(
                    "listing_completeness_pct", None, measured=False,
                    detail=f"category attributes lookup returned {resp.status_code}",
                )]

            required_attr_ids = {
                a["id"] for a in resp.json()
                if any(tag == "required" for tag in (a.get("tags") or {}).keys())
            }
            if not required_attr_ids:
                return [RankingSignal(
                    "listing_completeness_pct", 100.0, measured=True,
                    detail="category has no required attributes",
                )]

            filled_attr_ids = {
                a["id"] for a in (item_data.get("attributes") or [])
                if a.get("value_id") or a.get("value_name")
            }
            filled_required = required_attr_ids & filled_attr_ids
            pct = round(len(filled_required) / len(required_attr_ids) * 100, 1)

            return [RankingSignal(
                "listing_completeness_pct", pct, measured=True,
                unit="%",
                detail=f"{len(required_attr_ids) - len(filled_required)} required attribute(s) missing",
            )]
        except Exception as e:
            logger.warning(f"MercadoLibre ranking: completeness check failed: {str(e)[:100]}")
            return [RankingSignal("listing_completeness_pct", None, measured=False, detail=str(e)[:100])]

    def _title_and_photo_signals(self, item_data: dict[str, Any] | None) -> list[RankingSignal]:
        if not item_data:
            return [
                RankingSignal("title_length_score", None, measured=False, detail="item not fetched"),
                RankingSignal("photo_count", None, measured=False, detail="item not fetched"),
            ]

        title = item_data.get("title", "") or ""
        title_len = len(title)
        # ML's practical title guidance: use the available space (~60 chars)
        # with real keywords, no stuffing.
        title_score = 100.0 if 40 <= title_len <= 60 else max(0.0, 100.0 - abs(title_len - 50) * 2)

        photos = item_data.get("pictures") or []

        return [
            RankingSignal(
                "title_length_score", round(title_score, 1), measured=True,
                detail=f"title is {title_len} chars (target ~40-60)",
            ),
            RankingSignal(
                "photo_count", len(photos), measured=True,
                detail="ML recommends 6+ photos",
            ),
        ]

    # ── Scoring (moved from PositioningScoreService — identical formulas) ──

    def score_signals(self, signal_map: dict[str, RankingSignal]) -> dict[str, float | None]:
        """Weights/thresholds encode community-consensus marketplace ranking
        behavior, not any platform's published formula — ML has never
        published exact weights. A pillar stays None (excluded from the
        composite) when no honest signal exists for it."""
        return {
            "reputation_score": self._reputation_score(signal_map),
            # conversion_score intentionally left to be joined from
            # PublicationLinkMetrics.conversion_rate by the caller if desired —
            # scoring here only covers ranking signals, not analytics.
            "conversion_score": None,
            "price_competitiveness_score": None,  # no competitor-price source for ML — never fabricate
            "listing_quality_score": self._listing_quality_score(signal_map),
            "logistics_score": self._logistics_score(signal_map),
            "engagement_score": None,
        }

    def _reputation_score(self, signals: dict[str, RankingSignal]) -> float | None:
        claims = signals.get("seller_claims_rate")
        cancellations = signals.get("seller_cancellation_rate")
        gauge_unhealthy = signals.get("seller_has_unhealthy_items")

        parts = []
        if claims and claims.measured and claims.value is not None:
            # 0% claims = 100, 3%+ claims (ML's stated threshold) = 0
            parts.append(max(0.0, 100.0 - (claims.value / 3.0) * 100.0))
        if cancellations and cancellations.measured and cancellations.value is not None:
            parts.append(max(0.0, 100.0 - (cancellations.value / 10.0) * 100.0))
        if gauge_unhealthy and gauge_unhealthy.measured:
            parts.append(20.0 if gauge_unhealthy.value else 100.0)

        return round(sum(parts) / len(parts), 1) if parts else None

    def _listing_quality_score(self, signals: dict[str, RankingSignal]) -> float | None:
        completeness = signals.get("listing_completeness_pct")
        title = signals.get("title_length_score")
        photos = signals.get("photo_count")
        response_latency = signals.get("question_response_latency_minutes")
        answer_rate = signals.get("question_answer_rate_pct")

        parts = []
        if completeness and completeness.measured and completeness.value is not None:
            parts.append(completeness.value)
        if title and title.measured and title.value is not None:
            parts.append(title.value)
        if photos and photos.measured and photos.value is not None:
            parts.append(min(100.0, (photos.value / 6.0) * 100.0))
        if response_latency and response_latency.measured and response_latency.value is not None:
            parts.append(max(0.0, 100.0 - (response_latency.value / 60.0) * 100.0))
        if answer_rate and answer_rate.measured and answer_rate.value is not None:
            parts.append(answer_rate.value)

        return round(sum(parts) / len(parts), 1) if parts else None

    def _logistics_score(self, signals: dict[str, RankingSignal]) -> float | None:
        shipping = signals.get("shipping_tier")
        if not shipping or not shipping.measured or shipping.value is None:
            return None
        tier_scores = {"full": 100.0, "flex": 75.0, "standard": 40.0}
        return tier_scores.get(shipping.value, 40.0)

    def recommendation_rules(self, signal_map: dict[str, RankingSignal]) -> list[dict]:
        signals = signal_map
        rules: list[dict] = []

        claims = signals.get("seller_claims_rate")
        if claims and claims.measured and claims.value is not None and claims.value > 3.0:
            rules.append({
                "signal_key": "seller_claims_rate",
                "severity": "critical",
                "message": (
                    f"Tu tasa de reclamos es {claims.value:.1f}%, por encima del umbral "
                    "de reputación (3%) — revisá tus últimas 5 ventas."
                ),
                "current_value": f"{claims.value:.1f}%",
                "target_value": "<3%",
            })

        latency = signals.get("question_response_latency_minutes")
        if latency and latency.measured and latency.value is not None and latency.value > 60:
            rules.append({
                "signal_key": "question_response_latency_minutes",
                "severity": "warning",
                "message": (
                    f"Respondés preguntas en un promedio de {latency.value / 60:.1f}hs — "
                    "bajalo a menos de 1h para mejorar exposición."
                ),
                "current_value": f"{latency.value:.0f} min",
                "target_value": "<60 min",
            })

        completeness = signals.get("listing_completeness_pct")
        if completeness and completeness.measured and completeness.value is not None and completeness.value < 100:
            rules.append({
                "signal_key": "listing_completeness_pct",
                "severity": "warning",
                "message": (
                    f"Tu publicación tiene {completeness.value:.0f}% de atributos requeridos "
                    "completos — completalos para elegibilidad de catálogo."
                ),
                "current_value": f"{completeness.value:.0f}%",
                "target_value": "100%",
            })

        gauge = signals.get("seller_has_unhealthy_items")
        if gauge and gauge.measured and gauge.value:
            rules.append({
                "signal_key": "seller_has_unhealthy_items",
                "severity": "critical",
                "message": (
                    "ML marcó al menos una de tus publicaciones como 'unhealthy' en el medidor "
                    "de reputación — esto reduce tu exposición en búsquedas."
                ),
                "current_value": "unhealthy",
                "target_value": "healthy",
            })

        photos = signals.get("photo_count")
        if photos and photos.measured and photos.value is not None and photos.value < 6:
            rules.append({
                "signal_key": "photo_count",
                "severity": "info",
                "message": f"Tu publicación tiene {photos.value} foto(s) — ML recomienda 6 o más.",
                "current_value": str(photos.value),
                "target_value": "6+",
            })

        return rules
