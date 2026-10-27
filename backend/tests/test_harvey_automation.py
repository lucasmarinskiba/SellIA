"""Harvey automatic loop, discovery and reply answering. Reuses the isolated-SQLite setup of test_harvey."""

# The db/smtp fixtures are imported from test_harvey, so every test argument "redefines" them.
# ruff: noqa: F811

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from test_harvey import (  # noqa: F401 - db and smtp are pytest fixtures
    OPT_OUT,
    _approved,
    _connect_mailbox,
    _fake_inbox,
    _fake_model,
    _inbound,
    _send_step1,
    _setup,
    db,
    smtp,
)

from app.domains.harvey import discovery
from app.domains.harvey import service as harvey_service
from app.domains.harvey.schedule import effective_send_cap, in_send_window, warmup_cap
from app.domains.harvey.service import HarveyError

# Tuesday 2026-10-27 13:00 UTC = 10:00 in Buenos Aires (UTC-3), inside the default 9-18 window.
TUE_10AM = datetime(2026, 10, 27, 13, 0, tzinfo=timezone.utc)
SATURDAY = datetime(2026, 10, 31, 13, 0, tzinfo=timezone.utc)


def _profile(**kw):
    base = dict(
        send_window_start=9, send_window_end=18, send_timezone="America/Argentina/Buenos_Aires",
        send_weekdays_only=True, max_daily_sends=30, warmup_started_at=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


# ── schedule (pure) ───────────────────────────────────────────────────────
def test_send_window_uses_the_business_timezone_and_weekdays():
    assert in_send_window(_profile(), TUE_10AM)
    assert not in_send_window(_profile(), TUE_10AM.replace(hour=11))  # 08:00 local
    assert not in_send_window(_profile(), TUE_10AM.replace(hour=21))  # 18:00 local: end is exclusive
    assert not in_send_window(_profile(), SATURDAY)
    assert in_send_window(_profile(send_weekdays_only=False), SATURDAY)


def test_unknown_timezone_falls_back_to_utc():
    assert in_send_window(_profile(send_timezone="Mars/Olympus"), TUE_10AM)  # 13:00 UTC


def test_warmup_ramps_up_and_never_exceeds_the_business_limit():
    start = TUE_10AM
    assert warmup_cap(start, start) == 5
    assert warmup_cap(start, start + timedelta(days=1)) == 5
    assert warmup_cap(start, start + timedelta(days=2)) == 10
    assert warmup_cap(start, start + timedelta(days=10)) == 30
    assert effective_send_cap(_profile(warmup_started_at=start), start) == 5
    assert effective_send_cap(_profile(warmup_started_at=start, max_daily_sends=8), start + timedelta(days=10)) == 8
    assert effective_send_cap(_profile(), start) == 30  # no warm-up configured


@pytest.mark.asyncio
async def test_enabling_starts_warmup_and_schedule_is_validated(db):
    svc, biz, profile, _ = await _setup(db)
    assert profile.warmup_started_at is not None
    with pytest.raises(HarveyError) as e:
        await svc.update_profile(biz, {"send_window_start": 18, "send_window_end": 9})
    assert e.value.status_code == 422
    with pytest.raises(HarveyError):
        await svc.update_profile(biz, {"send_timezone": "Mars/Olympus"})
    profile = await svc.update_profile(biz, {"send_window_start": 8, "send_timezone": "America/Bogota"})
    assert profile.send_window_start == 8


# ── discovery: extraction and SSRF ────────────────────────────────────────
PAGE = """<html><head><title>Cliente SA | Panadería</title>
<meta name="description" content="Panadería artesanal en Córdoba"></head><body>
<a href="mailto:Info@cliente.com?subject=hola">escribinos</a>
<p>Ventas: ventas@cliente.com · personal: juan@gmail.com · noreply@cliente.com · ajeno@otro.com
logo@2x.png</p><a href="/contacto">Contacto</a></body></html>"""


def test_extract_keeps_only_business_addresses_on_the_sites_own_domain():
    found = {f.email: f for f in discovery.extract_emails(PAGE, "cliente.com", "https://cliente.com/")}
    assert set(found) == {"info@cliente.com", "ventas@cliente.com"}
    assert found["info@cliente.com"].is_company_inbox


@pytest.mark.parametrize("raw", ["ftp://a.com", "https://u:p@a.com", "https://a.com:8080", "", "http://"])
def test_normalize_url_rejects_unsafe_urls(raw):
    with pytest.raises(discovery.DiscoveryError):
        discovery.normalize_url(raw)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url", ["http://127.0.0.1/", "http://10.0.0.5/", "http://169.254.169.254/latest/", "http://[::1]/", "http://192.168.1.1/"]
)
async def test_internal_addresses_are_never_fetched(url):
    with pytest.raises(discovery.DiscoveryError):
        await discovery.assert_public_url(url)


