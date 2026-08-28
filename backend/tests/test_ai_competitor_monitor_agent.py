"""Fase F: AI Competitor FOMO Monitor Tests"""

from datetime import datetime, timezone
import pytest

from app.domains.fomo.ai_competitor_monitor_agent import (
    AICompetitorMonitorAgent,
    CompetitorPriceExtractor,
    PriceChangeDetector,
    CompetitiveMessagingGenerator,
    CompetitorAlertManager,
)

NOW = datetime(2026, 8, 28, tzinfo=timezone.utc)


class TestCompetitorPriceExtractor:
    def test_empty_text(self):
        result = CompetitorPriceExtractor.extract("")
        assert result["prices_found"] == []
        assert result["detected_price"] is None

    def test_extract_simple_price(self):
        result = CompetitorPriceExtractor.extract("Nuestro producto cuesta $49.99 hoy")
        assert 49.99 in result["prices_found"]
        assert result["detected_price"] == 49.99

    def test_extract_percent_off(self):
        result = CompetitorPriceExtractor.extract("¡30% off en toda la tienda!")
        assert 30 in result["discount_percents_found"]
        assert result["detected_discount_percent"] == 30

    def test_extract_percent_off_spanish(self):
        result = CompetitorPriceExtractor.extract("25% descuento en productos seleccionados")
        assert 25 in result["discount_percents_found"]

    def test_extract_was_now_pair(self):
        result = CompetitorPriceExtractor.extract("Was $100.00 now $70.00 — limited time!")
        assert len(result["was_now_pairs"]) == 1
        assert result["was_now_pairs"][0]["was"] == 100.00
        assert result["was_now_pairs"][0]["now"] == 70.00
        assert result["detected_price"] == 70.00
        assert result["detected_discount_percent"] == 30.0

    def test_extract_multiple_prices_takes_lowest_as_sale_price(self):
        result = CompetitorPriceExtractor.extract("Precio normal $199.99, oferta $149.99")
        assert result["detected_price"] == 149.99

    def test_no_signals_in_plain_text(self):
        result = CompetitorPriceExtractor.extract("Bienvenido a nuestra tienda online")
        assert result["detected_price"] is None
        assert result["detected_discount_percent"] is None


class TestPriceChangeDetector:
    def test_first_observation_no_previous(self):
        current = {"detected_discount_percent": 20, "detected_price": 80}
        result = PriceChangeDetector.detect_change(current, None)
        assert result["change_type"] == "first_observation"
        assert result["significant"] is True  # has a discount

    def test_first_observation_no_discount_not_significant(self):
        current = {"detected_discount_percent": None, "detected_price": 100}
        result = PriceChangeDetector.detect_change(current, None)
        assert result["significant"] is False

    def test_discount_increased_significant(self):
        previous = {"detected_discount_percent": 10, "detected_price": 90}
        current = {"detected_discount_percent": 25, "detected_price": 75}
        result = PriceChangeDetector.detect_change(current, previous)
        assert result["change_type"] == "discount_increased"
        assert result["significant"] is True
        assert result["discount_delta_points"] == 15

    def test_discount_increase_below_threshold_not_significant(self):
        previous = {"detected_discount_percent": 10, "detected_price": 90}
        current = {"detected_discount_percent": 15, "detected_price": 85}
        result = PriceChangeDetector.detect_change(current, previous)
        assert result["significant"] is False

    def test_discount_decreased(self):
        previous = {"detected_discount_percent": 30, "detected_price": 70}
        current = {"detected_discount_percent": 10, "detected_price": 90}
        result = PriceChangeDetector.detect_change(current, previous)
        assert result["change_type"] == "discount_decreased"

    def test_price_dropped_significant(self):
        previous = {"detected_discount_percent": 0, "detected_price": 100}
        current = {"detected_discount_percent": 0, "detected_price": 85}
        result = PriceChangeDetector.detect_change(current, previous)
        assert result["change_type"] == "price_dropped"
        assert result["significant"] is True

    def test_no_change(self):
        previous = {"detected_discount_percent": 20, "detected_price": 80}
        current = {"detected_discount_percent": 20, "detected_price": 80}
        result = PriceChangeDetector.detect_change(current, previous)
        assert result["change_type"] == "no_change"
        assert result["significant"] is False


