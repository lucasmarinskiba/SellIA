"""Amazon Brand Store (Storefront) analytics connector — store-level.

Source: Amazon Ads "Stores Analytics" API. Requires Brand Registry enrollment
and a published Brand Store, and authenticates against the Amazon ADS API — a
credential surface SEPARATE from the SP-API one used by AmazonRankingConnector
(platform_ranking_amazon.py): a bearer token plus the
`Amazon-Advertising-API-ClientId` and `Amazon-Advertising-API-Scope` headers.
Having one connected does NOT imply the other; callers must pass the
IntegrationConnection that actually holds Ads API credentials.

Credentials: {access_token | (refresh_token, client_id, client_secret),
client_id, scope (profile id), brand_entity_id?, ads_api_base_url?}

UNVERIFIED (could not be confirmed against live docs when written — each is a
single constant/keyword list to fix, and every one fails SAFE to measured=False
rather than guessing):
  - STORES_LIST_PATH / STORE_INSIGHTS_PATH request shapes.
  - Response field names (see _CANDIDATE_KEYS) and units (fractions vs percent,
    seconds vs milliseconds — see RATES_ARE_FRACTIONS / DWELL_IS_SECONDS).
Do not trust these numbers in production until run once against a real Brand
Store; the unit assumptions are echoed in each signal's `detail`.

Known API limit: 100-day maximum date range per request.
"""

from datetime import date, timedelta
from typing import Any

import httpx

from app.core.logger import get_logger
from app.domains.seo_config.platform_ranking_base import RankingSignal
from app.domains.seo_config.platform_store_ranking_base import StorePositioningConnector

logger = get_logger(__name__)

STORES_LIST_PATH = "/v2/stores"  # TODO: confirm against Amazon Ads docs
STORE_INSIGHTS_PATH = "/stores/{brand_entity_id}/insights"  # TODO: confirm against Amazon Ads docs
WINDOW_DAYS = 30  # well inside the API's 100-day cap

# TODO: verify with a real store. Assumed: rates as fractions 0-1, dwell time in seconds.
RATES_ARE_FRACTIONS = True
DWELL_IS_SECONDS = True

_CANDIDATE_KEYS = {
    "visitors": ("visitors", "totalVisitors", "uniqueVisitors"),
    "quality_score_level": ("qualityScoreLevel", "quality_score_level"),
    "dwell_time": ("dwellTime", "avgDwellTime", "dwell_time"),
    "bounce_rate": ("bounceRate", "bounce_rate"),
    "new_to_store": ("newToStoreRate", "newToStorePercentage", "newToStorePct", "new_to_store_rate"),
}

# Heuristic references — Amazon publishes no target for these; labeled as such wherever used.
DWELL_TARGET_S = 60.0
SECTION_CTR_TARGET_PCT = 5.0
BOUNCE_WARN_PCT = 60.0
SECTION_CTR_LOW_PCT = 1.0
DWELL_LOW_S = 15.0


def _find_number(node: Any, keys: tuple[str, ...]) -> float | None:
    """Depth-first search for the first numeric value under any of `keys`."""
    if isinstance(node, dict):
        for k in keys:
            if isinstance(node.get(k), (int, float)) and not isinstance(node.get(k), bool):
                return float(node[k])
        for child in node.values():
            found = _find_number(child, keys)
            if found is not None:
                return found
    elif isinstance(node, list):
        for child in node:
            found = _find_number(child, keys)
            if found is not None:
                return found
    return None


def _find_value(node: Any, keys: tuple[str, ...]) -> Any | None:
    if isinstance(node, dict):
        for k in keys:
            if k in node and node[k] is not None:
                return node[k]
        for child in node.values():
            found = _find_value(child, keys)
            if found is not None:
                return found
    elif isinstance(node, list):
        for child in node:
            found = _find_value(child, keys)
            if found is not None:
                return found
    return None


