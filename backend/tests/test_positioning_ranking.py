"""Tests for the platform-algorithm-aware positioning connectors.

Pure-logic tests (score_signals / recommendation_rules), graceful-degradation
tests (HTTP failures must yield measured=False, never raise), and a
regression guard proving the ML/Instagram scoring moved from the service into
the connectors without changing a single number.

No network: httpx.AsyncClient is replaced by a scripted fake.
"""

import json
import time

import httpx
import pytest

from app.domains.seo_config.platform_ranking_amazon import AmazonRankingConnector, extract_asin
from app.domains.seo_config.platform_ranking_base import PlatformRankingConnector, RankingSignal
from app.domains.seo_config.platform_ranking_hotmart import (
    ALL_STATUSES,
    HotmartRankingConnector,
    extract_product_id,
)
from app.domains.seo_config.platform_ranking_instagram import InstagramRankingConnector
from app.domains.seo_config.platform_ranking_mercadolibre import MercadoLibreRankingConnector
from app.domains.seo_config.platform_store_ranking_amazon import AmazonStoreRankingConnector
from app.domains.seo_config.positioning_scoring_utils import composite_from_sub_scores, measured_pct


def sig(key, value, measured=True):
    return RankingSignal(key, value, measured=measured)


def smap(*signals):
    return {s.key: s for s in signals}


# ── Scripted fake for httpx.AsyncClient ──

class FakeResponse:
    def __init__(self, status_code=200, body=None, content=None):
        self.status_code = status_code
        self._body = body
        self.content = content if content is not None else json.dumps(body).encode() if body is not None else b""

    def json(self):
        if self._body is None:
            raise ValueError("no json body")
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)


def install_fake_http(monkeypatch, routes, default_status=403):
    """routes: list of (method, url_substring, FakeResponse); first match wins."""

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def _dispatch(self, method, url, **kwargs):
            for m, needle, response in routes:
                if m == method and needle in url:
                    return response
            return FakeResponse(default_status, {"error": "unscripted"})

        async def get(self, url, **kwargs):
            return await self._dispatch("GET", url, **kwargs)

        async def post(self, url, **kwargs):
            return await self._dispatch("POST", url, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)


# ── Shared utils ──

def test_composite_excludes_none_pillars():
    assert composite_from_sub_scores({"a": 80.0, "b": None, "c": 60.0}) == 70.0
    assert composite_from_sub_scores({"a": None}) == 0.0


def test_measured_pct():
    assert measured_pct([sig("a", 1), sig("b", None, measured=False)]) == 50.0
    assert measured_pct([]) == 0.0


def test_every_connector_implements_the_full_contract():
    for cls in (
        MercadoLibreRankingConnector, InstagramRankingConnector,
        AmazonRankingConnector, HotmartRankingConnector,
    ):
        assert isinstance(cls({}), PlatformRankingConnector)


# ── Regression: ML / Instagram scoring moved, not changed ──

def test_ml_scoring_unchanged_healthy():
    ml = MercadoLibreRankingConnector({})
    s = smap(
        sig("seller_claims_rate", 0.5), sig("seller_cancellation_rate", 1.0),
        sig("seller_has_unhealthy_items", False),
        sig("listing_completeness_pct", 100.0), sig("title_length_score", 100.0),
        sig("photo_count", 8), sig("question_response_latency_minutes", 20.0),
        sig("question_answer_rate_pct", 95.0), sig("shipping_tier", "full"),
    )
    out = ml.score_signals(s)
    assert out["reputation_score"] == 91.1
    assert out["listing_quality_score"] == 92.3
    assert out["logistics_score"] == 100.0
    assert out["price_competitiveness_score"] is None
    assert ml.recommendation_rules(s) == []


def test_ml_scoring_unchanged_bad_account_triggers_all_rules():
    ml = MercadoLibreRankingConnector({})
    s = smap(
        sig("seller_claims_rate", 4.2), sig("seller_cancellation_rate", 12.0),
        sig("seller_has_unhealthy_items", True),
        sig("listing_completeness_pct", 60.0), sig("title_length_score", 40.0),
        sig("photo_count", 2), sig("question_response_latency_minutes", 180.0),
        sig("question_answer_rate_pct", 50.0), sig("shipping_tier", "standard"),
    )
    out = ml.score_signals(s)
    assert (out["reputation_score"], out["listing_quality_score"], out["logistics_score"]) == (6.7, 36.7, 40.0)
    assert [r["signal_key"] for r in ml.recommendation_rules(s)] == [
        "seller_claims_rate", "question_response_latency_minutes", "listing_completeness_pct",
        "seller_has_unhealthy_items", "photo_count",
    ]


