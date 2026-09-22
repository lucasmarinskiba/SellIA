"""Mercado Libre webhook: authentication, payload validation and idempotent ingestion.

Real SQLite tables (channel_connections, publication_links, conversion_events);
Mercado Libre's API is faked, but only inside the modules under test, so the
in-process ASGI client used to hit the endpoint keeps working.
"""

import json
import os
import uuid
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from fastapi import FastAPI
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

import app.domains.seo_config.mercadolibre_webhook_service as ml  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.domains.channels.models import ChannelConnection, ChannelPlatform  # noqa: E402
from app.domains.seo_config.fomo_models import ConversionEvent  # noqa: E402
from app.domains.seo_config.models import PublicationLink  # noqa: E402
from app.domains.seo_config.router import public_router  # noqa: E402

SELLER = "555"
TOKEN = "s3cret-callback-token-for-tests-0123456789abcdefghij"


# ── Fake Mercado Libre API ──

class FakeResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self._body = body if body is not None else {}

    def json(self):
        return self._body


def install_fake_ml(monkeypatch, handler):
    """handler(method, url, kwargs) -> FakeResponse. Patches only the modules under test."""
    calls = []

    class FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, **kw):
            calls.append(("GET", url, kw))
            return handler("GET", url, kw)

        async def post(self, url, **kw):
            calls.append(("POST", url, kw))
            return handler("POST", url, kw)

    shim = SimpleNamespace(AsyncClient=FakeClient, HTTPError=httpx.HTTPError)
    monkeypatch.setattr(ml, "httpx", shim)
    import app.core.oauth_connectors as oauth

    monkeypatch.setattr(oauth, "httpx", shim)
    return calls


def order(status="paid", seller=int(SELLER), items=(("MLA111", 2, 50.0),)):
    return {
        "id": 9001, "status": status, "seller": {"id": seller},
        "order_items": [{"item": {"id": i}, "quantity": q, "unit_price": p} for i, q, p in items],
    }


def serves(body, status=200):
    return lambda method, url, kw: FakeResponse(status, body)


# ── DB fixture ──

@pytest_asyncio.fixture
async def env():
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async with engine.begin() as conn:
        for t in (ChannelConnection.__table__, PublicationLink.__table__, ConversionEvent.__table__):
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        yield SimpleNamespace(db=db, Session=Session)
    await engine.dispose()


