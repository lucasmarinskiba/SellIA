"""Harvey competitor map: reading sites, isolation, the brief and how it feeds the drafts. Isolated SQLite."""

# The db fixture comes from test_harvey, so every test argument "redefines" it.
# ruff: noqa: F811

import httpx
import pytest
from test_harvey import _Biz, _fake_model, _setup, db  # noqa: F401 - db is a pytest fixture

from app.domains.harvey import competitors as reader
from app.domains.harvey import discovery
from app.domains.harvey import service as harvey_service
from app.domains.harvey.competitors_service import CompetitorError, CompetitorService
from app.domains.harvey.models import HarveyCompetitiveBrief, HarveyCompetitor
from app.domains.harvey.service import HarveyService

HOME = """<html><head><title>Rival SA - Panadería</title>
<meta name="description" content="Pan artesanal con envío"></head><body>
<h1>El mejor pan del barrio</h1><h2>Envío gratis en compras de más de $15.000</h2>
<a href="/precios">Precios</a><a href="/contacto">Contacto</a>
<p>Pan de campo $1.200. Aprovechá 20% off en tu primera compra. Texto largo sin relevancia alguna aquí.</p>
</body></html>"""
PRICES = "<h2>Planes</h2><p>Plan mensual USD 29 por mes. Garantía de 30 días sin preguntas.</p>"


def _public_dns(monkeypatch):
    async def fake_resolve(host):
        return ["93.184.216.34"]

    monkeypatch.setattr(discovery, "resolve_host", fake_resolve)


def _transport(pages, calls=None):
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(request.url.path)
        body = pages.get(request.url.path)
        if body is None:
            return httpx.Response(404)
        return httpx.Response(200, text=body, headers={"content-type": "text/html"})

    return httpx.MockTransport(handler)


@pytest.fixture
def cdb(db):
    return db


# ── reading a page (pure) ─────────────────────────────────────────────────
def test_extract_keeps_what_the_page_says():
    got = reader.extract(HOME)
    assert got["title"] == "Rival SA - Panadería" and got["description"] == "Pan artesanal con envío"
    assert "El mejor pan del barrio" in got["headlines"]
    assert any("$1.200" in p for p in got["prices"])
    assert any("20% off" in o for o in got["offers"])


def test_extract_survives_broken_markup_and_empty_pages():
    assert reader.extract("")["prices"] == []
    assert reader.extract("<h1>sin cerrar <p>$ 500")["prices"]  # keeps what it could parse


@pytest.mark.asyncio
async def test_scan_reads_home_and_price_pages_and_honours_robots(monkeypatch):
    _public_dns(monkeypatch)
    pages = {"/robots.txt": "User-agent: *\nDisallow: /contacto\n", "/": HOME, "/precios": PRICES, "/contacto": "x"}
    calls: list[str] = []
    async with discovery.make_client(_transport(pages, calls)) as client:
        snap = await reader.scan(client, "rival.com")
    assert any("USD 29" in p for p in snap["prices"]) and any("Garantía" in o for o in snap["offers"])
    assert "/contacto" not in calls  # not a price page, and disallowed anyway

    blocked = {"/robots.txt": "User-agent: *\nDisallow: /\n", "/": HOME}
    async with discovery.make_client(_transport(blocked)) as client:
        with pytest.raises(discovery.DiscoveryError, match="robots"):
            await reader.scan(client, "rival.com")


# ── the map ───────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_add_validates_and_rejects_duplicates_internal_urls_and_a_second_own_site(cdb, monkeypatch):
    _public_dns(monkeypatch)
    biz, svc = _Biz(), CompetitorService(cdb)
    row = await svc.add(biz.id, "https://Rival.com/tienda?x=1", "direct")
    assert row.url == "https://rival.com"
    with pytest.raises(CompetitorError) as e:
        await svc.add(biz.id, "rival.com", "indirect")
    assert e.value.status_code == 409
    with pytest.raises(CompetitorError):
        await svc.add(biz.id, "http://127.0.0.1/", "direct")
    with pytest.raises(CompetitorError):
        await svc.add(biz.id, "otro.com", "enemigo")
    await svc.add(biz.id, "mio.com", "own")
    with pytest.raises(CompetitorError, match="sitio propio"):
        await svc.add(biz.id, "mio2.com", "own")


@pytest.mark.asyncio
async def test_the_map_has_a_size_cap(cdb, monkeypatch):
    _public_dns(monkeypatch)
    biz, svc = _Biz(), CompetitorService(cdb)
    for i in range(15):
        await svc.add(biz.id, f"sitio{i}.com", "direct")
    with pytest.raises(CompetitorError, match="hasta 15"):
        await svc.add(biz.id, "uno-mas.com", "direct")