def test_ml_scoring_sparse_signals_yield_none_not_zero():
    ml = MercadoLibreRankingConnector({})
    out = ml.score_signals(smap(sig("seller_claims_rate", None, measured=False)))
    assert all(v is None for v in out.values())


def test_instagram_scoring_unchanged():
    ig = InstagramRankingConnector({})
    weak = smap(
        sig("sends_per_reach", 0.001), sig("likes_per_reach", 0.2), sig("saves_per_reach", 0.0),
        sig("comments_per_reach", 0.0), sig("alt_text_present", False),
    )
    out = ig.score_signals(weak)
    assert out["listing_quality_score"] == 50.0
    assert [r["signal_key"] for r in ig.recommendation_rules(weak)] == ["sends_per_reach", "alt_text_present"]


# ── Amazon (per listing) ──

def test_extract_asin():
    assert extract_asin("B08N5WRWNW") == "B08N5WRWNW"
    assert extract_asin("https://www.amazon.com/Some-Product/dp/B08N5WRWNW/ref=sr_1_1") == "B08N5WRWNW"
    assert extract_asin("https://www.amazon.com/gp/product/B08N5WRWNW") == "B08N5WRWNW"
    assert extract_asin("https://example.com/not-amazon") is None
    assert extract_asin("") is None


def test_amazon_scoring_and_rules():
    az = AmazonRankingConnector({})
    s = smap(
        sig("account_odr_pct", 2.0), sig("account_lsr_pct", 1.0), sig("account_vtr_pct", 90.0),
        sig("price_vs_foep_ratio", 1.1), sig("foep_price", 20.0),
        sig("listing_buyable", True), sig("catalog_completeness_pct", 80.0),
        sig("in_stock", True), sig("fulfillment_method", "fbm"),
        sig("listing_issues_count", 2),
    )
    out = az.score_signals(s)
    assert out["reputation_score"] == 50.0  # mean(ODR 2x the 1% cap -> 0, LSR 1/4 -> 75, VTR 5pts under 95 -> 75)
    assert out["price_competitiveness_score"] == 50.0  # 10% over FOEP costs 50 points
    assert out["listing_quality_score"] == 90.0
    assert out["logistics_score"] == 80.0
    keys = {r["signal_key"] for r in az.recommendation_rules(s)}
    assert {"account_odr_pct", "account_vtr_pct", "price_vs_foep_ratio", "listing_issues_count"} <= keys
    odr_rule = next(r for r in az.recommendation_rules(s) if r["signal_key"] == "account_odr_pct")
    assert odr_rule["severity"] == "critical" and "2.00%" in odr_rule["message"]


def test_amazon_price_at_or_below_foep_is_full_score():
    az = AmazonRankingConnector({})
    assert az.score_signals(smap(sig("price_vs_foep_ratio", 0.95)))["price_competitiveness_score"] == 100.0


def test_amazon_unmeasured_signals_never_score_or_recommend():
    az = AmazonRankingConnector({})
    s = smap(
        sig("account_odr_pct", None, measured=False), sig("price_vs_foep_ratio", None, measured=False),
        sig("listing_buyable", None, measured=False),
    )
    assert all(v is None for v in az.score_signals(s).values())
    assert az.recommendation_rules(s) == []


async def test_amazon_degrades_gracefully_when_every_call_fails(monkeypatch):
    install_fake_http(monkeypatch, routes=[], default_status=403)
    az = AmazonRankingConnector({"access_token": "t", "seller_id": "S1"})
    signals = await az.get_ranking_signals("B08N5WRWNW")
    assert signals, "must still return signals"
    assert all(s.measured is False for s in signals)


async def test_amazon_unresolvable_asin_returns_honest_signal():
    signals = await AmazonRankingConnector({"access_token": "t"}).get_ranking_signals("https://example.com/x")
    assert len(signals) == 1 and signals[0].key == "asin_unresolved" and signals[0].measured is False


