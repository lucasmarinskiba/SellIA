"""SellIA -> feedIA sales feed (app/domains/feedia_link).

Three things have to hold for the feed to be worth having:
  * feedIA accepts what we send: the signature is byte-identical to what feedIA's own code computes (the REF_ values
    were produced by running ``createHmac('sha256', secret).update(JSON.stringify({eventType, event}))`` in Node);
  * no sale is lost or counted twice: the outbox row is written with the order change, whichever code moved the order,
    and a failure in the feed can never break the order write;
  * a customer's real address never leaves SellIA, and only the business's own people can connect or read the link.

SQLite, no network: JSONB / UUID rendered for SQLite and delivery goes through an injected fake poster.
"""

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event, select, text
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.deps import get_current_active_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.feedia_link import capture, delivery, router as feedia_router, signing
from app.domains.feedia_link.models import FeediaLink, FeediaOutbox
from app.domains.orders.models import Order, OrderStatus

SECRET = "compat-webhook-secret-0123456789abcdef"

# Produced in Node with feedIA's algorithm (see the module docstring).
REF_SALE_EVENT = {
    "orderId": "ord-1",
    "totalAmount": "1499.90",
    "timestamp": "2026-10-01T15:30:00+00:00",
    "customerEmail": "ab12@customers.sellia.invalid",
    "sourcePostId": "",
}
REF_SALE_BODY = (
    '{"eventType":"sale","event":{"orderId":"ord-1","totalAmount":"1499.90","timestamp":"2026-10-01T15:30:00+00:00",'
    '"customerEmail":"ab12@customers.sellia.invalid","sourcePostId":""}}'
)
REF_SALE_SIG = "d63d09ce187cf145267a82a6b18431832349fbcebb02fde6f6e26293ee7f9dc9"
REF_REFUND_EVENT = {"orderId": "ord-ñ-é"}
REF_REFUND_BODY = '{"eventType":"refund","event":{"orderId":"ord-ñ-é"}}'
REF_REFUND_SIG = "4dd4620cdb2b7fefab3c63d2cd26db2830cc04c037ac65c4df6abeca4cd9c3d5"
FEEDIA_EMAIL_SHAPE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")  # feedIA ledger.ts normalizeOrder


# ── wire format ─────────────────────────────────────────────────────────────


def test_canonical_json_matches_javascript_stringify():
    assert signing.canonical_json("sale", REF_SALE_EVENT) == REF_SALE_BODY
    assert signing.canonical_json("refund", REF_REFUND_EVENT) == REF_REFUND_BODY  # non-ASCII is not escaped


def test_signature_matches_the_one_feedia_computes():
    assert signing.sign_event("sale", REF_SALE_EVENT, SECRET) == REF_SALE_SIG
    assert signing.sign_event("refund", REF_REFUND_EVENT, SECRET) == REF_REFUND_SIG


@pytest.mark.parametrize("bad", [{"a": 49.0}, {"a": True}, {"a": None}, {"a": Decimal("1")}, {"a": {"b": 1.5}}, {"a": [0.1]}])
def test_values_that_javascript_would_print_differently_are_refused(bad):
    with pytest.raises(ValueError):
        signing.canonical_json("sale", bad)


def test_sale_event_sends_amount_and_date_as_strings():
    ev = signing.sale_event(
        order_id=uuid.UUID(int=7), total=Decimal("1499.9"), when=datetime(2026, 10, 1, 12, 30, tzinfo=timezone(timedelta(hours=-3))),
        business_id="b", email="Ana@Example.com", key="k",
    )
    assert ev["totalAmount"] == "1499.90" and ev["timestamp"] == "2026-10-01T15:30:00+00:00"
    signing.canonical_json("sale", ev)  # nothing feedIA would reject


def test_customer_email_never_leaves_sellia():
    a = signing.pseudonymous_email("biz-1", "Ana@Example.com", "k")
    assert "example.com" not in a and "ana" not in a.lower()
    assert FEEDIA_EMAIL_SHAPE.match(a), "feedIA drops anything that does not look like an email"
    assert a == signing.pseudonymous_email("biz-1", " ana@example.COM ", "k")  # same customer, same id
    assert a != signing.pseudonymous_email("biz-2", "ana@example.com", "k")  # unlinkable across businesses
    assert a != signing.pseudonymous_email("biz-1", "ana@example.com", "other-key")
    assert signing.pseudonymous_email("biz-1", None, "k") == ""


@pytest.mark.parametrize("ok", ["abc", "a-b_c", "u" * 64])
def test_account_id_rule_matches_feedia(ok):
    assert signing.ACCOUNT_ID.match(ok)


@pytest.mark.parametrize("bad", ["", "../etc", "a b", "a/b", "u" * 65, "a.json"])
def test_unsafe_account_ids_are_refused(bad):
    assert not signing.ACCOUNT_ID.match(bad)


