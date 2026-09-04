"""Brand Transformation domain — self-contained regression tests (isolated SQLite).

Runs entirely offline: ANTHROPIC_API_KEY is stripped from the environment so
every agent takes its deterministic fallback path. This locks down the
plumbing (agent -> persisted artifact, stage progression, bridge mapping
functions) independent of LLM availability or network access — the same
things repeatedly verified by hand against prod in this domain's build-out.
"""

import json
import os
import uuid

import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from sqlalchemy import Column, String, Table  # noqa: E402
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB  # noqa: E402
from sqlalchemy.dialects.postgresql import UUID as PGUUID  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# conftest.py imports app.main (-> the real Business model, which uses
# postgresql.UUID) before this module's fixtures run, so `businesses`
# lands in Base.metadata with a Postgres-only column type. Shim it for
# SQLite the same way tests/test_ad_budget.py does.


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

from app.core.database import Base  # noqa: E402
from app.domains.brand_transformation import knowledge as K  # noqa: E402
from app.domains.brand_transformation.fomo_bridge import build_specs  # noqa: E402
from app.domains.brand_transformation.identity_bridge import build_plan as build_identity_plan  # noqa: E402
from app.domains.brand_transformation.models import BRAND_TRANSFORMATION_TABLES  # noqa: E402
from app.domains.brand_transformation.orchestrator import TransformationOrchestrator  # noqa: E402
from app.domains.brand_transformation.positioning_bridge import build_plan as build_positioning_plan  # noqa: E402
from app.domains.brand_transformation.service import (  # noqa: E402
    BrandIdentityAgent,
    DiagnosisAgent,
    PositioningAgent,
)


@pytest.fixture(autouse=True)
def _force_fallback_path(monkeypatch):
    """Force every agent's deterministic fallback path for this module.

    llm_available() checks settings.ANTHROPIC_API_KEY (which can come from a
    local .env, independent of os.environ) — monkeypatching the function
    itself is the only way to get network-independent, deterministic
    behaviour regardless of what's configured on the machine running the
    suite.
    """
    monkeypatch.setattr("app.domains.brand_transformation.service.llm_available", lambda: False)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    if "businesses" not in Base.metadata.tables:
        Table("businesses", Base.metadata, Column("id", String(36), primary_key=True))
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.tables["businesses"].create(bind=c, checkfirst=True))
        for t in BRAND_TRANSFORMATION_TABLES:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


PROFILE = {
    "industry": "specialty coffee roaster",
    "what_they_sell": "roasted beans wholesale + a small cafe",
    "current_positioning": "good quality coffee at a fair price",
    "known_competitors": ["Blue Bottle", "Starbucks"],
    "revenue_model": "retail + wholesale",
    "target_customer": "cafes and home brewers",
    "price_point": "mid",
    "notes": "commoditized, competes on price",
}


# --------------------------------------------------------------------------
# agents (fallback path — llm_available() forced False for this module)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_diagnosis_agent_fallback_persists(db):
    bid = uuid.uuid4()
    row = await DiagnosisAgent(db).run(bid, PROFILE)
    assert row.business_id == bid
    assert row.generated_by == "fallback"
    assert 0 <= row.referent_potential_score <= 100
    assert row.confidence <= 55  # fallback confidence ceiling (see _draft_then_refine)
    latest = await DiagnosisAgent(db).latest(bid)
    assert latest.id == row.id


@pytest.mark.asyncio
async def test_positioning_agent_fallback_persists(db):
    bid = uuid.uuid4()
    diag = await DiagnosisAgent(db).run(bid, PROFILE)
    pos = await PositioningAgent(db).run(
        bid, PROFILE, context={"closest_precedent": diag.closest_precedent, "referent_gap": diag.referent_gap},
    )
    assert pos.generated_by == "fallback"
    assert pos.positioning_statement
    latest = await PositioningAgent(db).latest(bid)
    assert latest.id == pos.id


@pytest.mark.asyncio
async def test_brand_identity_agent_fallback_persists(db):
    bid = uuid.uuid4()
    identity = await BrandIdentityAgent(db).run(bid, PROFILE, context=None)
    assert identity.generated_by == "fallback"
    assert identity.primary_archetype
    assert await BrandIdentityAgent(db).by_id(bid, identity.id) is not None


