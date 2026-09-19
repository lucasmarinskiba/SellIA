"""Amazon (SP-API) ranking-signal connector — per-listing.

Amazon has never published its search-ranking formula ("A9"/"A10" are
industry nicknames, not Amazon terminology). What Amazon DOES officially
document, and what this connector fetches, are the seller-performance
metrics that gate Buy Box / Featured Offer eligibility (Order Defect Rate,
Late Shipment Rate, Valid Tracking Rate), the Featured Offer Expected Price,
listing status (buyable / suppressed), and catalog-content completeness.
Weights and thresholds used in scoring are community-consensus heuristics
unless a comment says otherwise.

Credentials: SP-API uses an LWA refresh-token flow (same shape as
channels/connectors/amazon.py — pattern-matched, deliberately not imported,
because that class serves orders/messaging and coupling would risk
regressions there). Store-level (Brand Store) analytics use a DIFFERENT
credential surface (Amazon Ads API) — see platform_store_ranking_amazon.py.

Every sub-fetch is independently try/excepted: a missing SP-API role
(Pricing, Inventory and Order Tracking, Product Listing, Amazon
Fulfillment) yields measured=False for that signal only, never a crash.

Reviews (rating/count) are intentionally NOT a signal: no SP-API endpoint
for review metrics was confirmed, and this system does not fabricate signals.
"""

import asyncio
import gzip
import json
import re
from typing import Any

import httpx

from app.core.logger import get_logger
from app.domains.seo_config.platform_ranking_base import PlatformRankingConnector, RankingSignal

logger = get_logger(__name__)

_ASIN_URL_RE = re.compile(r"/(?:dp|gp/product)/([A-Z0-9]{10})")
_ASIN_BARE_RE = re.compile(r"^[A-Z0-9]{10}$")

# TODO: confirm this reportType against developer-docs.amazon.com/sp-api/docs/report-type-values-*
# before relying on it in production — it could not be verified when this was written.
SELLER_PERFORMANCE_REPORT_TYPE = "GET_V2_SELLER_PERFORMANCE_REPORT"

# TODO: verify with a real account. Amazon's performance report is assumed to express
# rates as fractions (0.01 = 1%). If real data shows percent values, flip this to False.
REPORT_RATES_ARE_FRACTIONS = True

ODR_THRESHOLD_PCT = 1.0  # Amazon-documented: keep Order Defect Rate below 1%
LSR_THRESHOLD_PCT = 4.0  # Amazon-documented: keep Late Shipment Rate below 4%
VTR_TARGET_PCT = 95.0  # Amazon-documented: keep Valid Tracking Rate above 95%

# Heuristic content targets (community best practice, NOT Amazon ranking thresholds).
TARGET_BULLETS = 5
TARGET_IMAGES = 7


def extract_asin(external_id: str) -> str | None:
    """Accept a bare ASIN or an Amazon product URL (/dp/ASIN, /gp/product/ASIN)."""
    if not external_id:
        return None
    match = _ASIN_URL_RE.search(external_id)
    if match:
        return match.group(1)
    if _ASIN_BARE_RE.match(external_id.strip()):
        return external_id.strip()
    return None