@pytest.mark.asyncio
async def test_a_hostname_that_resolves_to_a_private_address_is_refused(monkeypatch):
    async def fake_resolve(host):
        return ["10.1.2.3"]

    monkeypatch.setattr(discovery, "resolve_host", fake_resolve)
    with pytest.raises(discovery.DiscoveryError):
        await discovery.assert_public_url("https://sneaky.example.com/")


def _public_dns(monkeypatch):
    async def fake_resolve(host):
        return ["93.184.216.34"]

    monkeypatch.setattr(discovery, "resolve_host", fake_resolve)


def _site_transport(pages, calls=None):
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        body = pages.get(request.url.path)
        if body is None:
            return httpx.Response(404)
        status, text = body if isinstance(body, tuple) else (200, body)
        return httpx.Response(status, text=text, headers={"content-type": "text/html"})

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_redirect_to_an_internal_address_is_blocked(monkeypatch):
    async def resolve(host):
        return ["10.0.0.1"] if host == "internal.local" else ["93.184.216.34"]

    monkeypatch.setattr(discovery, "resolve_host", resolve)

    def handler(request):
        return httpx.Response(302, headers={"location": "http://internal.local/admin"})

    async with discovery.make_client(httpx.MockTransport(handler)) as client:
        with pytest.raises(discovery.DiscoveryError):
            await discovery.fetch(client, "https://cliente.com/")


@pytest.mark.asyncio
async def test_scan_follows_the_contact_page_and_honours_robots(monkeypatch):
    _public_dns(monkeypatch)
    pages = {
        "/robots.txt": "User-agent: *\nDisallow: /privado\n",
        "/": '<title>Cliente SA | Panadería</title><a href="/contacto">Contacto</a><a href="/privado/x">x</a>',
        "/contacto": '<a href="mailto:hola@cliente.com">mail</a>',
    }
    async with discovery.make_client(_site_transport(pages)) as client:
        site = await discovery.scan_site(client, "cliente.com")
    assert site.company == "Cliente SA" and [e.email for e in site.emails] == ["hola@cliente.com"]
    assert site.emails[0].is_company_inbox and site.emails[0].source_url.endswith("/contacto")

    blocked = {"/robots.txt": "User-agent: *\nDisallow: /\n", "/": "<title>x</title>"}
    async with discovery.make_client(_site_transport(blocked)) as client:
        with pytest.raises(discovery.DiscoveryError, match="robots"):
            await discovery.scan_site(client, "cliente.com")


@pytest.mark.asyncio
async def test_social_networks_are_not_prospects(monkeypatch):
    _public_dns(monkeypatch)
    async with discovery.make_client(_site_transport({})) as client:
        with pytest.raises(discovery.DiscoveryError):
            await discovery.scan_site(client, "https://www.instagram.com/panaderia")