@pytest.mark.parametrize("prev,new,expected", [
    (None, OrderStatus.PENDING, None),
    (None, OrderStatus.PAID, "sale"),  # created already paid
    (OrderStatus.PENDING, OrderStatus.PAID, "sale"),
    (OrderStatus.PAID, OrderStatus.SHIPPED, None),  # still the same sale
    (OrderStatus.SHIPPED, OrderStatus.DELIVERED, None),
    (OrderStatus.PENDING, OrderStatus.DELIVERED, "sale"),  # a marketplace can jump straight to delivered
    (OrderStatus.PAID, OrderStatus.REFUNDED, "refund"),
    (OrderStatus.DELIVERED, OrderStatus.CANCELLED, "refund"),
    (OrderStatus.PENDING, OrderStatus.CANCELLED, None),  # never counted, nothing to reverse
    (OrderStatus.PENDING, OrderStatus.REFUNDED, None),
    ("OrderStatus.PAID", "refunded", "refund"),  # raw values from webhooks
])
def test_which_status_moves_become_events(prev, new, expected):
    assert capture.event_for_transition(prev, new) == expected


# ── database ────────────────────────────────────────────────────────────────


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


@compiles(sqltypes.UUID, "sqlite")
def _uuid_as_char(type_, compiler, **kw):
    return "CHAR(32)"


def _make_aware(target, *_args) -> None:
    for key, value in list(target.__dict__.items()):
        if isinstance(value, datetime) and value.tzinfo is None:
            target.__dict__[key] = value.replace(tzinfo=timezone.utc)


event.listen(Base, "load", _make_aware, propagate=True)
event.listen(Base, "refresh", _make_aware, propagate=True)

MODELS = [Business, BusinessMember, Order, FeediaLink, FeediaOutbox]
USERS = {n: SimpleNamespace(id=uuid.uuid4(), email=f"{n.lower()}@example.com")
         for n in ("OWNER", "ADMIN", "MEMBER", "STRANGER")}


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def world(factory):
    async with factory() as s:
        biz = Business(user_id=USERS["OWNER"].id, name="A")
        other = Business(user_id=USERS["STRANGER"].id, name="B")
        s.add_all([biz, other])
        await s.flush()
        s.add_all([
            BusinessMember(business_id=biz.id, user_id=USERS["ADMIN"].id, role=BusinessMemberRole.ADMIN, is_active=True),
            BusinessMember(business_id=biz.id, user_id=USERS["MEMBER"].id, role=BusinessMemberRole.MEMBER, is_active=True),
        ])
        await s.commit()
        return {"biz": biz.id, "other": other.id}


async def _link(factory, business_id, account="acct-1", enabled=True):
    async with factory() as s:
        s.add(FeediaLink(business_id=business_id, feedia_account_id=account, enabled=enabled))
        await s.commit()


async def _outbox(factory):
    async with factory() as s:
        return (await s.execute(select(FeediaOutbox).order_by(FeediaOutbox.created_at))).scalars().all()


async def _order(factory, business_id, status=OrderStatus.PENDING, amount="1499.90", email="ana@example.com"):
    async with factory() as s:
        o = Order(business_id=business_id, total_amount=Decimal(amount), status=status, customer_email=email)
        s.add(o)
        await s.commit()
        return o.id


async def _move(factory, order_id, status):
    async with factory() as s:
        o = await s.get(Order, order_id)
        o.status = status
        await s.commit()


async def test_paying_a_linked_order_queues_exactly_one_sale(factory, world):
    await _link(factory, world["biz"])
    oid = await _order(factory, world["biz"])
    assert await _outbox(factory) == []  # a pending order is not a sale
    await _move(factory, oid, OrderStatus.PAID)
    await _move(factory, oid, OrderStatus.SHIPPED)
    await _move(factory, oid, OrderStatus.DELIVERED)
    rows = await _outbox(factory)
    assert [(r.event_type, r.order_id, r.status) for r in rows] == [("sale", str(oid), "pending")]
    p = rows[0].payload
    assert p["totalAmount"] == "1499.90" and p["orderId"] == str(oid)
    assert "example.com" not in json.dumps(p) and p["customerEmail"].endswith("@customers.sellia.invalid")


async def test_an_order_created_already_paid_is_a_sale(factory, world):
    await _link(factory, world["biz"])
    await _order(factory, world["biz"], status=OrderStatus.PAID)
    assert [r.event_type for r in await _outbox(factory)] == ["sale"]


async def test_refund_after_sale_queues_a_refund(factory, world):
    await _link(factory, world["biz"])
    oid = await _order(factory, world["biz"], status=OrderStatus.PAID)
    await _move(factory, oid, OrderStatus.REFUNDED)
    assert sorted(r.event_type for r in await _outbox(factory)) == ["refund", "sale"]