class AmazonRankingConnector(PlatformRankingConnector):
    """Fetch ranking/algorithm signals for one Amazon listing via SP-API."""

    platform_name = "amazon"
    DEFAULT_BASE_URL = "https://sellingpartnerapi-na.amazon.com"
    LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"

    def __init__(self, credentials: dict[str, Any]):
        super().__init__(credentials)
        self.refresh_token = credentials.get("refresh_token")
        self.lwa_app_id = credentials.get("lwa_app_id")
        self.lwa_client_secret = credentials.get("lwa_client_secret")
        self.marketplace_id = credentials.get("marketplace_id", "ATVPDKIKX0DER")
        self.seller_id = credentials.get("seller_id")
        self.base_url = credentials.get("sp_api_base_url", self.DEFAULT_BASE_URL)
        self.report_poll_attempts = int(credentials.get("report_poll_attempts", 8))
        self.report_poll_interval_s = float(credentials.get("report_poll_interval_s", 5))
        self._access_token: str | None = credentials.get("access_token")
        self._token_refreshed = False

    async def _ensure_token(self, client: httpx.AsyncClient) -> str | None:
        can_refresh = self.refresh_token and self.lwa_app_id and self.lwa_client_secret
        if can_refresh and not self._token_refreshed:
            resp = await client.post(
                self.LWA_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.lwa_app_id,
                    "client_secret": self.lwa_client_secret,
                },
                timeout=10,
            )
            resp.raise_for_status()
            self._access_token = resp.json()["access_token"]
            self._token_refreshed = True
        return self._access_token

    async def _headers(self, client: httpx.AsyncClient) -> dict[str, str]:
        token = await self._ensure_token(client)
        return {"x-amz-access-token": token or "", "Content-Type": "application/json"}

    async def validate_credentials(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                headers = await self._headers(client)
                if not headers["x-amz-access-token"]:
                    return False
                resp = await client.get(
                    f"{self.base_url}/sellers/v1/marketplaceParticipations",
                    headers=headers,
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Amazon ranking credentials validation failed: {str(e)[:100]}")
            return False

    async def get_ranking_signals(self, external_id: str) -> list[RankingSignal]:
        asin = extract_asin(external_id)
        if not asin:
            return [RankingSignal(
                "asin_unresolved", None, measured=False,
                detail=f"no se pudo extraer un ASIN de '{external_id[:80]}'",
            )]

        signals: list[RankingSignal] = []
        async with httpx.AsyncClient() as client:
            listing = await self._fetch_listing(client, asin)
            sku = (listing or {}).get("sku")

            signals.extend(await self._account_health_signals(client))
            signals.extend(self._listing_status_signals(listing))
            signals.extend(await self._price_competitiveness_signals(client, sku, listing))
            signals.extend(await self._catalog_signals(client, asin))

        return signals

    # ── Fetchers ──

    async def _get_json(
        self, client: httpx.AsyncClient, path: str, params: dict | None = None
    ) -> tuple[int, Any]:
        resp = await client.get(
            f"{self.base_url}{path}",
            headers=await self._headers(client),
            params=params,
            timeout=15,
        )
        try:
            body = resp.json()
        except Exception:
            body = None
        return resp.status_code, body

    async def _fetch_listing(self, client: httpx.AsyncClient, asin: str) -> dict[str, Any] | None:
        """Resolve the seller's own listing (SKU, price, stock, status) for an ASIN."""
        if not self.seller_id:
            return None
        try:
            status, body = await self._get_json(
                client,
                f"/listings/2021-08-01/items/{self.seller_id}",
                {
                    "marketplaceIds": self.marketplace_id,
                    "identifiers": asin,
                    "identifiersType": "ASIN",
                    "includedData": "summaries,offers,fulfillmentAvailability,issues",
                },
            )
            if status == 200 and body and body.get("items"):
                return body["items"][0]
            logger.warning(f"Amazon ranking: listing lookup for {asin} returned {status}")
        except Exception as e:
            logger.warning(f"Amazon ranking: listing lookup failed: {str(e)[:100]}")
        return None

    async def _account_health_signals(self, client: httpx.AsyncClient) -> list[RankingSignal]:
        """ODR / LSR / VTR from the seller-performance report.

        This is the one genuinely asynchronous fetch (createReport -> poll ->
        download). If the report isn't ready within the poll budget the metrics
        come back measured=False and the next nightly run retries — never a
        blocking wait, never a fabricated number.
        """
        keys = ("account_odr_pct", "account_lsr_pct", "account_vtr_pct")
        try:
            headers = await self._headers(client)
            create = await client.post(
                f"{self.base_url}/reports/2021-06-30/reports",
                headers=headers,
                json={
                    "reportType": SELLER_PERFORMANCE_REPORT_TYPE,
                    "marketplaceIds": [self.marketplace_id],
                },
                timeout=15,
            )
            if create.status_code not in (200, 202):
                return self._health_unavailable(
                    keys, f"createReport devolvió {create.status_code} (¿falta el rol de Selling Partner Insights?)"
                )
            report_id = create.json().get("reportId")

            document_id = None
            for _ in range(self.report_poll_attempts):
                status_code, body = await self._get_json(client, f"/reports/2021-06-30/reports/{report_id}")
                processing = (body or {}).get("processingStatus")
                if status_code == 200 and processing == "DONE":
                    document_id = body.get("reportDocumentId")
                    break
                if processing in ("CANCELLED", "FATAL"):
                    return self._health_unavailable(keys, f"reporte terminó en estado {processing}")
                await asyncio.sleep(self.report_poll_interval_s)

            if not document_id:
                return self._health_unavailable(
                    keys, "reporte de performance no listo dentro del presupuesto de espera; se reintenta en la próxima corrida nocturna"
                )

            doc = await self._download_report_document(client, document_id)
            if doc is None:
                return self._health_unavailable(keys, "no se pudo descargar/parsear el documento del reporte")

            odr = self._find_rate(doc, "orderDefectRate")
            lsr = self._find_rate(doc, "lateShipmentRate")
            vtr = self._find_rate(doc, "validTrackingRate")

            unit_note = (
                "el reporte se asume en fracción 0-1 (verificar con cuenta real)"
                if REPORT_RATES_ARE_FRACTIONS else "el reporte se asume en porcentaje"
            )
            return [
                self._rate_signal("account_odr_pct", odr, f"Amazon: mantener por debajo de {ODR_THRESHOLD_PCT}%. {unit_note}"),
                self._rate_signal("account_lsr_pct", lsr, f"Amazon: mantener por debajo de {LSR_THRESHOLD_PCT}%. {unit_note}"),
                self._rate_signal("account_vtr_pct", vtr, f"Amazon: mantener por encima de {VTR_TARGET_PCT}%. {unit_note}"),
            ]
        except Exception as e:
            logger.warning(f"Amazon ranking: account health fetch failed: {str(e)[:100]}")
            return self._health_unavailable(keys, str(e)[:100])

    def _health_unavailable(self, keys: tuple[str, ...], detail: str) -> list[RankingSignal]:
        return [RankingSignal(k, None, measured=False, unit="%", detail=detail) for k in keys]

    def _rate_signal(self, key: str, raw: float | None, detail: str) -> RankingSignal:
        if raw is None:
            return RankingSignal(
                key, None, measured=False, unit="%",
                detail="métrica no encontrada en el reporte (¿formato distinto al esperado?)",
            )
        pct = raw * 100.0 if REPORT_RATES_ARE_FRACTIONS else raw
        return RankingSignal(key, round(pct, 2), measured=True, unit="%", detail=detail)

    async def _download_report_document(self, client: httpx.AsyncClient, document_id: str) -> Any | None:
        status, body = await self._get_json(client, f"/reports/2021-06-30/documents/{document_id}")
        if status != 200 or not body or not body.get("url"):
            return None
        resp = await client.get(body["url"], timeout=30)  # pre-signed URL, no SP-API auth header
        if resp.status_code != 200:
            return None
        raw = resp.content
        if body.get("compressionAlgorithm") == "GZIP":
            raw = gzip.decompress(raw)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _find_rate(self, node: Any, key: str) -> float | None:
        """Depth-first search for `key` whose value is a number or {"rate": number}.
        Fails safe: unknown shape -> None, never a guessed value."""
        if isinstance(node, dict):
            if key in node:
                value = node[key]
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, dict):
                    rate = value.get("rate")
                    if isinstance(rate, (int, float)):
                        return float(rate)
                    for sub in value.values():
                        if isinstance(sub, dict) and isinstance(sub.get("rate"), (int, float)):
                            return float(sub["rate"])
            for child in node.values():
                found = self._find_rate(child, key)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for child in node:
                found = self._find_rate(child, key)
                if found is not None:
                    return found
        return None

    def _listing_status_signals(self, listing: dict[str, Any] | None) -> list[RankingSignal]:
        if not listing:
            return [
                RankingSignal("listing_buyable", None, measured=False,
                              detail="no se pudo resolver el listing del vendedor (¿falta seller_id o el rol Product Listing?)"),
                RankingSignal("in_stock", None, measured=False, detail="listing no resuelto"),
            ]

        out: list[RankingSignal] = []
        summaries = listing.get("summaries") or []
        statuses = (summaries[0].get("status") if summaries else None) or []
        out.append(RankingSignal(
            "listing_buyable", "BUYABLE" in statuses, measured=bool(summaries),
            detail="un listing no BUYABLE (suprimido/inactivo) pierde elegibilidad de Buy Box",
        ))

        issues = listing.get("issues") or []
        out.append(RankingSignal(
            "listing_issues_count", len(issues), measured=True,
            detail="issues de calidad/compliance reportados por Amazon para este listing",
        ))

        availability = listing.get("fulfillmentAvailability") or []
        if availability:
            qty = availability[0].get("quantity")
            channel = availability[0].get("fulfillmentChannelCode", "")
            out.append(RankingSignal(
                "in_stock", (qty or 0) > 0, measured=qty is not None,
                detail=f"cantidad disponible: {qty}",
            ))
            out.append(RankingSignal(
                "fulfillment_method", "fbm" if channel == "DEFAULT" else "fba", measured=bool(channel),
                detail="FBA/SFP suele recibir trato preferencial (consenso de la comunidad, no documentado por Amazon)",
            ))
        else:
            out.append(RankingSignal("in_stock", None, measured=False, detail="sin datos de fulfillmentAvailability"))
        return out

    async def _price_competitiveness_signals(
        self, client: httpx.AsyncClient, sku: str | None, listing: dict[str, Any] | None
    ) -> list[RankingSignal]:
        offers = (listing or {}).get("offers") or []
        try:
            current_price = float(offers[0]["price"]["amount"]) if offers else None
        except Exception:
            current_price = None

        if not sku or current_price is None:
            return [RankingSignal(
                "price_vs_foep_ratio", None, measured=False,
                detail="falta SKU o precio actual del listing para comparar con el FOEP",
            )]

        try:
            resp = await client.post(
                f"{self.base_url}/batches/products/pricing/2022-05-01/offer/featuredOfferExpectedPrice",
                headers=await self._headers(client),
                json={"requests": [{
                    "uri": "/products/pricing/2022-05-01/offer/featuredOfferExpectedPrice",
                    "method": "GET",
                    "marketplaceId": self.marketplace_id,
                    "sku": sku,
                }]},
                timeout=15,
            )
            if resp.status_code != 200:
                return [RankingSignal(
                    "price_vs_foep_ratio", None, measured=False,
                    detail=f"Product Pricing API devolvió {resp.status_code} (¿falta el rol Pricing?)",
                )]

            responses = resp.json().get("responses") or []
            results = ((responses[0].get("body") or {}).get("featuredOfferExpectedPriceResults") or []) if responses else []
            foep = None
            if results:
                foep = float(((results[0].get("featuredOfferExpectedPrice") or {}).get("listingPrice") or {}).get("amount"))

            if not foep:
                return [RankingSignal(
                    "price_vs_foep_ratio", None, measured=False,
                    detail="Amazon no devolvió un Featured Offer Expected Price para este SKU",
                )]

            return [
                RankingSignal("foep_price", foep, measured=True,
                              detail="precio al que Amazon estima que podés ganar el Featured Offer (Buy Box)"),
                RankingSignal("current_price", current_price, measured=True),
                RankingSignal("price_vs_foep_ratio", round(current_price / foep, 4), measured=True,
                              detail="<=1.0 significa precio en o por debajo del FOEP"),
            ]
        except Exception as e:
            logger.warning(f"Amazon ranking: FOEP fetch failed: {str(e)[:100]}")
            return [RankingSignal("price_vs_foep_ratio", None, measured=False, detail=str(e)[:100])]

    async def _catalog_signals(self, client: httpx.AsyncClient, asin: str) -> list[RankingSignal]:
        try:
            status, body = await self._get_json(
                client,
                f"/catalog/2022-04-01/items/{asin}",
                {"marketplaceIds": self.marketplace_id, "includedData": "attributes,images,salesRanks,summaries"},
            )
            if status != 200 or not body:
                return [RankingSignal(
                    "catalog_completeness_pct", None, measured=False,
                    detail=f"Catalog Items API devolvió {status}",
                )]

            summaries = body.get("summaries") or []
            title = (summaries[0].get("itemName") if summaries else "") or ""
            bullets = (body.get("attributes") or {}).get("bullet_point") or []
            image_groups = body.get("images") or []
            images = image_groups[0].get("images", []) if image_groups else []
            image_count = len({img.get("variant") or img.get("link") for img in images})

            checks = [
                1.0 if title else 0.0,
                min(1.0, len(bullets) / TARGET_BULLETS),
                min(1.0, image_count / TARGET_IMAGES),
            ]
            completeness = round(sum(checks) / len(checks) * 100, 1)

            out = [
                RankingSignal("title_length", len(title), measured=True, unit="chars"),
                RankingSignal("bullet_count", len(bullets), measured=True,
                              detail=f"objetivo heurístico: {TARGET_BULLETS} (no umbral oficial de ranking)"),
                RankingSignal("image_count", image_count, measured=True,
                              detail=f"objetivo heurístico: {TARGET_IMAGES} (no umbral oficial de ranking)"),
                RankingSignal("catalog_completeness_pct", completeness, measured=True, unit="%",
                              detail="promedio de título presente, bullets y cantidad de imágenes vs objetivos heurísticos"),
            ]

            ranks = body.get("salesRanks") or []
            bsr = None
            if ranks:
                display = (ranks[0].get("displayGroupRanks") or ranks[0].get("classificationRanks") or [])
                if display:
                    bsr = display[0].get("rank")
            out.append(RankingSignal(
                "best_sellers_rank", bsr, measured=bsr is not None,
                detail="solo informativo: sin escala absoluta contra la cual puntuarlo",
            ))
            return out
        except Exception as e:
            logger.warning(f"Amazon ranking: catalog fetch failed: {str(e)[:100]}")
            return [RankingSignal("catalog_completeness_pct", None, measured=False, detail=str(e)[:100])]

    # ── Scoring ──

    def score_signals(self, signal_map: dict[str, RankingSignal]) -> dict[str, float | None]:
        return {
            "reputation_score": self._reputation_score(signal_map),
            "conversion_score": None,
            "price_competitiveness_score": self._price_score(signal_map),
            "listing_quality_score": self._listing_quality_score(signal_map),
            "logistics_score": self._logistics_score(signal_map),
            "engagement_score": None,
        }

    @staticmethod
    def _usable(signal: RankingSignal | None) -> bool:
        return bool(signal and signal.measured and signal.value is not None)

    def _reputation_score(self, s: dict[str, RankingSignal]) -> float | None:
        parts = []
        odr, lsr, vtr = s.get("account_odr_pct"), s.get("account_lsr_pct"), s.get("account_vtr_pct")
        if self._usable(odr):
            parts.append(max(0.0, 100.0 - (odr.value / ODR_THRESHOLD_PCT) * 100.0))
        if self._usable(lsr):
            parts.append(max(0.0, 100.0 - (lsr.value / LSR_THRESHOLD_PCT) * 100.0))
        if self._usable(vtr):
            parts.append(100.0 if vtr.value >= VTR_TARGET_PCT else max(0.0, 100.0 - (VTR_TARGET_PCT - vtr.value) * 5.0))
        return round(sum(parts) / len(parts), 1) if parts else None

    def _price_score(self, s: dict[str, RankingSignal]) -> float | None:
        ratio = s.get("price_vs_foep_ratio")
        if not self._usable(ratio):
            return None
        if ratio.value <= 1.0:
            return 100.0
        # Heuristic: each 1% above the FOEP costs 5 points, floor 0.
        return round(max(0.0, 100.0 - (ratio.value - 1.0) * 100.0 * 5.0), 1)

    def _listing_quality_score(self, s: dict[str, RankingSignal]) -> float | None:
        parts = []
        completeness = s.get("catalog_completeness_pct")
        buyable = s.get("listing_buyable")
        if self._usable(completeness):
            parts.append(completeness.value)
        if self._usable(buyable):
            parts.append(100.0 if buyable.value else 0.0)
        return round(sum(parts) / len(parts), 1) if parts else None

    def _logistics_score(self, s: dict[str, RankingSignal]) -> float | None:
        parts = []
        in_stock, method = s.get("in_stock"), s.get("fulfillment_method")
        if self._usable(in_stock):
            parts.append(100.0 if in_stock.value else 0.0)
        if self._usable(method):
            parts.append(100.0 if method.value == "fba" else 60.0)  # heuristic, see fulfillment_method detail
        return round(sum(parts) / len(parts), 1) if parts else None

    def recommendation_rules(self, signal_map: dict[str, RankingSignal]) -> list[dict]:
        s = signal_map
        rules: list[dict] = []

        odr = s.get("account_odr_pct")
        if self._usable(odr) and odr.value > ODR_THRESHOLD_PCT:
            rules.append({
                "signal_key": "account_odr_pct", "severity": "critical",
                "message": (
                    f"Tu ODR es {odr.value:.2f}%, por encima del umbral de {ODR_THRESHOLD_PCT:.0f}% de Amazon — "
                    "podés perder el Buy Box hasta 60 días. Revisá tus últimos pedidos con defectos."
                ),
                "current_value": f"{odr.value:.2f}%", "target_value": f"<{ODR_THRESHOLD_PCT:.0f}%",
            })

        lsr = s.get("account_lsr_pct")
        if self._usable(lsr) and lsr.value > LSR_THRESHOLD_PCT:
            rules.append({
                "signal_key": "account_lsr_pct", "severity": "warning",
                "message": (
                    f"Tu tasa de envíos tardíos es {lsr.value:.2f}%, por encima del {LSR_THRESHOLD_PCT:.0f}% que exige Amazon — "
                    "ajustá tu tiempo de handling o tu capacidad de despacho."
                ),
                "current_value": f"{lsr.value:.2f}%", "target_value": f"<{LSR_THRESHOLD_PCT:.0f}%",
            })

        vtr = s.get("account_vtr_pct")
        if self._usable(vtr) and vtr.value < VTR_TARGET_PCT:
            rules.append({
                "signal_key": "account_vtr_pct", "severity": "warning",
                "message": (
                    f"Solo {vtr.value:.1f}% de tus paquetes tiene tracking válido (Amazon pide >{VTR_TARGET_PCT:.0f}%) — "
                    "cargá el tracking con carrier reconocido en cada envío."
                ),
                "current_value": f"{vtr.value:.1f}%", "target_value": f">{VTR_TARGET_PCT:.0f}%",
            })

        buyable = s.get("listing_buyable")
        if self._usable(buyable) and not buyable.value:
            rules.append({
                "signal_key": "listing_buyable", "severity": "critical",
                "message": "Tu listing no está en estado BUYABLE (suprimido o inactivo) — no puede ganar el Buy Box hasta que lo resuelvas en Seller Central.",
                "current_value": "no buyable", "target_value": "BUYABLE",
            })

        in_stock = s.get("in_stock")
        if self._usable(in_stock) and not in_stock.value:
            rules.append({
                "signal_key": "in_stock", "severity": "critical",
                "message": "Tu listing está sin stock — Amazon suprime la visibilidad de ofertas sin inventario. Reponé cantidad disponible.",
                "current_value": "sin stock", "target_value": "stock > 0",
            })

        ratio, foep = s.get("price_vs_foep_ratio"), s.get("foep_price")
        if self._usable(ratio) and ratio.value > 1.0 and self._usable(foep):
            rules.append({
                "signal_key": "price_vs_foep_ratio", "severity": "warning",
                "message": (
                    f"Tu precio está {(ratio.value - 1) * 100:.1f}% por encima del precio esperado para ganar el Featured Offer "
                    f"({foep.value:.2f}) — bajarlo puede recuperar el Buy Box."
                ),
                "current_value": f"{ratio.value:.3f}x", "target_value": "<=1.000x",
            })

        issues = s.get("listing_issues_count")
        if self._usable(issues) and issues.value > 0:
            rules.append({
                "signal_key": "listing_issues_count", "severity": "warning",
                "message": f"Amazon reporta {issues.value} issue(s) en tu listing — resolvelos en Seller Central para evitar supresión.",
                "current_value": str(issues.value), "target_value": "0",
            })

        completeness = s.get("catalog_completeness_pct")
        if self._usable(completeness) and completeness.value < 100:
            bullets, images = s.get("bullet_count"), s.get("image_count")
            b = bullets.value if self._usable(bullets) else "?"
            i = images.value if self._usable(images) else "?"
            rules.append({
                "signal_key": "catalog_completeness_pct", "severity": "info",
                "message": (
                    f"Tu contenido tiene {b} bullet(s) e {i} imagen(es); apuntá a {TARGET_BULLETS} bullets y {TARGET_IMAGES} imágenes "
                    "(objetivo heurístico) para mejorar conversión."
                ),
                "current_value": f"{completeness.value:.0f}%", "target_value": "100%",
            })

        return rules