class TestCompetitiveMessagingGenerator:
    def test_favorable_comparison(self):
        result = CompetitiveMessagingGenerator.generate_comparison(
            our_price=49.99, competitor_price=69.99, our_product_name="SellIA Pro", competitor_name="RivalCo"
        )
        assert result["price_favorable_to_us"] is True
        assert result["savings"] == 20.0
        assert "Ahorra" in result["headline"]

    def test_unfavorable_comparison(self):
        result = CompetitiveMessagingGenerator.generate_comparison(
            our_price=99.99, competitor_price=49.99, our_product_name="SellIA Pro"
        )
        assert result["price_favorable_to_us"] is False
        assert result["savings"] < 0

    def test_equal_price_comparison(self):
        result = CompetitiveMessagingGenerator.generate_comparison(
            our_price=50.0, competitor_price=50.0, our_product_name="SellIA Pro"
        )
        assert result["savings"] == 0
        assert result["price_favorable_to_us"] is False

    def test_invalid_our_price(self):
        result = CompetitiveMessagingGenerator.generate_comparison(0, 50, "Product")
        assert result["error"] == "invalid_our_price"

    def test_counter_offer_message(self):
        result = CompetitiveMessagingGenerator.generate_counter_offer_message(20, 25, "RivalCo")
        assert "RivalCo" in result["headline"]
        assert "20" in result["body"]
        assert "25" in result["body"]


class TestCompetitorAlertManager:
    def test_no_alert_when_not_significant(self):
        change = {"significant": False, "current": {}}
        alert = CompetitorAlertManager.build_alert("RivalCo", change)
        assert alert is None

    def test_alert_built_when_significant(self):
        change = {
            "significant": True,
            "change_type": "discount_increased",
            "current": {"detected_discount_percent": 30, "detected_price": 70},
        }
        alert = CompetitorAlertManager.build_alert("RivalCo", change, detected_at=NOW)
        assert alert["competitor_name"] == "RivalCo"
        assert alert["discount_percent"] == 30
        assert alert["detected_at"] == NOW.isoformat()


class TestAICompetitorMonitorAgent:
    def test_extract_competitor_offer(self):
        result = AICompetitorMonitorAgent.extract_competitor_offer("40% off today only!")
        assert result["detected_discount_percent"] == 40

    def test_detect_price_change(self):
        result = AICompetitorMonitorAgent.detect_price_change(
            {"detected_discount_percent": 20, "detected_price": 80}, None
        )
        assert result["change_type"] == "first_observation"

    def test_generate_competitive_message(self):
        result = AICompetitorMonitorAgent.generate_competitive_message(40, 60, "Our Product")
        assert result["price_favorable_to_us"] is True

    def test_build_alert(self):
        change = {"significant": True, "change_type": "discount_increased", "current": {"detected_discount_percent": 25}}
        alert = AICompetitorMonitorAgent.build_alert("RivalCo", change)
        assert alert is not None

    def test_full_monitor_cycle_first_observation_with_comparison(self):
        result = AICompetitorMonitorAgent.full_monitor_cycle(
            raw_text="Was $100 now $70 — hurry!",
            competitor_name="RivalCo",
            our_price=65.0,
            our_product_name="SellIA Pro",
        )
        assert result["current_snapshot"]["detected_price"] == 70.0
        assert result["change"]["change_type"] == "first_observation"
        assert result["alert"] is not None
        assert result["price_comparison"]["price_favorable_to_us"] is True
        assert result["counter_offer_message"] is not None

    def test_full_monitor_cycle_no_significant_change_no_alert(self):
        previous = {"detected_discount_percent": 20, "detected_price": 80, "prices_found": [80], "discount_percents_found": [20], "was_now_pairs": []}
        result = AICompetitorMonitorAgent.full_monitor_cycle(
            raw_text="20% off — same deal as before",
            competitor_name="RivalCo",
            previous_snapshot=previous,
        )
        assert result["alert"] is None
        assert result["counter_offer_message"] is None

    def test_full_monitor_cycle_no_pricing_context_no_comparison(self):
        result = AICompetitorMonitorAgent.full_monitor_cycle(
            raw_text="30% off today",
            competitor_name="RivalCo",
        )
        assert result["price_comparison"] is None


class TestFetchCompetitorPage:
    @pytest.mark.asyncio
    async def test_fetch_invalid_url_returns_none(self):
        from app.domains.fomo.ai_competitor_monitor_agent import fetch_competitor_page
        result = await fetch_competitor_page("http://this-domain-does-not-exist-12345.invalid", timeout_seconds=2)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