async def test_amazon_happy_path_parses_real_shapes(monkeypatch):
    performance_doc = {"performanceMetrics": [{
        "orderDefectRate": {"afn": {"rate": 0.02}},
        "lateShipmentRate": {"rate": 0.01},
        "validTrackingRate": {"rate": 0.97},
    }]}
    install_fake_http(monkeypatch, routes=[
        ("POST", "/reports/2021-06-30/reports", FakeResponse(202, {"reportId": "R1"})),
        ("GET", "/reports/2021-06-30/reports/R1", FakeResponse(200, {"processingStatus": "DONE", "reportDocumentId": "D1"})),
        ("GET", "/reports/2021-06-30/documents/D1", FakeResponse(200, {"url": "https://s3.example/doc"})),
        ("GET", "https://s3.example/doc", FakeResponse(200, content=json.dumps(performance_doc).encode())),
        ("GET", "/listings/2021-08-01/items/", FakeResponse(200, {"items": [{
            "sku": "SKU1",
            "summaries": [{"status": ["BUYABLE", "DISCOVERABLE"]}],
            "offers": [{"price": {"amount": "22.00"}}],
            "fulfillmentAvailability": [{"fulfillmentChannelCode": "AMAZON_NA", "quantity": 12}],
            "issues": [],
        }]})),
        ("POST", "featuredOfferExpectedPrice", FakeResponse(200, {"responses": [{"body": {
            "featuredOfferExpectedPriceResults": [{"featuredOfferExpectedPrice": {"listingPrice": {"amount": 20.0}}}],
        }}]})),
        ("GET", "/catalog/2022-04-01/items/", FakeResponse(200, {
            "summaries": [{"itemName": "A great product"}],
            "attributes": {"bullet_point": ["a", "b", "c", "d", "e"]},
            "images": [{"images": [{"variant": f"V{i}"} for i in range(7)]}],
            "salesRanks": [{"displayGroupRanks": [{"rank": 1234}]}],
        })),
    ])
    az = AmazonRankingConnector({"access_token": "t", "seller_id": "S1"})
    m = {s.key: s for s in await az.get_ranking_signals("B08N5WRWNW")}

    assert (m["account_odr_pct"].value, m["account_lsr_pct"].value, m["account_vtr_pct"].value) == (2.0, 1.0, 97.0)
    assert m["listing_buyable"].value is True and m["in_stock"].value is True
    assert m["fulfillment_method"].value == "fba"
    assert m["price_vs_foep_ratio"].value == 1.1 and m["foep_price"].value == 20.0
    assert m["catalog_completeness_pct"].value == 100.0
    assert m["best_sellers_rank"].value == 1234
    assert "reviews" not in " ".join(m), "reviews must never be fabricated"


# ── Hotmart (proxy) ──

def test_extract_product_id():
    assert extract_product_id("1234567") == "1234567"
    assert extract_product_id("https://x.example/p?product_id=987") == "987"
    assert extract_product_id("https://pay.hotmart.com/A12345678B") is None  # never guessed
    assert extract_product_id("") is None


def _hotmart(monkeypatch, counts):
    hm = HotmartRankingConnector({"basic_token": "b"})
    hm._access_token, hm._token_expires_at = "t", time.time() + 1000

    async def fake_counts(*args, **kwargs):
        return counts

    monkeypatch.setattr(hm, "_count_all_statuses", fake_counts)
    return hm


def _counts(**overrides):
    base = {s: 0 for s in ALL_STATUSES}
    base.update(overrides)
    return base


async def test_hotmart_rates_from_real_counts(monkeypatch):
    hm = _hotmart(monkeypatch, _counts(APPROVED=70, COMPLETE=10, REFUNDED=8, PARTIALLY_REFUNDED=2, CHARGEBACK=1, CANCELLED=9))
    m = {s.key: s for s in await hm.get_ranking_signals("123")}
    assert m["refund_rate_pct"].value == round(10 / 91 * 100, 2)  # 10 refunded of 91 paid sales
    assert m["chargeback_rate_pct"].value == round(1 / 91 * 100, 2)
    assert m["approval_rate_pct"].value == round(91 / 100 * 100, 2)
    assert m["sales_velocity"].value == round(91 / 30, 3)
    assert all(s.measured for s in m.values())
    assert all("NO es la Temperature/Blueprint real" in s.detail for s in m.values()), "every signal must say it's a proxy"


async def test_hotmart_zero_sales_rates_are_undefined_not_zero(monkeypatch):
    hm = _hotmart(monkeypatch, _counts())
    m = {s.key: s for s in await hm.get_ranking_signals("123")}
    assert m["sales_velocity"].value == 0.0 and m["sales_velocity"].measured is True
    for key in ("approval_rate_pct", "refund_rate_pct", "chargeback_rate_pct"):
        assert m[key].value is None and m[key].measured is False


