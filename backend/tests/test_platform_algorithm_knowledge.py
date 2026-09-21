"""Platform algorithm knowledge: integrity, name normalisation, and how it shapes the
positioning API (explained recommendations, coverage, prioritised action plan)."""

import json
import os
import pathlib
import re
import uuid
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from fastapi import FastAPI
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool


@compiles(PGUUID, "sqlite")
def _uuid_sqlite(el, comp, **kw):  # noqa: ANN001
    return "CHAR(36)"


@compiles(PGJSONB, "sqlite")
def _jsonb_sqlite(el, comp, **kw):  # noqa: ANN001
    return "TEXT"


def _try_uuid(v):
    try:
        return uuid.UUID(v)
    except (ValueError, TypeError, AttributeError):
        return v


PGUUID.bind_processor = lambda self, d: (lambda v: None if v is None else str(v))
PGUUID.result_processor = lambda self, d, c: (lambda v: None if v is None else _try_uuid(v))
PGJSONB.bind_processor = lambda self, d: (lambda v: None if v is None else json.dumps(v))
PGJSONB.result_processor = lambda self, d, c: (
    lambda v: None if v in (None, "") else (v if isinstance(v, (dict, list)) else json.loads(v))
)

import app.domains.seo_config.platform_algorithm_knowledge as kb  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.core.deps import get_current_user  # noqa: E402
from app.domains.automations.models import AutomationToggle, ToggleAuditLog  # noqa: E402
from app.domains.seo_config import positioning_score_service as pss  # noqa: E402
from app.domains.seo_config.models import PlatformSEOStatus, PublicationLink, SEOConfig  # noqa: E402
from app.domains.seo_config.platform_ranking_base import RankingSignal  # noqa: E402
from app.domains.seo_config.positioning_models import (  # noqa: E402
    PositioningRecommendation, PublicationLinkPositioningScore, StorePositioningScore,
)
from app.domains.seo_config.router import router  # noqa: E402

SEO_DIR = pathlib.Path(__file__).resolve().parents[1] / "app" / "domains" / "seo_config"
LIBRARY = pathlib.Path(__file__).resolve().parents[1] / "app" / "core" / "knowledge" / "library" / "marketplace_algorithm_mastery.json"

CONNECTOR_SOURCE = {
    "mercado-libre": "platform_ranking_mercadolibre.py",
    "amazon": "platform_ranking_amazon.py",
    "hotmart": "platform_ranking_hotmart.py",
    "instagram": "platform_ranking_instagram.py",
}


# ── Names ──

@pytest.mark.parametrize("raw,expected", [
    ("mercado-libre", "mercado-libre"), ("mercadolibre", "mercado-libre"), ("Mercado_Libre", "mercado-libre"),
    ("MELI", "mercado-libre"), ("Amazon", "amazon"), ("hotmart", "hotmart"), ("IG", "instagram"),
    ("nuvemshop", "tiendanube"), ("Tienda Nube", "tiendanube"), ("facebook_marketplace", "facebook"),
    ("otro", "custom"),
])
def test_every_spelling_resolves_to_the_canonical_key(raw, expected):
    assert kb.canonical_platform(raw) == expected


def test_unknown_or_empty_names_are_not_guessed():
    assert kb.canonical_platform("plataforma-inventada") is None
    assert kb.canonical_platform("") is None and kb.canonical_platform(None) is None
    assert kb.coverage_for("plataforma-inventada") == kb.GUIDANCE_ONLY


def test_an_alias_never_belongs_to_two_platforms():
    seen: dict[str, str] = {}
    for profile in kb.PROFILES.values():
        for name in (profile.key, *profile.aliases):
            slug = re.sub(r"[^a-z0-9]", "", name.lower())
            assert seen.setdefault(slug, profile.key) == profile.key, f"{name!r} is claimed by two platforms"


def test_connector_keys_match_the_canonical_names():
    for key in pss.RANKING_CONNECTORS:
        assert kb.canonical_platform(key) == key


# ── Integrity ──

def test_every_factor_states_how_sure_we_are():
    for profile in kb.PROFILES.values():
        for factor in profile.factors:
            assert factor.evidence in (kb.OFFICIAL, kb.COMMUNITY), (profile.key, factor.name)
            assert factor.note.strip()


def test_unresearched_platforms_claim_nothing():
    unresearched = [p for p in kb.PROFILES.values() if not p.researched]
    assert unresearched, "expected some platforms flagged as not researched yet"
    for p in unresearched:
        assert p.factors == () and p.playbook == () and p.coverage == kb.GUIDANCE_ONLY


def test_measured_platforms_have_a_connector_and_admit_what_they_cannot_see():
    measured = {p.key for p in kb.PROFILES.values() if p.coverage == kb.MEASURED}
    assert measured == set(pss.RANKING_CONNECTORS), "coverage=measured must match the registered connectors"
    for key in measured:
        assert kb.PROFILES[key].not_measurable, f"{key} must say what it cannot measure"
        assert any(f.evidence == kb.OFFICIAL for f in kb.PROFILES[key].factors)


