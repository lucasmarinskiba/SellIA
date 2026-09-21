"""SEO switches <-> Brain Interaction Map: one control, not two.

Covers the guard (Map nodes really stop the work), the FOMO generation gate on
every path, the two-way sync of the global switch, and the Map registry entries.
"""

import json
import os
import uuid
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from sqlalchemy import select
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

import app.api.v1.brain as brain_api  # noqa: E402
import app.domains.seo_config.router  # noqa: E402,F401  (loads every model into metadata)
from app.core.brain import get_brain_registry  # noqa: E402
from app.domains.automations.models import AutomationToggle, ToggleAuditLog  # noqa: E402
from app.domains.seo_config import brain_toggles as bt  # noqa: E402
from app.domains.seo_config.agent_guard import SEOAgentGuard  # noqa: E402
from app.domains.seo_config.fomo_generator import PublicationFOMOGenerator  # noqa: E402
from app.domains.seo_config.models import PlatformSEOStatus, PublicationLink, SEOConfig  # noqa: E402
from app.domains.seo_config.service import SEOConfigService  # noqa: E402


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    tables = (
        AutomationToggle.__table__, ToggleAuditLog.__table__, SEOConfig.__table__,
        PlatformSEOStatus.__table__, PublicationLink.__table__,
    )
    async with engine.begin() as conn:
        for t in tables:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


async def audit_rows(db):
    return (await db.execute(select(ToggleAuditLog))).scalars().all()


# ── helpers ──

@pytest.mark.parametrize("name,expected", [
    ("mercado-libre", "platform.mercadolibre"),
    ("mercado_libre", "platform.mercadolibre"),
    ("MercadoLibre", "platform.mercadolibre"),
    ("amazon", "platform.amazon"),
    ("", None),
    (None, None),
])
def test_platform_names_normalise_to_the_map_id(name, expected):
    assert bt.platform_brain_id(name) == expected


async def test_capability_defaults_to_enabled_and_follows_the_toggle_row(db):
    biz = uuid4()
    assert await bt.is_brain_capability_enabled(db, biz, bt.SEO_POSITIONING) is True

    await bt.set_brain_capability(db, biz, bt.SEO_POSITIONING, False)
    await db.commit()
    assert await bt.is_brain_capability_enabled(db, biz, bt.SEO_POSITIONING) is False
    assert await bt.is_brain_capability_enabled(db, uuid4(), bt.SEO_POSITIONING) is True  # other business unaffected

    await bt.set_brain_capability(db, biz, bt.SEO_POSITIONING, True)
    await db.commit()
    assert await bt.is_brain_capability_enabled(db, biz, bt.SEO_POSITIONING) is True
    assert [a.action for a in await audit_rows(db)] == ["disabled", "enabled"]


async def test_setting_the_same_state_again_is_a_noop(db):
    biz = uuid4()
    await bt.set_brain_capability(db, biz, bt.SEO_POSITIONING, False)
    await db.commit()
    await bt.set_brain_capability(db, biz, bt.SEO_POSITIONING, False)
    await db.commit()
    assert len(await audit_rows(db)) == 1


# ── The guard ──

async def test_guard_allows_by_default(db):
    g = SEOAgentGuard(db)
    biz = uuid4()
    assert await g.can_run_seo_agent(biz, "positioning", platform_name="mercado-libre")
    assert await g.can_run_seo_agent(biz, "fomo_engine", platform_name="amazon")


async def test_global_seo_off_blocks_everything(db):
    biz = uuid4()
    db.add(SEOConfig(business_id=biz, global_seo_enabled=False))
    await db.commit()
    g = SEOAgentGuard(db)
    assert not await g.can_run_seo_agent(biz, "positioning")
    assert not await g.can_run_seo_agent(biz, "fomo_engine")


async def test_positioning_node_off_stops_every_positioning_alias_but_not_fomo(db):
    biz = uuid4()
    await bt.set_brain_capability(db, biz, bt.SEO_POSITIONING, False)
    await db.commit()
    g = SEOAgentGuard(db)
    for agent in ("positioning", "positioning_agent", "store_positioning"):
        assert not await g.can_run_seo_agent(biz, agent), agent
    assert await g.can_run_seo_agent(biz, "fomo_engine")


async def test_fomo_node_off_stops_fomo_but_not_positioning(db):
    biz = uuid4()
    await bt.set_brain_capability(db, biz, bt.FOMO_PUBLICATIONS, False)
    await db.commit()
    g = SEOAgentGuard(db)
    assert not await g.can_run_seo_agent(biz, "fomo_engine")
    assert not await g.can_run_seo_agent(biz, "fomo_engine_agent")
    assert await g.can_run_seo_agent(biz, "positioning")


async def test_turning_a_platform_off_on_the_map_stops_seo_on_that_platform_only(db):
    biz = uuid4()
    await bt.set_brain_capability(db, biz, "platform.mercadolibre", False)
    await db.commit()
    g = SEOAgentGuard(db)
    for spelling in ("mercado-libre", "mercado_libre", "mercadolibre"):
        assert not await g.can_run_seo_agent(biz, "positioning", platform_name=spelling), spelling
    assert await g.can_run_seo_agent(biz, "positioning", platform_name="amazon")


async def test_platform_seo_status_off_still_blocks(db):
    biz, conn = uuid4(), uuid4()
    db.add(PlatformSEOStatus(business_id=biz, connection_id=conn, platform_name="amazon", seo_enabled=False))
    await db.commit()
    assert not await SEOAgentGuard(db).can_run_seo_agent(biz, "positioning", platform_id=conn)


