"""Hotmart ranking-signal connector (PROXY — read this before trusting a value).

Hotmart's affiliate marketplace does rank/filter products by two internal
composites, both officially documented in Hotmart's Help Center:
  - Temperature (0-150): sales frequency/recency + refund rate + Blueprint
    score + undisclosed indicators.
  - Blueprint: a quality qualification (%) across ~11 criteria; products under
    60% are not listed in the Affiliate Marketplace at all.
NEITHER is exposed by any Hotmart API. This connector therefore does NOT read
them. It reconstructs honest proxies from the Sales API — approval, refund and
chargeback rates and sales velocity aggregated from real transactions. Those
numbers are real (measured=True) but they are NOT Hotmart's Temperature or
Blueprint, and every signal's `detail` says so.

Deliberately absent:
  - EPC (earnings per click): a ClickBank-style concept that does not exist in
    Hotmart, so no signal is invented for it.
  - Listing/content quality: Hotmart offers third-party sellers no API for
    product content, so listing_quality_score stays None.

The Sales API's default response is not guaranteed to include refunded or
charged-back transactions, so each status is counted with its own explicit
filter instead of relying on the default — otherwise refund/chargeback rates
would silently read 0%. If any status count fails, all rate signals are
reported measured=False rather than published from partial data.

Credentials: OAuth2 client_credentials, same shape as
channels/connectors/hotmart.py (pattern-matched, not imported, so this
ranking code can't regress the payments/webhook connector).
"""

import asyncio
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.logger import get_logger
from app.domains.seo_config.platform_ranking_base import PlatformRankingConnector, RankingSignal

logger = get_logger(__name__)

PROXY_NOTE = (
    "proxy calculado sobre transacciones reales — NO es la Temperature/Blueprint real de Hotmart, "
    "índices internos que ninguna API expone"
)

# Status groups (names per Hotmart's Sales API transaction_status values).
PAID_RETAINED = ("APPROVED", "COMPLETE")
REFUNDED = ("REFUNDED", "PARTIALLY_REFUNDED")
CHARGEBACK = ("CHARGEBACK", "PROTESTED")
NOT_COMPLETED = ("CANCELLED", "EXPIRED", "BLOCKED")
ALL_STATUSES = PAID_RETAINED + REFUNDED + CHARGEBACK + NOT_COMPLETED

# Heuristic thresholds — Hotmart publishes no official numeric thresholds for these derived rates.
REFUND_WARN_PCT = 10.0
CHARGEBACK_CRITICAL_PCT = 1.0  # card-network monitoring programs treat ~1% as the alarm line, not a Hotmart rule
APPROVAL_INFO_PCT = 50.0

_PRODUCT_ID_PARAM_RE = re.compile(r"[?&](?:product_id|prod)=(\d+)")


def extract_product_id(external_id: str) -> str | None:
    """Accept a bare numeric product id, or a URL carrying ?product_id=NNN.

    Hotmart checkout/marketplace URLs are not documented to embed the numeric
    product id, so nothing else is guessed — a wrong id would produce
    misleading zero-sales metrics. Callers fall back to account-level.
    """
    if not external_id:
        return None
    value = external_id.strip()
    if value.isdigit():
        return value
    match = _PRODUCT_ID_PARAM_RE.search(value)
    return match.group(1) if match else None