class AmazonStoreRankingConnector(StorePositioningConnector):
    """Fetch storefront-level performance signals from Amazon's Stores Analytics API."""

    platform_name = "amazon"
    DEFAULT_BASE_URL = "https://advertising-api.amazon.com"
    LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"

    def __init__(self, credentials: dict[str, Any]):
        super().__init__(credentials)
        self.access_token: str | None = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.scope = credentials.get("scope") or credentials.get("profile_id")
        self.brand_entity_id = credentials.get("brand_entity_id")
        self.base_url = credentials.get("ads_api_base_url", self.DEFAULT_BASE_URL)
        self._refreshed = False

    async def _headers(self, client: httpx.AsyncClient) -> dict[str, str]:
        if self.refresh_token and self.client_id and self.client_secret and not self._refreshed:
            resp = await client.post(
                self.LWA_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=10,
            )
            resp.raise_for_status()
            self.access_token = resp.json()["access_token"]
            self._refreshed = True
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Amazon-Advertising-API-ClientId": self.client_id or "",
        }
        if self.scope:
            headers["Amazon-Advertising-API-Scope"] = str(self.scope)
        return headers

    async def validate_credentials(self) -> bool:
        if not (self.access_token or self.refresh_token) or not self.client_id:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}{STORES_LIST_PATH}", headers=await self._headers(client), timeout=10
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Amazon store ranking credentials validation failed: {str(e)[:100]}")
            return False

    async def get_store_signals(self, store_external_id: str | None = None) -> list[RankingSignal]:
        brand_entity_id = store_external_id or self.brand_entity_id
        if not brand_entity_id:
            return self._unavailable("falta brand_entity_id (ni en las credenciales ni como parámetro)")

        try:
            async with httpx.AsyncClient() as client:
                end = date.today()
                start = end - timedelta(days=WINDOW_DAYS)
                resp = await client.get(
                    f"{self.base_url}{STORE_INSIGHTS_PATH.format(brand_entity_id=brand_entity_id)}",
                    headers=await self._headers(client),
                    params={"startDate": start.isoformat(), "endDate": end.isoformat()},
                    timeout=20,
                )
            if resp.status_code != 200:
                return self._unavailable(
                    f"Stores Analytics API devolvió {resp.status_code} (¿Brand Registry / Store publicada / scope de Ads API?)"
                )
            body = resp.json()
        except Exception as e:
            logger.warning(f"Amazon store ranking: insights fetch failed: {str(e)[:100]}")
            return self._unavailable(str(e)[:100])

        unit_note = (
            f"asumido: tasas en fracción 0-1={RATES_ARE_FRACTIONS}, dwell en segundos={DWELL_IS_SECONDS} (verificar con una tienda real)"
        )
        signals: list[RankingSignal] = []

        visitors = _find_number(body, _CANDIDATE_KEYS["visitors"])
        signals.append(RankingSignal(
            "visitors", visitors, measured=visitors is not None,
            detail="visitantes de la tienda en la ventana; sin escala absoluta para puntuarlo (solo informativo)",
        ))

        level = _find_value(body, _CANDIDATE_KEYS["quality_score_level"])
        signals.append(RankingSignal(
            "quality_score_level", level, measured=level is not None,
            detail="escala no confirmada; solo informativo, no se usa para puntuar",
        ))

        dwell = _find_number(body, _CANDIDATE_KEYS["dwell_time"])
        dwell_s = None if dwell is None else (dwell if DWELL_IS_SECONDS else dwell / 1000.0)
        signals.append(RankingSignal(
            "dwell_time_seconds", None if dwell_s is None else round(dwell_s, 1), measured=dwell_s is not None,
            unit="s", detail=unit_note,
        ))

        bounce = _find_number(body, _CANDIDATE_KEYS["bounce_rate"])
        signals.append(self._pct_signal("bounce_rate_pct", bounce, unit_note))

        new_to_store = _find_number(body, _CANDIDATE_KEYS["new_to_store"])
        signals.append(self._pct_signal("new_to_store_pct", new_to_store, unit_note))

        signals.append(self._section_ctr_signal(body, unit_note))
        return signals

    def _pct_signal(self, key: str, raw: float | None, detail: str) -> RankingSignal:
        if raw is None:
            return RankingSignal(key, None, measured=False, unit="%", detail="campo no encontrado en la respuesta")
        pct = raw * 100.0 if RATES_ARE_FRACTIONS else raw
        return RankingSignal(key, round(pct, 2), measured=True, unit="%", detail=detail)

    def _section_ctr_signal(self, body: Any, detail: str) -> RankingSignal:
        """CTR aggregated over a `sections` list: sum(clicks) / sum(impressions)."""
        sections = _find_value(body, ("sections", "sectionPerformance", "sectionalPerformance"))
        clicks = impressions = 0.0
        if isinstance(sections, list):
            for section in sections:
                if not isinstance(section, dict):
                    continue
                c = _find_number(section, ("clicks",))
                i = _find_number(section, ("viewableImpressions", "impressions", "renders"))
                if c is not None and i:
                    clicks += c
                    impressions += i
        if impressions <= 0:
            return RankingSignal(
                "section_ctr_pct", None, measured=False, unit="%",
                detail="sin datos de secciones en la respuesta (o formato no reconocido)",
            )
        return RankingSignal(
            "section_ctr_pct", round(clicks / impressions * 100, 2), measured=True, unit="%",
            detail="clicks / impresiones visibles agregado sobre las secciones de la tienda",
        )

    def _unavailable(self, reason: str) -> list[RankingSignal]:
        return [
            RankingSignal(k, None, measured=False, detail=reason)
            for k in ("visitors", "dwell_time_seconds", "bounce_rate_pct", "new_to_store_pct", "section_ctr_pct")
        ]

    # ── Scoring ──

    @staticmethod
    def _usable(signal: RankingSignal | None) -> bool:
        return bool(signal and signal.measured and signal.value is not None)

    def score_signals(self, signal_map: dict[str, RankingSignal]) -> dict[str, float | None]:
        s = signal_map

        engagement_parts = []
        dwell, bounce = s.get("dwell_time_seconds"), s.get("bounce_rate_pct")
        if self._usable(dwell):
            engagement_parts.append(min(100.0, dwell.value / DWELL_TARGET_S * 100.0))  # heuristic reference
        if self._usable(bounce):
            engagement_parts.append(max(0.0, 100.0 - bounce.value))

        new_visitors, ctr = s.get("new_to_store_pct"), s.get("section_ctr_pct")
        return {
            # Raw visitor counts and the quality-score level have no absolute scale to score
            # against without a per-business baseline — left None rather than invented.
            "traffic_score": None,
            "engagement_score": round(sum(engagement_parts) / len(engagement_parts), 1) if engagement_parts else None,
            "new_visitor_score": round(min(100.0, new_visitors.value), 1) if self._usable(new_visitors) else None,
            "content_performance_score": (
                round(min(100.0, ctr.value / SECTION_CTR_TARGET_PCT * 100.0), 1) if self._usable(ctr) else None
            ),
        }

    def recommendation_rules(self, signal_map: dict[str, RankingSignal]) -> list[dict]:
        s = signal_map
        rules: list[dict] = []

        bounce = s.get("bounce_rate_pct")
        if self._usable(bounce) and bounce.value > BOUNCE_WARN_PCT:
            rules.append({
                "signal_key": "bounce_rate_pct", "severity": "warning",
                "message": (
                    f"El {bounce.value:.0f}% de los visitantes abandona tu Brand Store sin navegar — "
                    "revisá la home de la tienda: banner, productos destacados y navegación. (umbral heurístico, no oficial de Amazon)"
                ),
                "current_value": f"{bounce.value:.0f}%", "target_value": f"<{BOUNCE_WARN_PCT:.0f}%",
            })

        dwell = s.get("dwell_time_seconds")
        if self._usable(dwell) and dwell.value < DWELL_LOW_S:
            rules.append({
                "signal_key": "dwell_time_seconds", "severity": "info",
                "message": (
                    f"Tus visitantes pasan {dwell.value:.0f}s en la tienda — agregá secciones con video, "
                    "colecciones y contenido que invite a explorar. (referencia heurística)"
                ),
                "current_value": f"{dwell.value:.0f}s", "target_value": f">{DWELL_LOW_S:.0f}s",
            })

        ctr = s.get("section_ctr_pct")
        if self._usable(ctr) and ctr.value < SECTION_CTR_LOW_PCT:
            rules.append({
                "signal_key": "section_ctr_pct", "severity": "info",
                "message": (
                    f"El CTR de tus secciones es {ctr.value:.2f}% — probá otro orden de secciones o imágenes/CTA más claros "
                    "en las de menor clics. (referencia heurística)"
                ),
                "current_value": f"{ctr.value:.2f}%", "target_value": f">{SECTION_CTR_LOW_PCT:.0f}%",
            })

        return rules
