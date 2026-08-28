"""
Fase F: AI Competitor FOMO Monitor

Extracts pricing/discount signals from competitor page content the user
configured to monitor, detects meaningful changes, generates "better than
the competition" messaging, and produces the competitor_signal payload that
feeds directly into Fase E's OpportunityDetector.detect_competitor_opportunity.

Scope note: this module PARSES text content and (via a thin async wrapper)
fetches a URL the user explicitly configured to monitor — it does not decide
what to target, discover competitor sites, or scrape at any scale/frequency
that would be abusive. One page, on request, same category as the existing
Ollama-availability HTTP check already in this codebase.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


class CompetitorPriceExtractor:
    """Extract price/discount signals from raw page text via pattern matching"""

    PRICE_PATTERN = re.compile(r"\$\s?(\d{1,6}(?:[.,]\d{2})?)")
    PERCENT_OFF_PATTERN = re.compile(
        r"(\d{1,3})\s?%\s?(?:off|OFF|descuento|de descuento|dto\.?)", re.IGNORECASE
    )
    WAS_NOW_PATTERN = re.compile(
        r"(?:was|antes|precio normal)[:\s]*\$\s?(\d{1,6}(?:[.,]\d{2})?)"
        r".{0,40}?(?:now|ahora|precio oferta)[:\s]*\$\s?(\d{1,6}(?:[.,]\d{2})?)",
        re.IGNORECASE | re.DOTALL,
    )

    @staticmethod
    def _to_float(raw: str) -> float:
        return float(raw.replace(",", ""))

    @staticmethod
    def extract(raw_text: str) -> Dict[str, Any]:
        """Parse a page's raw text/HTML for pricing and discount signals"""
        if not raw_text:
            return {
                "prices_found": [],
                "discount_percents_found": [],
                "detected_price": None,
                "detected_discount_percent": None,
                "was_now_pairs": [],
            }

        prices = [
            CompetitorPriceExtractor._to_float(m)
            for m in CompetitorPriceExtractor.PRICE_PATTERN.findall(raw_text)
        ]
        discounts = [
            int(m) for m in CompetitorPriceExtractor.PERCENT_OFF_PATTERN.findall(raw_text)
        ]
        was_now_matches = CompetitorPriceExtractor.WAS_NOW_PATTERN.findall(raw_text)
        was_now_pairs = [
            {
                "was": CompetitorPriceExtractor._to_float(w),
                "now": CompetitorPriceExtractor._to_float(n),
            }
            for w, n in was_now_matches
        ]

        # Prefer an explicit was/now pair for both detected price and implied
        # discount — it's an unambiguous signal, unlike a bag of loose prices
        detected_price = None
        detected_discount = None

        if was_now_pairs:
            pair = was_now_pairs[0]
            detected_price = pair["now"]
            if pair["was"] > 0:
                detected_discount = round((1 - pair["now"] / pair["was"]) * 100, 1)
        elif prices:
            detected_price = min(prices)  # the sale price is typically the lowest listed

        if detected_discount is None and discounts:
            detected_discount = max(discounts)

        return {
            "prices_found": prices,
            "discount_percents_found": discounts,
            "detected_price": detected_price,
            "detected_discount_percent": detected_discount,
            "was_now_pairs": was_now_pairs,
        }