# --------------------------------------------------------------------------
# orchestrator — stage progression across all 8 etapas
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_orchestrator_run_stage_advances_pointer(db):
    orch = TransformationOrchestrator(db)
    prog = await orch.create_program(uuid.uuid4(), "Test", PROFILE)
    assert prog.current_stage == "diagnosis"
    r = await orch.run_stage(prog, "diagnosis")
    assert r["next_stage"] == "positioning"
    assert r["completed_stages"] == ["diagnosis"]
    assert r["bridge_result"] is None  # no auto_bridges configured


@pytest.mark.asyncio
async def test_orchestrator_run_all_completes_without_bridges(db):
    orch = TransformationOrchestrator(db)
    prog = await orch.create_program(uuid.uuid4(), "Test Program", PROFILE)
    results = await orch.run_all(prog)
    assert len(results) == len(K.STAGE_ORDER)

    prog2 = await orch.get_program(prog.id)
    assert prog2.status == "completed"
    assert set(prog2.completed_stages) == set(K.STAGE_ORDER)
    assert prog2.coherence_audit is not None
    assert prog2.roadmap is not None
    assert prog2.execution_plan is not None


def test_grade_severity_thresholds():
    assert TransformationOrchestrator._grade_severity(90, "on-brand") == ("ok", False)
    assert TransformationOrchestrator._grade_severity(60, "minor-drift") == ("warn", True)
    assert TransformationOrchestrator._grade_severity(30, None) == ("critical", True)
    assert TransformationOrchestrator._grade_severity(None, "major-drift")[0] == "critical"


# --------------------------------------------------------------------------
# bridges — deterministic mapping functions (no DB, no LLM)
# --------------------------------------------------------------------------

def test_fomo_bridge_maps_known_levers_and_skips_unmapped():
    class PB:
        id = uuid.uuid4()
        mechanisms = [
            {"lever": "artificial_scarcity", "why_it_fits": "x", "implementation": "y"},
            {"lever": "identity_and_tribe", "why_it_fits": "z"},  # no on-site primitive
        ]
        content_hooks = [{"mechanism": "artificial_scarcity", "copy_angle": "Only 50 made"}]
        launch_ritual = {"the_hook": "sells out"}
        cadence = "monthly"

    plan = build_specs(PB())
    assert len(plan["campaign_specs"]) == 1
    spec = plan["campaign_specs"][0]
    assert spec["campaign_type"] == "limited_spots"
    assert spec["headline"] == "Only 50 made"
    assert plan["skipped_levers"] == [
        {"lever": "identity_and_tribe", "reason": "no on-site campaign primitive for this lever"}
    ]


def test_positioning_bridge_flags_competitors_without_url():
    class PS:
        id = uuid.uuid4()
        alternatives_matrix = [{"alternative": "Acme", "what_customer_keeps": "safety", "what_they_lose": "speed"}]
        attribute_value_proof = [{"attribute": "ships in 2h", "value": "no waiting"}]
        enemy_analysis = {"enemy": "the slow status quo"}
        the_enemy = None
        positioning_statement = "For X, we are the fast Y"
        one_liner = "Fast Y"
        reframe = {"to": "a premium choice"}

    plan = build_positioning_plan(PS(), [{"name": "Acme", "url": "https://acme.com"}, {"name": "NoUrl Inc"}])
    assert len(plan["monitors"]) == 1
    assert len(plan["battlecards"]) == 2
    assert plan["skipped"] == [{"competitor": "NoUrl Inc", "reason": "no URL — monitor requires one; battlecard only"}]


def test_identity_bridge_builds_all_asset_kinds():
    class BI:
        id = uuid.uuid4()
        primary_archetype = "Outlaw"
        secondary_archetype = None
        tagline = "Do it properly"
        taglines_alt = ["a", "b"]
        verbal_identity = {
            "attributes": [{"adj": "blunt", "sounds_like": "x", "not": "y"}],
            "lexicon": {"use": ["real"], "ban": ["synergy"]},
            "rhythm": "short", "humor": "dry", "first_line_rule": "name the enemy",
        }
        identity_consistency_rules = ["rule1"]
        manifesto = "We believe..."
        sample_rewrites = [{"context": "hero", "text": "Hi"}]
        story_spine = {"world": "w"}
        visual_brief = {"mood": "bold", "moodboard_search_terms": ["a", "b"]}

    plan = build_identity_plan(BI())
    kinds = [a["content_type"] for a in plan["assets"]]
    assert kinds == ["manifesto", "tagline", "copy:hero", "story_spine", "visual_brief"]