@pytest.mark.asyncio
async def test_search_needs_a_key_and_drops_platform_results(monkeypatch):
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    assert not discovery.search_available()
    async with discovery.make_client(httpx.MockTransport(lambda r: httpx.Response(500))) as client:
        with pytest.raises(discovery.DiscoveryError, match="BRAVE_SEARCH_API_KEY"):
            await discovery.search_sites(client, "panaderías córdoba")

    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "k")
    payload = {"web": {"results": [
        {"url": "https://panaderiasol.com/menu"}, {"url": "https://www.facebook.com/x"},
        {"url": "https://panaderiasol.com/otra"}, {"url": "https://otra.com.ar/"},
    ]}}
    seen = {}

    def handler(request):
        seen["token"] = request.headers["x-subscription-token"]
        return httpx.Response(200, json=payload)

    async with discovery.make_client(httpx.MockTransport(handler)) as client:
        urls = await discovery.search_sites(client, "panaderías córdoba")
    assert urls == ["https://panaderiasol.com", "https://otra.com.ar"] and seen["token"] == "k"


# ── discovery through the service ─────────────────────────────────────────
PAGES = {
    "/robots.txt": (404, ""),
    "/": '<title>Lo de Marta</title><meta name="description" content="Viandas caseras"><a href="mailto:hola@lodemarta.com">m</a>',
}


@pytest.mark.asyncio
async def test_discovered_prospects_wait_for_a_person_to_verify_them(db, monkeypatch):
    _public_dns(monkeypatch)
    svc, biz, profile, _ = await _setup(db)
    out = await svc.discover(biz, profile, urls=["lodemarta.com"], transport=_site_transport(PAGES))
    assert out["counts"]["created"] == 1 and out["sites"][0]["outcome"] == "added"
    prospect = (await svc.list_prospects(biz.id))[0]
    assert prospect.email == "hola@lodemarta.com" and prospect.source == "discovery"
    assert prospect.email_status == "scraped" and prospect.notes == "Viandas caseras"

    _fake_model(monkeypatch, {"subject": "viandas", "body": "¿Cómo reciben pedidos?"})
    with pytest.raises(HarveyError) as e:  # no model credits spent on an unverified address
        await svc.draft_step(biz, profile, prospect, 1)
    assert e.value.status_code == 409

    assert await svc.verify_prospects(biz.id, [prospect.id], True) == 1
    await db.refresh(prospect)
    assert (await svc.draft_step(biz, profile, prospect, 1)).status == "pending_review"


@pytest.mark.asyncio
async def test_discovery_skips_known_sites_and_respects_the_daily_limit(db, monkeypatch):
    _public_dns(monkeypatch)
    svc, biz, profile, _ = await _setup(db, max_daily_discoveries=1)
    await svc.discover(biz, profile, urls=["lodemarta.com"], transport=_site_transport(PAGES))
    with pytest.raises(HarveyError) as e:
        await svc.discover(biz, profile, urls=["otra.com"], transport=_site_transport(PAGES))
    assert e.value.status_code == 429

    profile = await svc.update_profile(biz, {"max_daily_discoveries": 5})
    again = await svc.discover(biz, profile, urls=["lodemarta.com"], transport=_site_transport(PAGES))
    assert again["counts"]["created"] == 0 and again["sites"][0]["outcome"] == "exists"


@pytest.mark.asyncio
async def test_discovery_does_not_add_do_not_contact_domains(db, monkeypatch):
    _public_dns(monkeypatch)
    svc, biz, profile, _ = await _setup(db, do_not_contact=["lodemarta.com"])
    out = await svc.discover(biz, profile, urls=["lodemarta.com"], transport=_site_transport(PAGES))
    assert out["counts"]["created"] == 0 and out["counts"]["skipped"] == 1


@pytest.mark.asyncio
async def test_verify_cannot_touch_another_business_or_provided_addresses(db, monkeypatch):
    svc, biz, profile, prospect = await _setup(db)
    assert await svc.verify_prospects(uuid.uuid4(), [prospect.id], True) == 0
    assert await svc.verify_prospects(biz.id, [prospect.id], False) == 0  # "provided" is the business's own list