async def test_hotmart_partial_count_failure_publishes_no_rates(monkeypatch):
    hm = _hotmart(monkeypatch, None)
    signals = await hm.get_ranking_signals("123")
    assert signals and all(s.measured is False for s in signals)


async def test_hotmart_count_status_uses_total_results_and_fails_safe(monkeypatch):
    hm = HotmartRankingConnector({"basic_token": "b"})
    install_fake_http(monkeypatch, [("GET", "/sales/history", FakeResponse(200, {"page_info": {"total_results": 42}, "items": [{}]}))])
    async with httpx.AsyncClient() as c:
        assert await hm._count_status(c, "t", "REFUNDED", None, 0, 1) == 42
    install_fake_http(monkeypatch, [("GET", "/sales/history", FakeResponse(500, {}))])
    async with httpx.AsyncClient() as c:
        assert await hm._count_status(c, "t", "REFUNDED", None, 0, 1) is None


def test_hotmart_scoring_and_rules_have_no_listing_pillars():
    hm = HotmartRankingConnector({})
    s = smap(sig("refund_rate_pct", 20.0), sig("chargeback_rate_pct", 2.0), sig("approval_rate_pct", 40.0))
    out = hm.score_signals(s)
    assert out["reputation_score"] == 0.0
    assert out["conversion_score"] == 40.0
    assert out["listing_quality_score"] is None and out["logistics_score"] is None
    rules = {r["signal_key"]: r for r in hm.recommendation_rules(s)}
    assert rules["chargeback_rate_pct"]["severity"] == "critical"
    assert "heurístico" in rules["refund_rate_pct"]["message"]  # never presented as an official Hotmart threshold
    assert "approval_rate_pct" in rules


# ── Amazon Brand Store (store level) ──

def test_store_scoring_and_rules():
    st = AmazonStoreRankingConnector({})
    s = smap(
        sig("dwell_time_seconds", 45.0), sig("bounce_rate_pct", 70.0),
        sig("new_to_store_pct", 40.0), sig("section_ctr_pct", 1.0), sig("visitors", 5000.0),
    )
    out = st.score_signals(s)
    assert out["engagement_score"] == 52.5
    assert out["new_visitor_score"] == 40.0
    assert out["content_performance_score"] == 20.0
    assert out["traffic_score"] is None, "raw visitors have no absolute scale; never scored"
    assert [r["signal_key"] for r in st.recommendation_rules(s)] == ["bounce_rate_pct"]


async def test_store_requires_brand_entity_id():
    signals = await AmazonStoreRankingConnector({"access_token": "t", "client_id": "c"}).get_store_signals()
    assert signals and all(s.measured is False for s in signals)


async def test_store_degrades_on_api_error(monkeypatch):
    install_fake_http(monkeypatch, [("GET", "/insights", FakeResponse(403, {}))])
    st = AmazonStoreRankingConnector({"access_token": "t", "client_id": "c", "brand_entity_id": "B1"})
    assert all(s.measured is False for s in await st.get_store_signals())


async def test_store_parses_insights(monkeypatch):
    install_fake_http(monkeypatch, [("GET", "/insights", FakeResponse(200, {
        "visitors": 1000, "dwellTime": 45, "bounceRate": 0.7, "newToStoreRate": 0.4,
        "sections": [{"clicks": 10, "viewableImpressions": 1000}, {"clicks": 5, "viewableImpressions": 500}],
    }))])
    st = AmazonStoreRankingConnector({"access_token": "t", "client_id": "c", "brand_entity_id": "B1"})
    m = {s.key: s for s in await st.get_store_signals()}
    assert m["bounce_rate_pct"].value == 70.0 and m["new_to_store_pct"].value == 40.0
    assert m["dwell_time_seconds"].value == 45.0 and m["section_ctr_pct"].value == 1.0


# ── Schema: the new/changed tables must compile for Postgres ──

def test_positioning_tables_compile_for_postgres():
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateTable

    import app.domains.seo_config.router  # noqa: F401  (loads every model into metadata)
    from app.domains.seo_config.positioning_models import POSITIONING_TABLES

    ddl = {t.name: str(CreateTable(t).compile(dialect=postgresql.dialect())) for t in POSITIONING_TABLES}
    assert "store_positioning_scores" in ddl
    recs = ddl["positioning_recommendations"]
    assert "store_score_id" in recs
    assert "link_id UUID NOT NULL" not in recs, "link_id must be nullable for store-scoped recommendations"