class HotmartRankingConnector(PlatformRankingConnector):
    """Fetch proxy ranking signals for a Hotmart product (or the whole account)."""

    platform_name = "hotmart"
    TOKEN_URL = "https://api-sec-vlc.hotmart.com/security/oauth/token"
    SALES_API = "https://developers.hotmart.com/payments/api/v1"
    WINDOW_DAYS = 30
    FALLBACK_MAX_PAGES = 10

    def __init__(self, credentials: dict[str, Any]):
        super().__init__(credentials)
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.basic_token = credentials.get("basic_token")
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        if not self.basic_token:
            raise ValueError("Faltan credenciales de Hotmart (basic_token)")
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        resp = await client.post(
            self.TOKEN_URL,
            params={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {self.basic_token}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
        return self._access_token

    async def validate_credentials(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                await self._get_access_token(client)
                return True
        except Exception as e:
            logger.error(f"Hotmart ranking credentials validation failed: {str(e)[:100]}")
            return False

    async def get_ranking_signals(self, external_id: str) -> list[RankingSignal]:
        product_id = extract_product_id(external_id)
        scope_note = (
            f"producto {product_id}" if product_id
            else "métricas a nivel cuenta: no se pudo resolver un product_id desde el link"
        )

        end = datetime.now(timezone.utc)
        start = end - timedelta(days=self.WINDOW_DAYS)
        start_ms, end_ms = int(start.timestamp() * 1000), int(end.timestamp() * 1000)

        try:
            async with httpx.AsyncClient() as client:
                token = await self._get_access_token(client)
                counts = await self._count_all_statuses(client, token, product_id, start_ms, end_ms)
        except Exception as e:
            logger.warning(f"Hotmart ranking: sales fetch failed: {str(e)[:100]}")
            return self._unavailable(f"Sales API no disponible: {str(e)[:100]}")

        if counts is None:
            return self._unavailable("no se pudo contar alguna categoría de transacciones; no se publican tasas parciales")

        paid_retained = sum(counts[s] for s in PAID_RETAINED)
        refunded = sum(counts[s] for s in REFUNDED)
        chargeback = sum(counts[s] for s in CHARGEBACK)
        not_completed = sum(counts[s] for s in NOT_COMPLETED)
        paid_total = paid_retained + refunded + chargeback
        attempted = paid_total + not_completed

        window_note = f"{scope_note}, últimos {self.WINDOW_DAYS} días. {PROXY_NOTE}"
        signals = [RankingSignal(
            "sales_velocity", round(paid_total / self.WINDOW_DAYS, 3), measured=True, unit="ventas/día",
            detail=f"ventas pagas por día ({paid_total} en la ventana). {window_note}",
        )]

        def rate(key: str, numerator: int, denominator: int, extra: str) -> RankingSignal:
            if denominator == 0:
                return RankingSignal(
                    key, None, measured=False, unit="%",
                    detail=f"sin transacciones en la ventana: la tasa es indefinida, no 0%. {window_note}",
                )
            return RankingSignal(
                key, round(numerator / denominator * 100, 2), measured=True, unit="%",
                detail=f"{extra}. {window_note}",
            )

        signals.append(rate("approval_rate_pct", paid_total, attempted,
                            "ventas pagas sobre intentos de compra (pagas + canceladas/expiradas/bloqueadas)"))
        signals.append(rate("refund_rate_pct", refunded, paid_total,
                            "reembolsos sobre ventas pagas. Sin umbral oficial de Hotmart"))
        signals.append(rate("chargeback_rate_pct", chargeback, paid_total,
                            "contracargos/disputas sobre ventas pagas. Sin umbral oficial de Hotmart"))
        return signals

    def _unavailable(self, reason: str) -> list[RankingSignal]:
        return [
            RankingSignal(key, None, measured=False, unit=unit, detail=f"{reason}. {PROXY_NOTE}")
            for key, unit in (
                ("sales_velocity", "ventas/día"), ("approval_rate_pct", "%"),
                ("refund_rate_pct", "%"), ("chargeback_rate_pct", "%"),
            )
        ]

    async def _count_all_statuses(
        self, client: httpx.AsyncClient, token: str, product_id: str | None, start_ms: int, end_ms: int
    ) -> dict[str, int] | None:
        results = await asyncio.gather(
            *[self._count_status(client, token, s, product_id, start_ms, end_ms) for s in ALL_STATUSES],
            return_exceptions=True,
        )
        counts: dict[str, int] = {}
        for status, result in zip(ALL_STATUSES, results):
            if isinstance(result, BaseException) or result is None:
                logger.warning(f"Hotmart ranking: could not count status {status}: {result}")
                return None
            counts[status] = result
        return counts

    async def _count_status(
        self, client: httpx.AsyncClient, token: str, status: str, product_id: str | None,
        start_ms: int, end_ms: int,
    ) -> int | None:
        params: dict[str, Any] = {
            "transaction_status": status, "start_date": start_ms, "end_date": end_ms, "max_results": 1,
        }
        if product_id:
            params["product_id"] = product_id
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(f"{self.SALES_API}/sales/history", headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            return None
        body = resp.json()
        total = (body.get("page_info") or {}).get("total_results")
        if isinstance(total, int):
            return total

        # Fallback when total_results is absent: bounded manual paging.
        count = len(body.get("items") or [])
        token_next = (body.get("page_info") or {}).get("next_page_token")
        params["max_results"] = 500
        pages = 0
        while token_next and pages < self.FALLBACK_MAX_PAGES:
            params["page_token"] = token_next
            page = await client.get(f"{self.SALES_API}/sales/history", headers=headers, params=params, timeout=30)
            if page.status_code != 200:
                return None
            page_body = page.json()
            count += len(page_body.get("items") or [])
            token_next = (page_body.get("page_info") or {}).get("next_page_token")
            pages += 1
        return None if token_next else count  # still more pages after the cap -> can't claim a real count

    # ── Scoring ──

    def score_signals(self, signal_map: dict[str, RankingSignal]) -> dict[str, float | None]:
        return {
            "reputation_score": self._reputation_score(signal_map),
            "conversion_score": self._conversion_score(signal_map),
            "price_competitiveness_score": None,
            "listing_quality_score": None,  # no content API for third-party sellers — never invented
            "logistics_score": None,
            "engagement_score": None,
        }

    @staticmethod
    def _usable(signal: RankingSignal | None) -> bool:
        return bool(signal and signal.measured and signal.value is not None)

    def _reputation_score(self, s: dict[str, RankingSignal]) -> float | None:
        parts = []
        refund, chargeback = s.get("refund_rate_pct"), s.get("chargeback_rate_pct")
        if self._usable(refund):
            parts.append(max(0.0, 100.0 - (refund.value / REFUND_WARN_PCT) * 100.0))
        if self._usable(chargeback):
            parts.append(max(0.0, 100.0 - (chargeback.value / CHARGEBACK_CRITICAL_PCT) * 100.0))
        return round(sum(parts) / len(parts), 1) if parts else None

    def _conversion_score(self, s: dict[str, RankingSignal]) -> float | None:
        approval = s.get("approval_rate_pct")
        return round(approval.value, 1) if self._usable(approval) else None

    def recommendation_rules(self, signal_map: dict[str, RankingSignal]) -> list[dict]:
        s = signal_map
        rules: list[dict] = []

        chargeback = s.get("chargeback_rate_pct")
        if self._usable(chargeback) and chargeback.value > CHARGEBACK_CRITICAL_PCT:
            rules.append({
                "signal_key": "chargeback_rate_pct", "severity": "critical",
                "message": (
                    f"Tu tasa de contracargos/disputas en Hotmart es {chargeback.value:.1f}% — es la señal más grave "
                    "para tu reputación como productor. Revisá la promesa de tu página de ventas y el proceso de entrega. "
                    "(umbral heurístico, no oficial de Hotmart)"
                ),
                "current_value": f"{chargeback.value:.1f}%", "target_value": f"<{CHARGEBACK_CRITICAL_PCT:.0f}%",
            })

        refund = s.get("refund_rate_pct")
        if self._usable(refund) and refund.value > REFUND_WARN_PCT:
            rules.append({
                "signal_key": "refund_rate_pct", "severity": "warning",
                "message": (
                    f"Tu tasa de reembolsos en Hotmart es {refund.value:.1f}% — el refund rate es uno de los insumos "
                    "de la Temperature del producto. Revisá la calidad del producto o la página de ventas. "
                    "(umbral heurístico, no oficial de Hotmart)"
                ),
                "current_value": f"{refund.value:.1f}%", "target_value": f"<{REFUND_WARN_PCT:.0f}%",
            })

        approval = s.get("approval_rate_pct")
        if self._usable(approval) and approval.value < APPROVAL_INFO_PCT:
            rules.append({
                "signal_key": "approval_rate_pct", "severity": "info",
                "message": (
                    f"Solo {approval.value:.0f}% de los intentos de compra terminan pagos — muchos se cancelan, expiran o "
                    "se bloquean. Revisá medios de pago ofrecidos y fricción del checkout. (umbral heurístico)"
                ),
                "current_value": f"{approval.value:.0f}%", "target_value": f">{APPROVAL_INFO_PCT:.0f}%",
            })

        return rules