# ── answering replies ─────────────────────────────────────────────────────
async def _replied(db, monkeypatch, smtp, classification="interested", answer="¡Genial! ¿Te sirve el jueves?"):
    svc, biz, profile, prospect, first = await _send_step1(db, monkeypatch)
    _fake_inbox(monkeypatch, [_inbound(10, from_email="ana@cliente.com", in_reply_to=first.message_id)])
    _fake_model(monkeypatch, {"classification": classification, "answer": answer})
    await svc.sync_inbox(biz, profile)
    reply = (await svc.list_replies(biz.id))[0]
    return svc, biz, profile, prospect, reply


@pytest.mark.asyncio
async def test_answer_is_staged_approved_and_threaded_under_the_reply(db, monkeypatch, smtp):
    svc, biz, profile, prospect, reply = await _replied(db, monkeypatch, smtp)
    item = await svc.answer_reply(biz, profile, reply.id)
    assert item.kind == "reply" and item.step == 100 and item.status == "pending_review"
    assert item.subject == "Re: pedidos online" and OPT_OUT in item.body
    assert (await svc.answer_reply(biz, profile, reply.id)).id == item.id  # idempotent

    approved = await svc.decide(biz.id, profile, item.id, uuid.uuid4(), approve=True)
    assert approved.status == "approved"  # a reply draft is exactly for someone who replied
    sent = await svc.send_item(biz, profile, approved, await svc.require_account(biz.id))
    assert sent.status == "sent" and smtp[-1]["In-Reply-To"] == "<in10@c>"
    assert prospect.status == "replied"


@pytest.mark.asyncio
@pytest.mark.parametrize("classification", ["not_interested", "handoff"])
async def test_replies_that_need_a_person_get_no_answer_draft(db, monkeypatch, smtp, classification):
    svc, biz, profile, _, reply = await _replied(db, monkeypatch, smtp, classification, answer="x")
    with pytest.raises(HarveyError) as e:
        await svc.answer_reply(biz, profile, reply.id)
    assert e.value.status_code == 409


@pytest.mark.asyncio
async def test_answer_for_another_business_is_not_found(db, monkeypatch, smtp):
    svc, biz, profile, _, reply = await _replied(db, monkeypatch, smtp)
    with pytest.raises(HarveyError) as e:
        await svc.answer_reply(SimpleNamespace(id=uuid.uuid4()), profile, reply.id)
    assert e.value.status_code == 404


@pytest.mark.asyncio
async def test_reply_draft_to_someone_who_opted_out_is_refused(db, monkeypatch, smtp):
    svc, biz, profile, prospect, reply = await _replied(db, monkeypatch, smtp)
    prospect.status = "opted_out"
    await db.commit()
    with pytest.raises(HarveyError):
        await svc.answer_reply(biz, profile, reply.id)


# ── editing a draft ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_editing_reruns_the_gate_and_only_works_before_approval(db, monkeypatch):
    svc, biz, profile, prospect = await _setup(db)
    _fake_model(monkeypatch, {"subject": "pedidos", "body": "¿Cómo reciben pedidos?"})
    item = await svc.draft_step(biz, profile, prospect, 1)

    bad = await svc.edit_item(biz.id, profile, item.id, "pedidos", "Hola, sin línea de baja")
    assert bad.status == "blocked" and bad.gate_reasons
    good = await svc.edit_item(biz.id, profile, item.id, "pedidos", f"Hola Ana, ¿pedidos?\n{OPT_OUT}")
    assert good.status == "pending_review" and not good.gate_reasons

    await svc.decide(biz.id, profile, item.id, uuid.uuid4(), approve=True)
    with pytest.raises(HarveyError) as e:
        await svc.edit_item(biz.id, profile, item.id, "x", "y")
    assert e.value.status_code == 409