@pytest.mark.parametrize("platform,filename", CONNECTOR_SOURCE.items())
def test_signals_cited_in_the_guide_really_exist_in_the_connector(platform, filename):
    """Anti-drift: a factor may only claim a signal the connector (or the scoring service, for
    cadence) actually produces."""
    source = (SEO_DIR / filename).read_text(encoding="utf-8") + (SEO_DIR / "positioning_score_service.py").read_text(encoding="utf-8")
    for factor in kb.PROFILES[platform].factors:
        for key in factor.measured_by:
            assert f'"{key}"' in source, f"{platform}: guide cites signal {key!r} that no connector produces"


@pytest.mark.parametrize("platform,filename", CONNECTOR_SOURCE.items())
def test_every_recommendation_a_connector_can_emit_has_a_documented_reason(platform, filename):
    source = (SEO_DIR / filename).read_text(encoding="utf-8")
    emitted = set(re.findall(r'"signal_key":\s*"([a-z_]+)"', source))
    assert emitted, platform
    for key in emitted:
        assert kb.factor_for_signal(platform, key) is not None, f"{platform}: no 'why' for recommendation {key!r}"


def test_agent_knowledge_file_is_generated_from_the_module():
    on_disk = {i["id"]: i for i in json.loads(LIBRARY.read_text(encoding="utf-8"))["items"]}
    for item in kb.render_library_items():
        assert on_disk[item["id"]] == item, f"{item['id']} drifted: regenerate the library file from the module"
    for legacy in ("algo_003", "algo_004", "algo_005"):
        assert legacy in on_disk, "existing knowledge must not be deleted"
    for unverified in ("algo_003", "algo_004"):
        assert "Sin verificar" in on_disk[unverified]["tactic"]


# ── DB-backed behaviour ──

@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    tables = (
        PublicationLink.__table__, PublicationLinkPositioningScore.__table__, StorePositioningScore.__table__,
        PositioningRecommendation.__table__, SEOConfig.__table__, PlatformSEOStatus.__table__,
        AutomationToggle.__table__, ToggleAuditLog.__table__,
    )
    async with engine.begin() as conn:
        for t in tables:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


async def add_link(db, biz, platform, title="x"):
    link = PublicationLink(business_id=biz, url=f"https://example.com/{platform}/{uuid4()}", title=title,
                           platform_source=platform, seo_enabled=True)
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def add_score(db, biz, link, platform):
    score = PublicationLinkPositioningScore(business_id=biz, link_id=link.id, platform_name=platform, composite_score=60.0)
    db.add(score)
    await db.commit()
    await db.refresh(score)
    return score


async def add_rec(db, biz, link, score, key, severity, message="m"):
    rec = PositioningRecommendation(business_id=biz, link_id=link.id, score_id=score.id, signal_key=key,
                                    severity=severity, message=message, status="open")
    db.add(rec)
    await db.commit()
    return rec


async def test_platform_spellings_are_one_platform_and_unscored_links_say_why(db):
    biz = uuid4()
    ml_a = await add_link(db, biz, "mercado-libre")
    await add_link(db, biz, "mercadolibre")  # channels' spelling of the same platform
    await add_link(db, biz, "shopify")
    await add_link(db, biz, "etsy")
    await add_score(db, biz, ml_a, "mercado-libre")

    summary = await pss.PositioningScoreService(db).get_business_summary(biz)

    overview = {p["platform"]: p for p in summary["platform_overview"]}
    assert overview["mercado-libre"]["links"] == 2 and overview["mercado-libre"]["scored_links"] == 1
    assert overview["mercado-libre"]["coverage"] == kb.MEASURED
    assert overview["shopify"]["coverage"] == kb.WEB_AUDIT and overview["etsy"]["coverage"] == kb.GUIDANCE_ONLY

    reasons = {u["platform"]: u for u in summary["unscored_links"]}
    assert "sitio propio" in reasons["shopify"]["reason"]
    assert "solo se muestra la guía" in reasons["etsy"]["reason"]
    assert reasons["mercado-libre"]["coverage"] == kb.MEASURED and "Todavía no se calculó" in reasons["mercado-libre"]["reason"]