class PriceChangeDetector:
    """Compare a new extraction against the last known snapshot"""

    SIGNIFICANT_DISCOUNT_DELTA = 10  # percentage points
    SIGNIFICANT_PRICE_DROP_RATIO = 0.10  # 10%+ price drop

    @staticmethod
    def detect_change(
        current: Dict[str, Any],
        previous: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if previous is None:
            return {
                "change_type": "first_observation",
                "significant": bool(current.get("detected_discount_percent")),
                "current": current,
            }

        prev_discount = previous.get("detected_discount_percent") or 0
        curr_discount = current.get("detected_discount_percent") or 0
        discount_delta = curr_discount - prev_discount

        prev_price = previous.get("detected_price")
        curr_price = current.get("detected_price")
        price_drop_ratio = None
        if prev_price and curr_price and prev_price > 0:
            price_drop_ratio = (prev_price - curr_price) / prev_price

        significant = (
            discount_delta >= PriceChangeDetector.SIGNIFICANT_DISCOUNT_DELTA
            or (price_drop_ratio is not None and price_drop_ratio >= PriceChangeDetector.SIGNIFICANT_PRICE_DROP_RATIO)
        )

        if curr_discount > prev_discount:
            change_type = "discount_increased"
        elif curr_discount < prev_discount:
            change_type = "discount_decreased"
        elif price_drop_ratio and price_drop_ratio > 0:
            change_type = "price_dropped"
        else:
            change_type = "no_change"

        return {
            "change_type": change_type,
            "significant": significant,
            "discount_delta_points": discount_delta,
            "price_drop_ratio": round(price_drop_ratio, 4) if price_drop_ratio is not None else None,
            "current": current,
            "previous": previous,
        }


class CompetitiveMessagingGenerator:
    """Deterministic 'better than the competition' messaging — no LLM
    dependency, kept fast and fully testable. Can be handed to Fase A's
    copywriter separately for a punchier rewrite when desired."""

    @staticmethod
    def generate_comparison(
        our_price: float,
        competitor_price: float,
        our_product_name: str,
        competitor_name: str = "la competencia",
    ) -> Dict[str, Any]:
        if our_price <= 0:
            return {"error": "invalid_our_price"}

        savings = competitor_price - our_price
        savings_percent = (savings / competitor_price * 100) if competitor_price > 0 else 0

        if savings > 0:
            headline = f"{our_product_name}: ${our_price:.2f} vs {competitor_name}: ${competitor_price:.2f} — Ahorra ${savings:.2f}"
            cta = "Comparar y ahorrar"
            favorable = True
        elif savings < 0:
            headline = f"{our_product_name} — calidad superior, precio justo"
            cta = "Ver por qué vale la pena"
            favorable = False
        else:
            headline = f"{our_product_name} — mismo precio, mejor experiencia"
            cta = "Descubrí la diferencia"
            favorable = False

        return {
            "headline": headline,
            "cta": cta,
            "our_price": our_price,
            "competitor_price": competitor_price,
            "savings": round(savings, 2),
            "savings_percent": round(savings_percent, 1),
            "price_favorable_to_us": favorable,
        }

    @staticmethod
    def generate_counter_offer_message(
        competitor_discount_percent: float,
        our_recommended_discount_percent: float,
        competitor_name: str = "la competencia",
    ) -> Dict[str, str]:
        return {
            "headline": f"{competitor_name} bajó precios — nosotros también",
            "body": (
                f"Notamos que {competitor_name} está ofreciendo {competitor_discount_percent:.0f}% OFF. "
                f"Por tiempo limitado, nosotros ofrecemos {our_recommended_discount_percent:.0f}% OFF."
            ),
            "cta": "Aprovechar oferta",
        }


class CompetitorAlertManager:
    """Decide whether to fire an alert and build the Fase E-compatible signal"""

    @staticmethod
    def build_alert(
        competitor_name: str,
        change_result: Dict[str, Any],
        detected_at: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        if not change_result["significant"]:
            return None

        detected_at = detected_at or datetime.now(timezone.utc)
        current = change_result["current"]

        return {
            "competitor_name": competitor_name,
            "discount_percent": current.get("detected_discount_percent") or 0,
            "detected_price": current.get("detected_price"),
            "change_type": change_result["change_type"],
            "detected_at": detected_at.isoformat(),
        }


class AICompetitorMonitorAgent:
    """Fase F: Main agent — extract, detect change, generate messaging, alert"""

    @staticmethod
    def extract_competitor_offer(raw_text: str) -> Dict[str, Any]:
        return CompetitorPriceExtractor.extract(raw_text)

    @staticmethod
    def detect_price_change(
        current: Dict[str, Any],
        previous: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return PriceChangeDetector.detect_change(current, previous)

    @staticmethod
    def generate_competitive_message(
        our_price: float,
        competitor_price: float,
        our_product_name: str,
        competitor_name: str = "la competencia",
    ) -> Dict[str, Any]:
        return CompetitiveMessagingGenerator.generate_comparison(
            our_price, competitor_price, our_product_name, competitor_name
        )

    @staticmethod
    def build_alert(
        competitor_name: str,
        change_result: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        return CompetitorAlertManager.build_alert(competitor_name, change_result)

    @staticmethod
    def full_monitor_cycle(
        raw_text: str,
        competitor_name: str,
        previous_snapshot: Optional[Dict[str, Any]] = None,
        our_price: Optional[float] = None,
        our_product_name: Optional[str] = None,
        our_recommended_discount_percent: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Full pipeline: extract -> detect change -> alert (if significant)
        -> competitive messaging (if our pricing context is supplied)"""
        current = CompetitorPriceExtractor.extract(raw_text)
        change = PriceChangeDetector.detect_change(current, previous_snapshot)
        alert = CompetitorAlertManager.build_alert(competitor_name, change)

        comparison = None
        counter_offer = None

        if our_price is not None and current.get("detected_price") is not None and our_product_name:
            comparison = CompetitiveMessagingGenerator.generate_comparison(
                our_price, current["detected_price"], our_product_name, competitor_name
            )

        if alert is not None and current.get("detected_discount_percent"):
            counter_discount = our_recommended_discount_percent or min(
                current["detected_discount_percent"] + 5, 50
            )
            counter_offer = CompetitiveMessagingGenerator.generate_counter_offer_message(
                current["detected_discount_percent"], counter_discount, competitor_name
            )

        return {
            "current_snapshot": current,
            "change": change,
            "alert": alert,
            "price_comparison": comparison,
            "counter_offer_message": counter_offer,
        }


async def fetch_competitor_page(url: str, timeout_seconds: int = 10) -> Optional[str]:
    """Thin async fetcher for a single user-configured URL — mirrors the
    existing Ollama-availability check pattern in llm_provider.py. Returns
    raw page text, or None on any failure (never raises into the caller)."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Competitor page fetch returned {resp.status} for {url}")
                    return None
                return await resp.text()
    except Exception as e:
        logger.warning(f"Competitor page fetch failed for {url}: {e}")
        return None