# ── the automatic loop ────────────────────────────────────────────────────
class _Counter:
    def __init__(self, monkeypatch, payload):
        self.calls = 0

        async def fake(system, prompt, **kw):
            self.calls += 1
            return payload

        monkeypatch.setattr(harvey_service, "ask_json", fake)
        monkeypatch.setattr(harvey_service, "llm_available", lambda: True)


@pytest.mark.asyncio
async def test_cycle_does_nothing_for_a_disabled_business(db):
    svc, biz, profile, _ = await _setup(db, is_enabled=False)
    assert await svc.run_cycle(biz, profile, TUE_10AM) == {"skipped": "desactivado"}
    assert profile.last_cycle_at is None


@pytest.mark.asyncio
async def test_cycle_without_a_mailbox_is_recorded_not_raised(db):
    svc, biz, profile, _ = await _setup(db)
    result = await svc.run_cycle(biz, profile, TUE_10AM)
    assert "canal de email" in result["skipped"] and profile.last_cycle == result


@pytest.mark.asyncio
async def test_cycle_sends_approved_mail_only_inside_the_window(db, monkeypatch, smtp):
    svc, biz, profile, prospect = await _setup(db)
    await _connect_mailbox(db, biz)
    _fake_inbox(monkeypatch, [])
    await _approved(monkeypatch, svc, biz, profile, prospect)

    outside = await svc.run_cycle(biz, profile, SATURDAY)
    assert outside["send"] == "fuera de la ventana de envío" and smtp == []
    inside = await svc.run_cycle(biz, profile, TUE_10AM)
    assert inside["send"]["sent"] == 1 and len(smtp) == 1
    assert profile.last_cycle_at == TUE_10AM and profile.last_cycle["send"]["sent"] == 1


@pytest.mark.asyncio
async def test_one_run_sends_a_few_not_the_whole_queue(db, monkeypatch, smtp):
    svc, biz, profile, prospect = await _setup(db, max_daily_sends=50)
    await _connect_mailbox(db, biz)
    _fake_inbox(monkeypatch, [])
    profile.warmup_started_at = TUE_10AM - timedelta(days=30)
    others, _ = await svc.add_prospects(biz.id, profile, [{"email": f"p{i}@c{i}.com"} for i in range(4)])
    for p in [prospect, *others]:
        await _approved(monkeypatch, svc, biz, profile, p)
    result = await svc.run_cycle(biz, profile, TUE_10AM)
    assert result["send"]["sent"] == harvey_service.AUTO_SENDS_PER_RUN == len(smtp)


@pytest.mark.asyncio
async def test_a_failing_inbox_does_not_stop_the_sends(db, monkeypatch, smtp):
    svc, biz, profile, prospect = await _setup(db)
    await _connect_mailbox(db, biz)
    await _approved(monkeypatch, svc, biz, profile, prospect)

    async def boom(*a, **kw):
        raise OSError("imap down")

    monkeypatch.setattr(harvey_service.mailer, "fetch_new", boom)
    first = await svc.run_cycle(biz, profile, TUE_10AM)  # nothing sent yet: inbox not even opened
    assert first["send"]["sent"] == 1
    second = await svc.run_cycle(biz, profile, TUE_10AM)  # now there is something to read, and it fails
    assert "inbox_error" in second and "send" in second


@pytest.mark.asyncio
async def test_drafting_is_opt_in_and_always_waits_for_approval(db, monkeypatch, smtp):
    svc, biz, profile, prospect = await _setup(db)
    await _connect_mailbox(db, biz)
    _fake_inbox(monkeypatch, [])
    model = _Counter(monkeypatch, {"subject": "pedidos", "body": "¿Cómo reciben pedidos?"})
    await svc.add_prospects(biz.id, profile, [{"email": "x@y.com", "email_status": "scraped"}])

    await svc.run_cycle(biz, profile, TUE_10AM)
    assert model.calls == 0  # auto_draft is off: no credits spent

    profile = await svc.update_profile(biz, {"auto_draft": True})
    result = await svc.run_cycle(biz, profile, TUE_10AM)
    assert result["first_emails"]["drafted"] == 1 and model.calls == 1  # the scraped one is skipped
    assert smtp == []  # drafted, not sent: a person still approves
    assert [i.status for i in await svc.list_outbox(biz.id)] == ["pending_review"]