async def make_channel(db, business_id, *, token=TOKEN, seller=SELLER, active=True,
                       platform=ChannelPlatform.MERCADOLIBRE, credentials=None):
    creds = {"access_token": "at-1", "refresh_token": "rt-1"}
    if seller is not None:
        creds["seller_id"] = seller
    creds.update(credentials or {})
    channel = ChannelConnection(
        business_id=business_id, platform=platform, name="ML", credentials=creds,
        webhook_token=token, is_active=active,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


async def make_link(db, business_id, url="https://articulo.mercadolibre.com.ar/MLA-111-zapatillas_JM"):
    link = PublicationLink(
        business_id=business_id, url=url, title="Zapatillas", platform_source="mercado-libre"
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def conversions(db):
    return (await db.execute(select(ConversionEvent))).scalars().all()


# ── Authentication ──

async def test_authenticate_accepts_only_the_right_token_for_this_business(env):
    biz, other = uuid4(), uuid4()
    channel = await make_channel(env.db, biz)
    assert (await ml.authenticate_channel(env.db, biz, TOKEN)).id == channel.id
    assert await ml.authenticate_channel(env.db, biz, "wrong") is None
    assert await ml.authenticate_channel(env.db, biz, None) is None
    assert await ml.authenticate_channel(env.db, biz, "") is None
    assert await ml.authenticate_channel(env.db, other, TOKEN) is None  # right token, wrong business


async def test_authenticate_rejects_inactive_and_non_ml_channels(env):
    biz = uuid4()
    await make_channel(env.db, biz, token="inactive-token", active=False)
    await make_channel(env.db, biz, token="whatsapp-token", platform=ChannelPlatform.WHATSAPP)
    assert await ml.authenticate_channel(env.db, biz, "inactive-token") is None
    assert await ml.authenticate_channel(env.db, biz, "whatsapp-token") is None


async def test_authenticate_tolerates_non_ascii_token(env):
    biz = uuid4()
    await make_channel(env.db, biz)
    assert await ml.authenticate_channel(env.db, biz, "tóken-ñandú") is None


# ── Payload validation ──

def _channel(seller=SELLER):
    return SimpleNamespace(credentials={"seller_id": seller} if seller else {})


def test_non_order_topics_are_ignored_not_rejected():
    for topic in ("questions", "messages", "items", "payments"):
        assert ml.parse_notification({"topic": topic, "resource": "/questions/1", "user_id": 555}, _channel()) is None


def test_order_notification_is_parsed():
    n = ml.parse_notification({"topic": "orders_v2", "resource": "/orders/9001", "user_id": 555}, _channel())
    assert n == ml.OrderNotification(order_id="9001", seller_id=SELLER)


@pytest.mark.parametrize("resource", [
    "https://evil.example/orders/1", "/orders/1/../../users/me", "/orders/abc", "/orders/", "/users/1",
    "//evil.example/orders/1", "/orders/1?x=1", "",
])
def test_resource_must_be_exactly_an_order_path(resource):
    with pytest.raises(ml.NotificationRejected) as e:
        ml.parse_notification({"topic": "orders_v2", "resource": resource, "user_id": 555}, _channel())
    assert e.value.status_code == 400


def test_notification_for_another_seller_is_forbidden():
    with pytest.raises(ml.NotificationRejected) as e:
        ml.parse_notification({"topic": "orders_v2", "resource": "/orders/1", "user_id": 999}, _channel())
    assert e.value.status_code == 403


def test_channel_without_seller_id_cannot_bind_a_notification():
    with pytest.raises(ml.NotificationRejected) as e:
        ml.parse_notification({"topic": "orders_v2", "resource": "/orders/1", "user_id": 555}, _channel(seller=None))
    assert e.value.status_code == 403


def test_non_dict_payload_is_rejected():
    for bad in (None, [], "x", 5):
        with pytest.raises(ml.NotificationRejected):
            ml.parse_notification(bad, _channel())


# ── Matching an order item to a tracked link ──

@pytest.mark.parametrize("url", [
    "https://articulo.mercadolibre.com.ar/MLA-1234567890-zapatillas-nike-_JM",  # listing permalink, hyphenated
    "https://www.mercadolibre.com.ar/zapatillas/p/MLA1234567890",  # catalog page, no hyphen
    "https://articulo.mercadolibre.com.ar/mla-1234567890-zapatillas-_JM?x=1",  # lower case + query
])
def test_url_matches_item_in_every_real_spelling(url):
    assert ml.url_matches_item(url, "MLA1234567890")


@pytest.mark.parametrize("url", [
    "https://articulo.mercadolibre.com.ar/MLA-12345678901-otro",  # longer id that merely contains ours
    "https://articulo.mercadolibre.com.ar/MLA-123456789-otro",  # shorter id
    "https://example.com/XMLA1234567890",  # id glued to other letters
    "https://articulo.mercadolibre.com.ar/MLB-1234567890-otro-sitio",  # same digits, different site
])
def test_url_does_not_match_a_different_item(url):
    assert not ml.url_matches_item(url, "MLA1234567890")


# ── Order verification + ingestion ──

async def test_paid_order_for_tracked_item_is_recorded_once(env, monkeypatch):
    biz = uuid4()
    channel = await make_channel(env.db, biz)
    link = await make_link(env.db, biz)
    calls = install_fake_ml(monkeypatch, serves(order()))

    first = await ml.process_order_notification(env.db, channel.id, "9001")
    assert first == {"status": "recorded", "conversions": 1}

    events = await conversions(env.db)
    assert len(events) == 1
    e = events[0]
    assert (e.business_id, e.link_id, e.platform_name) == (biz, link.id, "mercado-libre")
    assert e.conversion_value == 100.0  # 2 x 50
    assert e.external_listing_id == "MLA111"
    assert e.raw_event_data["order_id"] == "9001" and e.raw_event_data["verified"] is True

    # ML retries and re-notifies on every change to the order: must not double count.
    again = await ml.process_order_notification(env.db, channel.id, "9001")
    assert again["status"] == "ignored"
    assert len(await conversions(env.db)) == 1

    # Only ever talked to ML's order endpoint, using the seller's own token.
    assert {c[1] for c in calls} == {"https://api.mercadolibre.com/orders/9001"}
    assert calls[0][2]["headers"]["Authorization"] == "Bearer at-1"


async def test_order_for_untracked_item_records_nothing(env, monkeypatch):
    biz = uuid4()
    channel = await make_channel(env.db, biz)
    await make_link(env.db, biz)
    install_fake_ml(monkeypatch, serves(order(items=(("MLA999", 1, 10.0),))))
    result = await ml.process_order_notification(env.db, channel.id, "9001")
    assert result["status"] == "ignored" and await conversions(env.db) == []


async def test_link_of_another_business_is_never_credited(env, monkeypatch):
    biz, other = uuid4(), uuid4()
    channel = await make_channel(env.db, biz)
    await make_link(env.db, other)  # same item URL, different business
    install_fake_ml(monkeypatch, serves(order()))
    assert (await ml.process_order_notification(env.db, channel.id, "9001"))["status"] == "ignored"
    assert await conversions(env.db) == []


async def test_unpaid_order_is_not_a_conversion_yet(env, monkeypatch):
    biz = uuid4()
    channel = await make_channel(env.db, biz)
    await make_link(env.db, biz)
    install_fake_ml(monkeypatch, serves(order(status="payment_required")))
    result = await ml.process_order_notification(env.db, channel.id, "9001")
    assert result["status"] == "ignored" and await conversions(env.db) == []


async def test_order_of_a_different_seller_is_rejected(env, monkeypatch):
    biz = uuid4()
    channel = await make_channel(env.db, biz)
    await make_link(env.db, biz)
    install_fake_ml(monkeypatch, serves(order(seller=999)))
    with pytest.raises(ml.NotificationRejected) as e:
        await ml.process_order_notification(env.db, channel.id, "9001")
    assert e.value.status_code == 403 and await conversions(env.db) == []


@pytest.mark.parametrize("status", [404, 403])
async def test_order_ml_does_not_recognise_is_ignored(env, monkeypatch, status):
    biz = uuid4()
    channel = await make_channel(env.db, biz)
    await make_link(env.db, biz)
    install_fake_ml(monkeypatch, serves({}, status))
    assert (await ml.process_order_notification(env.db, channel.id, "9001"))["status"] == "ignored"
    assert await conversions(env.db) == []


async def test_ml_outage_is_reported_not_recorded(env, monkeypatch):
    biz = uuid4()
    channel = await make_channel(env.db, biz)
    await make_link(env.db, biz)
    install_fake_ml(monkeypatch, serves({}, 503))
    with pytest.raises(ml.MercadoLibreUnavailable):
        await ml.process_order_notification(env.db, channel.id, "9001")
    assert await conversions(env.db) == []


async def test_expired_token_is_refreshed_once_and_persisted(env, monkeypatch):
    biz = uuid4()
    channel = await make_channel(env.db, biz)
    await make_link(env.db, biz)

    def handler(method, url, kw):
        if method == "POST":  # oauth/token refresh
            return FakeResponse(200, {"access_token": "at-2", "refresh_token": "rt-2"})
        if kw["headers"]["Authorization"] == "Bearer at-2":
            return FakeResponse(200, order())
        return FakeResponse(401, {})

    install_fake_ml(monkeypatch, handler)
    result = await ml.process_order_notification(env.db, channel.id, "9001")
    assert result == {"status": "recorded", "conversions": 1}

    await env.db.refresh(channel)
    assert channel.credentials["access_token"] == "at-2" and channel.credentials["refresh_token"] == "rt-2"


async def test_dead_token_without_refresh_is_unavailable_not_a_verdict(env, monkeypatch):
    biz = uuid4()
    channel = await make_channel(env.db, biz, credentials={"refresh_token": None})
    channel.credentials["refresh_token"] = None
    await env.db.commit()
    await make_link(env.db, biz)
    install_fake_ml(monkeypatch, serves({}, 401))
    with pytest.raises(ml.MercadoLibreUnavailable):
        await ml.process_order_notification(env.db, channel.id, "9001")


# ── The HTTP endpoint ──

def build_client(env, monkeypatch):
    app = FastAPI()
    # The ML webhook lives on public_router (channel-token auth, no user
    # session) — kept off the main `router`, which now requires business
    # ownership via verify_business_access.
    app.include_router(public_router, prefix="/api/v1/businesses")

    async def override_db():
        yield env.db

    app.dependency_overrides[get_db] = override_db
    import app.core.database as database

    monkeypatch.setattr(database, "AsyncSessionLocal", env.Session)  # background task opens its own session
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def url(biz, token=TOKEN):
    base = f"/api/v1/businesses/{biz}/seo-config/webhooks/mercado-libre"
    return base if token is None else f"{base}?token={token}"


GOOD = {"topic": "orders_v2", "resource": "/orders/9001", "user_id": 555}


async def test_endpoint_requires_a_valid_token(env, monkeypatch):
    biz = uuid4()
    await make_channel(env.db, biz)
    async with build_client(env, monkeypatch) as client:
        assert (await client.post(url(biz, None), json=GOOD)).status_code == 401
        assert (await client.post(url(biz, "nope"), json=GOOD)).status_code == 401
        assert (await client.post(url(uuid4()), json=GOOD)).status_code == 401  # unknown business: same answer
    assert await conversions(env.db) == []


async def test_endpoint_rejects_bad_payloads_after_auth(env, monkeypatch):
    biz = uuid4()
    await make_channel(env.db, biz)
    async with build_client(env, monkeypatch) as client:
        assert (await client.post(url(biz), content=b"not json")).status_code == 400
        assert (await client.post(url(biz), json={**GOOD, "resource": "https://evil.example/x"})).status_code == 400
        assert (await client.post(url(biz), json={**GOOD, "user_id": 999})).status_code == 403
        ignored = await client.post(url(biz), json={"topic": "questions", "resource": "/questions/1", "user_id": 555})
        assert ignored.status_code == 200 and ignored.json() == {"received": True, "ignored": True}


async def test_endpoint_acknowledges_and_records_a_verified_sale(env, monkeypatch):
    biz = uuid4()
    await make_channel(env.db, biz)
    link = await make_link(env.db, biz)
    install_fake_ml(monkeypatch, serves(order()))
    async with build_client(env, monkeypatch) as client:
        resp = await client.post(url(biz), json=GOOD)
    assert resp.status_code == 200 and resp.json() == {"received": True}

    events = await conversions(env.db)
    assert len(events) == 1 and events[0].link_id == link.id and events[0].conversion_value == 100.0


async def test_authenticated_but_forged_order_records_nothing(env, monkeypatch):
    """Even holding the token, a notification for an order ML doesn't know can't create a conversion."""
    biz = uuid4()
    await make_channel(env.db, biz)
    await make_link(env.db, biz)
    install_fake_ml(monkeypatch, serves({}, 404))
    async with build_client(env, monkeypatch) as client:
        resp = await client.post(url(biz), json=GOOD)
    assert resp.status_code == 200
    assert await conversions(env.db) == []


# ── extract_listing_id (platform sync) ───────────────────────────────────────

import pytest as _pytest


@_pytest.mark.parametrize(
    "url,expected",
    [
        ("https://articulo.mercadolibre.com.ar/MLA-1234567890-zapatillas-_JM", "MLA1234567890"),
        ("https://www.mercadolibre.com.ar/p/MLA1234567890", "MLA1234567890"),
        ("https://www.mercadolibre.com.mx/items/MLM123456789", "MLM123456789"),
        ("https://example.com/HTML5-guide", None),
        ("https://example.com/sin-id", None),
    ],
)
async def test_extract_listing_id_handles_hyphenated_permalinks(url, expected):
    from app.domains.seo_config.platform_sync_mercadolibre import MercadoLibreListingSync

    connector = MercadoLibreListingSync.__new__(MercadoLibreListingSync)
    assert await connector.extract_listing_id(url) == expected