async def test_action_plan_orders_by_severity_then_documented_then_reach(db):
    biz = uuid4()
    links = [await add_link(db, biz, "mercado-libre") for _ in range(3)]
    scores = [await add_score(db, biz, l, "mercado-libre") for l in links]

    # community-level info on all 3 links; official warning on 1; official critical on 1; community warning on 2
    for l, s in zip(links, scores):
        await add_rec(db, biz, l, s, "photo_count", "info")
    await add_rec(db, biz, links[0], scores[0], "listing_completeness_pct", "warning")  # community factor
    await add_rec(db, biz, links[1], scores[1], "listing_completeness_pct", "warning")
    await add_rec(db, biz, links[0], scores[0], "seller_has_unhealthy_items", "critical")  # official
    await add_rec(db, biz, links[2], scores[2], "seller_claims_rate", "warning")  # official

    plan = await pss.PositioningScoreService(db).get_action_plan(biz)
    order = [(p["signal_key"], p["severity"], p["affected"]) for p in plan]

    assert order[0] == ("seller_has_unhealthy_items", "critical", 1)
    assert order[1][0] == "seller_claims_rate"  # official warning before community warning
    assert order[2] == ("listing_completeness_pct", "warning", 2)
    assert order[3] == ("photo_count", "info", 3)
    assert plan[0]["why"]["evidence"] == kb.OFFICIAL and plan[0]["platform"] == "mercado-libre"
    assert "id" not in plan[0]


async def test_recommendations_are_returned_most_urgent_first_and_explained(db):
    biz = uuid4()
    link = await add_link(db, biz, "amazon")
    score = await add_score(db, biz, link, "amazon")
    await add_rec(db, biz, link, score, "catalog_completeness_pct", "info")
    await add_rec(db, biz, link, score, "account_odr_pct", "critical")

    recs = await pss.PositioningScoreService(db).get_open_recommendations(link.id)
    assert [r.severity for r in recs] == ["critical", "info"]
    payload = pss.recommendation_payload(recs[0], "amazon")
    assert payload["why"]["evidence"] == kb.OFFICIAL and "Salud de la cuenta" in payload["why"]["factor"]
    assert pss.recommendation_payload(recs[0], "plataforma-inventada")["why"] is None


async def test_a_link_spelled_mercadolibre_is_scored_with_the_ml_connector(db, monkeypatch):
    biz, conn = uuid4(), uuid4()
    link = PublicationLink(business_id=biz, url="https://x.example/MLA-1", title="t",
                           platform_source="MercadoLibre", seo_enabled=True, connection_id=conn)
    db.add(link)
    await db.commit()
    await db.refresh(link)

    asked = {}

    class FakeConnector:
        async def get_ranking_signals(self, external_id):
            return [RankingSignal("seller_claims_rate", 5.0, measured=True)]

        def score_signals(self, m):
            return {"reputation_score": 10.0, "conversion_score": None, "price_competitiveness_score": None,
                    "listing_quality_score": None, "logistics_score": None, "engagement_score": None}

        def recommendation_rules(self, m):
            return [{"signal_key": "seller_claims_rate", "severity": "critical", "message": "reclamos altos"}]

    async def fake_get_connector(self, platform_name, connection_id):
        asked["platform"] = platform_name
        return FakeConnector()

    monkeypatch.setattr(pss.PositioningScoreService, "get_ranking_connector", fake_get_connector)
    score = await pss.PositioningScoreService(db).compute_score_for_link(biz, link, conn)

    assert asked["platform"] == "mercado-libre"
    assert score is not None and score.platform_name == "mercado-libre"


# ── Endpoints ──

def client(db):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/businesses")

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), email="u@example.com")
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_guide_lists_the_platforms_in_use_first(db):
    biz = uuid4()
    await add_link(db, biz, "mercadolibre")
    async with client(db) as c:
        resp = await c.get(f"/api/v1/businesses/{biz}/seo-config/positioning/algorithm-guide")
    assert resp.status_code == 200
    platforms = resp.json()["platforms"]
    assert platforms[0]["platform"] == "mercado-libre" and platforms[0]["in_use"] is True
    assert {p["platform"] for p in platforms} >= {"amazon", "hotmart", "instagram", "shopify", "etsy"}
    ml = platforms[0]
    assert ml["disclosure"] and ml["not_measurable"] and {f["evidence"] for f in ml["factors"]} == {"official", "community"}


async def test_single_guide_accepts_any_spelling_and_404s_on_unknown(db):
    biz = uuid4()
    base = f"/api/v1/businesses/{biz}/seo-config/positioning/algorithm-guide"
    async with client(db) as c:
        ok = await c.get(f"{base}/MercadoLibre")
        missing = await c.get(f"{base}/no-existe")
    assert ok.status_code == 200 and ok.json()["platform"] == "mercado-libre"
    assert missing.status_code == 404


async def test_compute_explains_why_a_shopify_link_has_no_marketplace_score(db):
    biz = uuid4()
    link = await add_link(db, biz, "shopify")
    async with client(db) as c:
        resp = await c.post(f"/api/v1/businesses/{biz}/seo-config/publication-links/{link.id}/positioning/compute")
    body = resp.json()
    assert resp.status_code == 200 and body["computed"] is False
    assert body["coverage"] == kb.WEB_AUDIT and "sitio propio" in body["reason"]