async def test_unlinked_or_disabled_business_queues_nothing(factory, world):
    await _order(factory, world["biz"], status=OrderStatus.PAID)  # not linked
    await _link(factory, world["other"], enabled=False)
    await _order(factory, world["other"], status=OrderStatus.PAID)  # linked but switched off
    assert await _outbox(factory) == []


async def test_orders_of_another_business_are_never_queued_under_this_link(factory, world):
    await _link(factory, world["biz"])
    await _order(factory, world["other"], status=OrderStatus.PAID)
    assert await _outbox(factory) == []


async def test_a_broken_feed_cannot_break_an_order_write(factory, world):
    """The feed is best effort: if its table is gone, the order must still be saved."""
    await _link(factory, world["biz"])
    async with factory() as s:
        await s.execute(text("DROP TABLE feedia_outbox"))
        await s.commit()
    oid = await _order(factory, world["biz"], status=OrderStatus.PAID)
    async with factory() as s:
        assert (await s.get(Order, oid)).status == OrderStatus.PAID


# ── delivery ────────────────────────────────────────────────────────────────


class FakeFeedia:
    def __init__(self, status=200, data=None):
        self.status, self.data, self.calls = status, {"ok": True} if data is None else data, []

    async def __call__(self, url, body, headers):
        self.calls.append((url, body, headers))
        return self.status, self.data


async def _queue_sale(factory, world, order_status=OrderStatus.PAID):
    await _link(factory, world["biz"], account="acct-9")
    oid = await _order(factory, world["biz"], status=order_status)
    return oid


async def _deliver(factory, fake, now=None, base="https://feedia.example", secret=SECRET):
    async with factory() as s:
        return await delivery.deliver_due(s, base_url=base, secret=secret, post=fake, now=now)


async def test_delivery_posts_the_signed_event_to_the_webhook(factory, world):
    oid = await _queue_sale(factory, world)
    fake = FakeFeedia()
    stats = await _deliver(factory, fake)
    assert stats["sent"] == 1
    (url, body, headers), = fake.calls
    assert url == "https://feedia.example/api/sellia/webhook"
    sent = json.loads(body)
    assert sent["accountId"] == "acct-9" and sent["eventType"] == "sale" and sent["event"]["orderId"] == str(oid)
    # feedIA recomputes the signature from the parsed {eventType, event}; it must match what we signed.
    assert sent["signature"] == headers["X-Sellia-Signature"]
    assert sent["signature"] == signing.sign_event(sent["eventType"], sent["event"], SECRET)
    assert (await _outbox(factory))[0].status == "sent"


async def test_delivery_is_a_no_op_until_feedia_is_configured(factory, world):
    await _queue_sale(factory, world)
    for base, secret in ((None, SECRET), ("https://feedia.example", None), ("http://insecure.example", SECRET), ("", "")):
        fake = FakeFeedia()
        assert (await _deliver(factory, fake, base=base, secret=secret))["not_configured"] == 1
        assert fake.calls == []
    assert (await _outbox(factory))[0].status == "pending"  # waits, is not lost


@pytest.mark.parametrize("status,data", [(503, {"ok": False, "error": "webhook-not-configured"}), (401, {"ok": False, "error": "invalid-signature"}),
                                          (500, None), (0, None)])
async def test_server_side_and_secret_problems_are_retried_with_backoff(factory, world, status, data):
    await _queue_sale(factory, world)
    now = datetime.now(timezone.utc) + timedelta(minutes=1)  # the event was queued a moment ago
    stats = await _deliver(factory, FakeFeedia(status, data), now=now)
    assert stats["retry"] == 1
    row = (await _outbox(factory))[0]
    assert row.status == "pending" and row.attempts == 1 and row.next_attempt_at.replace(tzinfo=timezone.utc) == now + timedelta(minutes=1)
    # not due yet -> not sent again
    fake = FakeFeedia()
    await _deliver(factory, fake, now=now + timedelta(seconds=30))
    assert fake.calls == []
    # due -> delivered once the other side is fixed
    assert (await _deliver(factory, fake, now=now + timedelta(minutes=2)))["sent"] == 1


async def test_a_wrong_account_id_fails_for_good_and_tells_the_owner(factory, world):
    await _queue_sale(factory, world)
    stats = await _deliver(factory, FakeFeedia(404, {"ok": False, "error": "unknown-account"}))
    assert stats["failed"] == 1
    assert (await _outbox(factory))[0].status == "failed"
    async with factory() as s:
        assert "feedIA" in (await s.get(FeediaLink, world["biz"])).last_error