@pytest.mark.asyncio
async def test_other_business_cannot_see_scan_or_delete_my_competitors(cdb, monkeypatch):
    _public_dns(monkeypatch)
    mine, intruder, svc = _Biz(), _Biz(), CompetitorService(cdb)
    row = await svc.add(mine.id, "rival.com", "direct")
    assert await svc.list_all(intruder.id) == []
    for call in (svc.get(intruder.id, row.id), svc.remove(intruder.id, row.id)):
        with pytest.raises(CompetitorError) as e:
            await call
        assert e.value.status_code == 404
    assert len(await svc.list_all(mine.id)) == 1


@pytest.mark.asyncio
async def test_scan_one_stores_the_snapshot_and_throttles_rereads(cdb, monkeypatch):
    _public_dns(monkeypatch)
    biz, svc = _Biz(), CompetitorService(cdb)
    row = await svc.add(biz.id, "rival.com", "direct")
    async with discovery.make_client(_transport({"/robots.txt": "", "/": HOME, "/precios": PRICES})) as client:
        row = await svc.scan_one(row, client)
        assert row.name == "Rival SA - Panadería" and row.snapshot["prices"] and row.last_error == ""
        with pytest.raises(CompetitorError) as e:
            await svc.scan_one(row, client)
    assert e.value.status_code == 429


@pytest.mark.asyncio
async def test_an_unreadable_site_records_the_error_instead_of_failing(cdb, monkeypatch):
    _public_dns(monkeypatch)
    biz, svc = _Biz(), CompetitorService(cdb)
    row = await svc.add(biz.id, "caido.com", "direct")
    async with discovery.make_client(httpx.MockTransport(lambda r: httpx.Response(500))) as client:
        row = await svc.scan_one(row, client)
    assert row.last_error and not row.snapshot  # a 500 on robots.txt counts as "not allowed"


# ── the brief ─────────────────────────────────────────────────────────────
async def _studied(cdb, monkeypatch, biz):
    _public_dns(monkeypatch)
    svc = CompetitorService(cdb)
    row = await svc.add(biz.id, "rival.com", "direct")
    async with discovery.make_client(_transport({"/robots.txt": "", "/": HOME, "/precios": PRICES})) as client:
        await svc.scan_one(row, client)
    return svc


@pytest.mark.asyncio
async def test_analyze_stores_a_model_brief_and_clips_what_it_returns(cdb, monkeypatch):
    biz = _Biz()
    _, biz, profile, _ = await _setup(cdb, biz)
    svc = await _studied(cdb, monkeypatch, biz)
    _fake_model(monkeypatch, {
        "summary": "Rival publica envío gratis.", "gaps": ["No decís el precio"], "opportunities": "no es lista",
        "angles": ["Entrega el mismo día", "a", "b", "descartado por ser el cuarto"], "icp_hints": [],
    })
    monkeypatch.setattr("app.domains.harvey.competitors_service.ask_json", harvey_service.ask_json)
    monkeypatch.setattr("app.domains.harvey.competitors_service.llm_available", lambda: True)
    row = await svc.analyze(biz, profile)
    assert row.brief["source"] == "model" and len(row.brief["angles"]) == 3
    assert row.brief["opportunities"] == []  # a non-list from the model is dropped, not trusted


@pytest.mark.asyncio
async def test_analyze_without_a_model_keeps_only_facts(cdb, monkeypatch):
    biz = _Biz()
    _, biz, profile, _ = await _setup(cdb, biz)
    svc = await _studied(cdb, monkeypatch, biz)
    monkeypatch.setattr("app.domains.harvey.competitors_service.llm_available", lambda: False)
    row = await svc.analyze(biz, profile)
    assert row.brief["source"] == "facts" and row.brief["angles"] == []
    assert await svc.angles_for_prompt(biz.id) == ""


@pytest.mark.asyncio
async def test_analyze_needs_sites(cdb):
    biz = _Biz()
    _, biz, profile, _ = await _setup(cdb, biz)
    with pytest.raises(CompetitorError) as e:
        await CompetitorService(cdb).analyze(biz, profile)
    assert e.value.status_code == 422


@pytest.mark.asyncio
async def test_angles_reach_the_draft_prompt_fenced_and_only_for_their_business(cdb, monkeypatch):
    biz = _Biz()
    svc0, biz, profile, prospect = await _setup(cdb, biz)
    svc = await _studied(cdb, monkeypatch, biz)
    cdb.add(HarveyCompetitiveBrief(business_id=biz.id, brief={"angles": ["Entrega el mismo día"]}))
    await cdb.commit()

    prompts: list[str] = []

    async def capture(system, prompt, **kw):
        prompts.append(prompt)
        return {"subject": "hola", "body": "¿Cómo reciben pedidos?"}

    monkeypatch.setattr(harvey_service, "ask_json", capture)
    monkeypatch.setattr(harvey_service, "llm_available", lambda: True)
    await HarveyService(cdb).draft_first_email(biz, profile, prospect)
    assert "Entrega el mismo día" in prompts[0] and '<untrusted source="ángulos de mercado">' in prompts[0]
    assert "sin nombrar competidores" in prompts[0]

    other = _Biz()
    assert await svc.angles_for_prompt(other.id) == ""