@pytest.mark.asyncio
async def test_cycle_stages_the_answer_to_a_reply_when_drafting_is_on(db, monkeypatch, smtp):
    svc, biz, profile, _, reply = await _replied(db, monkeypatch, smtp)
    profile = await svc.update_profile(biz, {"auto_draft": True})
    _fake_inbox(monkeypatch, [])
    result = await svc.run_cycle(biz, profile, TUE_10AM)
    assert result["replies_staged"] == 1
    again = await svc.run_cycle(biz, profile, TUE_10AM)
    assert again["replies_staged"] == 0


@pytest.mark.asyncio
async def test_status_reports_readiness_and_queues(db, monkeypatch, smtp):
    svc, biz, profile, prospect = await _setup(db)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    st = await svc.status(biz, profile)
    assert st["email_connected"] is False and st["search_available"] is False
    assert st["prospects"] == {"new": 1} and st["send_cap_today"] == 5  # warming up
    await _connect_mailbox(db, biz)
    assert (await svc.status(biz, profile))["email_connected"] is True


# ── HTTP layer: response models and routes for the new endpoints ──────────
@pytest.mark.asyncio
async def test_http_endpoints_serialize_and_enforce_the_flow(db, monkeypatch, smtp):
    from fastapi import FastAPI

    from app.core.database import get_db
    from app.core.deps import get_current_user
    from app.domains.harvey import router as router_mod

    svc, biz, profile, prospect, reply = await _replied(db, monkeypatch, smtp)
    user = SimpleNamespace(id=uuid.uuid4())

    async def fake_access(_db, business_id, _user, manage=False):
        assert business_id == biz.id
        return biz

    async def fake_db():
        yield db

    monkeypatch.setattr(router_mod, "require_business_access", fake_access)
    app = FastAPI()
    app.include_router(router_mod.router, prefix="/api/v1/businesses")
    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_user] = lambda: user
    base = f"/api/v1/businesses/{biz.id}/harvey"

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        st = (await c.get(f"{base}/status")).json()
        assert st["email_connected"] is True and st["replies"] == 1 and st["prospects"] == {"replied": 1}

        prof = (await c.patch(f"{base}/profile", json={"auto_draft": True, "send_window_end": 20})).json()
        assert prof["auto_draft"] is True and prof["send_window_end"] == 20 and prof["last_cycle"] == {}
        bad = await c.patch(f"{base}/profile", json={"send_window_start": 20, "send_window_end": 10})
        assert bad.status_code == 422

        staged = await c.post(f"{base}/replies/{reply.id}/answer")
        assert staged.status_code == 201 and staged.json()["kind"] == "reply" and staged.json()["reply_id"] == str(reply.id)
        item_id = staged.json()["id"]

        edited = await c.patch(f"{base}/outbox/{item_id}", json={"subject": "Re: pedidos", "body": "sin baja"})
        assert edited.status_code == 200 and edited.json()["status"] == "blocked"
        no_such = await c.patch(f"{base}/outbox/{uuid.uuid4()}", json={"subject": "x", "body": "y"})
        assert no_such.status_code == 404

        verified = await c.post(f"{base}/prospects/verify", json={"prospect_ids": [str(prospect.id)], "verified": True})
        assert verified.json() == {"counts": {"updated": 0}}  # a "provided" address is not touched

        nothing = await c.post(f"{base}/prospects/discover", json={"urls": [], "queries": []})
        assert nothing.status_code == 422  # no urls and no keywords in the ideal customer
        listed = (await c.get(f"{base}/prospects")).json()
        assert listed[0]["source"] == "manual" and listed[0]["source_url"] == ""