async def test_platform_name_is_resolved_from_the_connection_when_omitted(db):
    biz, conn = uuid4(), uuid4()
    db.add(PlatformSEOStatus(business_id=biz, connection_id=conn, platform_name="mercado-libre", seo_enabled=True))
    await bt.set_brain_capability(db, biz, "platform.mercadolibre", False)
    await db.commit()
    assert not await SEOAgentGuard(db).can_run_seo_agent(biz, "positioning", platform_id=conn)


# ── Two-way sync of the global switch ──

async def test_phase12_global_toggle_is_mirrored_on_the_map(db):
    biz = uuid4()
    svc = SEOConfigService(db)

    await svc.toggle_global_seo(biz, False, user_email="dueño@example.com")
    assert (await svc.get_or_create_seo_config(biz)).global_seo_enabled is False
    assert await bt.is_brain_capability_enabled(db, biz, bt.SEO_POSITIONING) is False
    assert (await audit_rows(db))[0].changed_by_email == "dueño@example.com"

    await svc.toggle_global_seo(biz, True)
    assert (await svc.get_or_create_seo_config(biz)).global_seo_enabled is True
    assert await bt.is_brain_capability_enabled(db, biz, bt.SEO_POSITIONING) is True


async def test_map_to_config_sync_does_not_write_the_map_back(db):
    biz = uuid4()
    await SEOConfigService(db).sync_global_from_brain(biz, False)
    await db.commit()
    assert (await SEOConfigService(db).get_or_create_seo_config(biz)).global_seo_enabled is False
    assert (await db.execute(select(AutomationToggle))).scalars().all() == []  # no ping-pong


async def test_brain_endpoint_flips_the_global_seo_switch(db, monkeypatch):
    biz, user = uuid4(), SimpleNamespace(id=uuid4(), email="u@example.com")

    async def fake_user(request, db):  # noqa: ANN001
        return user

    async def fake_business(u, db):  # noqa: ANN001
        return biz

    monkeypatch.setattr(brain_api, "_optional_user", fake_user)
    monkeypatch.setattr(brain_api, "_resolve_business_id", fake_business)

    out = await brain_api.brain_set_toggle(
        brain_api.ToggleUpdate(brain_id="automation.seo_positioning", enabled=False), SimpleNamespace(), db
    )
    assert out["ok"] and "automation.seo_positioning" in out["disabled_brain_ids"]
    assert (await SEOConfigService(db).get_or_create_seo_config(biz)).global_seo_enabled is False

    # A different node must not touch the SEO switch.
    other = uuid4()
    monkeypatch.setattr(brain_api, "_resolve_business_id", lambda u, d: _async(other))
    await brain_api.brain_set_toggle(
        brain_api.ToggleUpdate(brain_id="automation.cart_recovery", enabled=False), SimpleNamespace(), db
    )
    assert (await db.execute(select(SEOConfig).where(SEOConfig.business_id == other))).scalar_one_or_none() is None


async def _async(value):
    return value


# ── FOMO generation is gated on every path ──

def _link(biz, **kw):
    defaults = dict(business_id=biz, url="https://articulo.mercadolibre.com.ar/MLA-1-x-_JM", title="t",
                    platform_source="mercado-libre", seo_enabled=True)
    defaults.update(kw)
    return PublicationLink(**defaults)


async def test_may_generate_respects_link_global_and_map_switches(db):
    biz = uuid4()
    gen = PublicationFOMOGenerator(db)
    link = _link(biz)
    db.add(link)
    await db.commit()

    assert await gen._may_generate(biz, link) is True

    link.seo_enabled = False
    assert await gen._may_generate(biz, link) is False
    link.seo_enabled = True

    await bt.set_brain_capability(db, biz, bt.FOMO_PUBLICATIONS, False)
    await db.commit()
    assert await gen._may_generate(biz, link) is False
    assert await gen.is_fomo_generation_enabled(biz) is False


async def test_auto_rotation_and_multilanguage_path_does_not_generate_when_off(db, monkeypatch):
    """generate_fomo_copy backs auto-rotation and multi-language generation; it used to skip every toggle."""
    import app.domains.seo_config.fomo_generator as fg

    class Boom:
        def __init__(self, *a, **k):
            raise AssertionError("the FOMO agent must not run while SEO is off")

    monkeypatch.setattr(fg, "FOMOEngineAgent", Boom)
    biz = uuid4()
    link = _link(biz)
    db.add(link)
    db.add(SEOConfig(business_id=biz, global_seo_enabled=False))
    await db.commit()

    assert await PublicationFOMOGenerator(db).generate_fomo_copy(biz, link.id, "mercado-libre") is None


# ── The Map registry ──

def test_registry_exposes_both_seo_nodes_wired_to_the_marketplaces():
    registry = get_brain_registry()
    graph = registry.graph()
    ids = {n["id"] for n in graph["nodes"]}
    for node in (bt.SEO_POSITIONING, bt.FOMO_PUBLICATIONS):
        assert node in ids
        targets = {e["target"] for e in graph["edges"] if e["source"] == node}
        assert {"platform.mercadolibre", "platform.amazon", "platform.hotmart", "platform.instagram"} <= targets

    flows = {f["id"]: f for f in registry.flows()["flows"]}
    for node in (bt.SEO_POSITIONING, bt.FOMO_PUBLICATIONS):
        assert f"flow.{node}" in flows