async def test_data_feedia_refuses_is_not_retried(factory, world):
    await _queue_sale(factory, world)
    assert (await _deliver(factory, FakeFeedia(200, {"ok": False, "error": "invalid-order-data"})))["failed"] == 1


async def test_gives_up_after_the_maximum_attempts(factory, world):
    await _queue_sale(factory, world)
    now = datetime.now(timezone.utc)
    for i in range(delivery.MAX_ATTEMPTS):
        now += timedelta(days=1)
        await _deliver(factory, FakeFeedia(500, None), now=now)
    row = (await _outbox(factory))[0]
    assert row.status == "failed" and row.attempts == delivery.MAX_ATTEMPTS


def test_backoff_doubles_and_is_capped():
    assert [delivery.backoff(n).total_seconds() for n in (1, 2, 3)] == [60, 120, 240]
    assert delivery.backoff(30).total_seconds() == 6 * 3600


async def test_events_of_an_unlinked_business_are_skipped_not_sent(factory, world):
    await _queue_sale(factory, world)
    async with factory() as s:
        await s.delete(await s.get(FeediaLink, world["biz"]))
        await s.commit()
    fake = FakeFeedia()
    assert (await _deliver(factory, fake))["skipped"] == 1 and fake.calls == []


# ── owner controls ──────────────────────────────────────────────────────────


def _app(factory, who):
    app = FastAPI()
    app.include_router(feedia_router.router, prefix="/api/v1/feedia")

    async def _db():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_db] = _db
    if who:
        app.dependency_overrides[get_current_active_user] = lambda: USERS[who]
    return app


def _client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://t")


async def _call(factory, who, method, path, biz, **kw):
    async with _client(_app(factory, who)) as c:
        return await c.request(method, f"/api/v1/feedia{path}", params={"business_id": str(biz), **kw.pop("params", {})}, **kw)


async def test_only_the_businesss_people_can_see_or_change_the_link(factory, world):
    biz = world["biz"]
    assert (await _call(factory, "STRANGER", "GET", "/link", biz)).status_code == 403
    assert (await _call(factory, None, "GET", "/link", biz)).status_code in (401, 403)
    for who in ("STRANGER", "MEMBER"):  # a plain member can look, not change
        assert (await _call(factory, who, "PUT", "/link", biz, json={"account_id": "x"})).status_code == 403
    assert (await _call(factory, "MEMBER", "GET", "/link", biz)).status_code == 200
    r = await _call(factory, "OWNER", "PUT", "/link", biz, json={"account_id": "acct-1"})
    assert r.status_code == 200 and r.json()["linked"] and r.json()["account_id"] == "acct-1"
    assert (await _call(factory, "ADMIN", "DELETE", "/link", biz)).status_code == 204
    assert (await _call(factory, "OWNER", "GET", "/link", biz)).json()["linked"] is False


@pytest.mark.parametrize("bad", ["", "../x", "a b", "u" * 65])
async def test_an_invalid_account_id_is_rejected(factory, world, bad):
    assert (await _call(factory, "OWNER", "PUT", "/link", world["biz"], json={"account_id": bad})).status_code == 422


async def test_fixing_the_account_id_gives_failed_events_a_second_chance(factory, world):
    await _queue_sale(factory, world)
    await _deliver(factory, FakeFeedia(404, {"ok": False, "error": "unknown-account"}))
    r = await _call(factory, "OWNER", "PUT", "/link", world["biz"], json={"account_id": "right-one"})
    assert r.json()["pending"] == 1 and r.json()["failed"] == 0 and r.json()["link_error"] is None


async def test_backfill_queues_past_sales_once(factory, world):
    biz = world["biz"]
    await _order(factory, biz, status=OrderStatus.PAID)  # before linking: not queued by capture
    await _order(factory, biz, status=OrderStatus.PENDING)
    assert (await _call(factory, "OWNER", "POST", "/backfill", biz)).status_code == 409  # not linked yet
    await _call(factory, "OWNER", "PUT", "/link", biz, json={"account_id": "acct-1"})
    r = await _call(factory, "OWNER", "POST", "/backfill", biz)
    assert r.json()["queued"] == 1
    again = await _call(factory, "OWNER", "POST", "/backfill", biz)
    assert again.json()["queued"] == 0 and again.json()["already_queued"] == 1
    assert len(await _outbox(factory)) == 1
    assert (await _call(factory, "MEMBER", "POST", "/backfill", biz)).status_code == 403


async def test_backfill_never_reads_another_businesss_orders(factory, world):
    await _order(factory, world["other"], status=OrderStatus.PAID)
    await _call(factory, "OWNER", "PUT", "/link", world["biz"], json={"account_id": "acct-1"})
    assert (await _call(factory, "OWNER", "POST", "/backfill", world["biz"])).json()["queued"] == 0
