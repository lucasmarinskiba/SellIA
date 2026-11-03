"""automations router: who may touch which business's automations.

Before this, all 57 endpoints only asked for *a* logged-in user and then trusted the business_id (or the id of
the row) the client sent, so anyone with an account could read, edit, delete, run or spam any other business's
workflows, templates, sequences, chatbot rules, content and toggles by changing an id. The router also lets the
client pick where the server sends webhooks (an SSRF) and lets ``generation_config`` overwrite the
``business_id`` handed to the Celery task.

Callers (see app.core.business_access): the business owner, an ADMIN member, a plain MEMBER, an inactive
member, a stranger and the owner of a *different* business. Two levels:

* ``member``  the owner or any active member (reads, and the content pipeline: generate / approve / calendar);
* ``manage``  the owner or an ADMIN member (workflows, templates, sequences, rules, toggles, schedules,
  notification rules, seeding, running a workflow).

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, Callable, Optional

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event, select
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.api.v1 import automations
from app.core.database import Base, get_db
from app.core.deps import get_current_active_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.automations import models as am
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.catalogs.models import CatalogItem, CatalogItemType
from app.domains.channels.models import ChannelConnection
from app.domains.harvey import discovery


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


@compiles(sqltypes.UUID, "sqlite")
def _uuid_as_char(type_, compiler, **kw):
    return "CHAR(32)"


def _make_aware(target, *_args) -> None:
    """timestamptz comes back timezone-aware from Postgres; SQLite hands back naive datetimes."""
    for key, value in list(target.__dict__.items()):
        if isinstance(value, datetime) and value.tzinfo is None:
            target.__dict__[key] = value.replace(tzinfo=timezone.utc)


event.listen(Base, "load", _make_aware, propagate=True)
event.listen(Base, "refresh", _make_aware, propagate=True)

MODELS = [
    Business, BusinessMember, CatalogItem, ChannelConnection,
    am.Workflow, am.WorkflowVariant, am.EmailTemplate, am.EmailSequence, am.SequenceStep,
    am.SequenceSubscription, am.SequenceEmailLog, am.ChatbotRule, am.GeneratedContent, am.ContentCalendar,
    am.AutomationToggle, am.ToggleAuditLog, am.ToggleSchedule, am.ToggleNotificationRule,
    am.ToggleNotificationLog,
]

ACTORS = ["OWNER", "ADMIN", "MEMBER", "INACTIVE", "STRANGER", "OTHER_OWNER"]
USERS = {name: SimpleNamespace(id=uuid.uuid4(), email=f"{name.lower()}@example.com") for name in ACTORS}
FUTURE = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


def _build_app(factory, who: Optional[str]) -> FastAPI:
    app = FastAPI()
    app.include_router(automations.router, prefix="/api/v1/automations")  # as in app/main.py

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    if who is not None:  # None -> the real get_current_active_user (no token => rejected)
        app.dependency_overrides[get_current_active_user] = lambda: USERS[who]
    return app


async def _seed_business(s, owner_id, label: str) -> dict:
    biz = Business(user_id=owner_id, name=f"Biz {label}")
    s.add(biz)
    await s.flush()
    wf = am.Workflow(business_id=biz.id, name="wf", trigger_type=am.WorkflowTriggerType.NEW_LEAD)
    toggle = am.AutomationToggle(business_id=biz.id, toggle_key=f"key_{label}", category=am.ToggleCategory.AGENT,
                                 display_name="T")
    s.add_all([
        wf, toggle,
        am.EmailTemplate(business_id=biz.id, name="t", subject="s", body_text="b"),
        am.EmailSequence(business_id=biz.id, name="seq"),
        am.ChatbotRule(business_id=biz.id, name="r", intent="price", response_template="hi"),
        am.GeneratedContent(business_id=biz.id, content_type="copy", agent_slug="x"),
        CatalogItem(business_id=biz.id, type=CatalogItemType.GOOD, name="p", price=10),
        ChannelConnection(business_id=biz.id, platform="instagram", name="ig"),
    ])
    await s.flush()
    tmpl = (await s.execute(select(am.EmailTemplate).where(am.EmailTemplate.business_id == biz.id))).scalar_one()
    seq = (await s.execute(select(am.EmailSequence).where(am.EmailSequence.business_id == biz.id))).scalar_one()
    rule = (await s.execute(select(am.ChatbotRule).where(am.ChatbotRule.business_id == biz.id))).scalar_one()
    content = (await s.execute(select(am.GeneratedContent).where(am.GeneratedContent.business_id == biz.id))).scalar_one()
    catalog = (await s.execute(select(CatalogItem).where(CatalogItem.business_id == biz.id))).scalar_one()
    channel = (await s.execute(select(ChannelConnection).where(ChannelConnection.business_id == biz.id))).scalar_one()
    variant = am.WorkflowVariant(workflow_id=wf.id, business_id=biz.id, variant_name="A")
    entry = am.ContentCalendar(business_id=biz.id, scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
                               platform="instagram", content_format="post")
    sched = am.ToggleSchedule(business_id=biz.id, toggle_id=toggle.id,
                              start_time=datetime.now(timezone.utc) + timedelta(hours=1), action="enable")
    nrule = am.ToggleNotificationRule(business_id=biz.id, toggle_id=toggle.id,
                                      event_type=am.ToggleNotificationEventType.ENABLED)
    s.add_all([variant, entry, sched, nrule])
    await s.flush()
    return {
        "biz": biz.id, "wf": wf.id, "variant": variant.id, "tmpl": tmpl.id, "seq": seq.id, "rule": rule.id,
        "content": content.id, "entry": entry.id, "toggle": toggle.id, "sched": sched.id, "nrule": nrule.id,
        "catalog": catalog.id, "channel": channel.id, "slug": "some-tool",
    }


@pytest_asyncio.fixture
async def world(factory):
    async with factory() as s:
        a = await _seed_business(s, USERS["OWNER"].id, "A")
        b = await _seed_business(s, USERS["OTHER_OWNER"].id, "B")
        s.add_all([
            BusinessMember(business_id=a["biz"], user_id=USERS["ADMIN"].id, role=BusinessMemberRole.ADMIN,
                           is_active=True),
            BusinessMember(business_id=a["biz"], user_id=USERS["MEMBER"].id, role=BusinessMemberRole.MEMBER,
                           is_active=True),
            BusinessMember(business_id=a["biz"], user_id=USERS["INACTIVE"].id, role=BusinessMemberRole.ADMIN,
                           is_active=False),
        ])
        await s.commit()
    return {"A": a, "B": b}


@pytest.fixture(autouse=True)
def _no_side_effects(monkeypatch):
    """Nothing here may reach Celery, the workflow engine or the seeders: only the access rules are under test."""
    import app.domains.automations.engine as engine
    import app.domains.automations.seed_toggles as seed_toggles
    import app.tasks.content_tasks as content_tasks

    async def _noop(*_a, **_k):
        return None

    class _Engine:
        def __init__(self, *_a, **_k):
            pass

        async def process_trigger(self, **_k):
            return []

    TASK_CALLS.clear()

    def _delay(**kwargs):
        TASK_CALLS.append(kwargs)
        return SimpleNamespace(id="task-1")

    monkeypatch.setattr(automations, "seed_automations", _noop)
    monkeypatch.setattr(seed_toggles, "seed_toggles_for_business", _noop)
    monkeypatch.setattr(engine, "WorkflowEngine", _Engine)
    for name in ("generate_product_images_task", "generate_video_clips_task", "generate_product_copy_task",
                 "generate_carousel_task", "generate_thumbnail_task"):
        monkeypatch.setattr(getattr(content_tasks, name), "delay", _delay)

    async def _resolve(host: str) -> list[str]:  # never touch DNS
        return ["127.0.0.1"] if host == "localhost" else ["93.184.216.34"]

    monkeypatch.setattr(discovery, "resolve_host", _resolve)


TASK_CALLS: list[dict] = []


@dataclass
class Spec:
    id: str
    method: str
    path: str  # formatted with the ids of the business being targeted
    level: str  # "member" | "manage"
    params: Optional[Callable[[dict], dict]] = None
    body: Any = None  # dict, or callable(ids) -> dict
    ok: bool = True  # the owner must get a 2xx (False: the handler needs services that are not stubbed here)


def _q(ids: dict) -> dict:
    return {"business_id": str(ids["biz"])}


CAL_BODY = {"scheduled_at": FUTURE, "platform": "instagram", "content_format": "post"}

SPECS = [
    Spec("wf-list", "GET", "/workflows", "member", _q),
    Spec("wf-create", "POST", "/workflows", "manage",
         body=lambda i: {"name": "n", "trigger_type": "new_lead", "business_id": str(i["biz"])}),
    Spec("wf-update", "PATCH", "/workflows/{wf}", "manage", body={"name": "renamed"}),
    Spec("wf-delete", "DELETE", "/workflows/{wf}", "manage"),
    Spec("wf-execute", "POST", "/workflows/{wf}/execute", "manage", _q),
    Spec("seed", "POST", "/seed", "manage", _q),
    Spec("tmpl-list", "GET", "/email-templates", "member", _q),
    Spec("tmpl-create", "POST", "/email-templates", "manage",
         body=lambda i: {"name": "n", "subject": "s", "body_text": "b", "business_id": str(i["biz"])}),
    Spec("tmpl-update", "PATCH", "/email-templates/{tmpl}", "manage", body={"name": "x"}),
    Spec("tmpl-delete", "DELETE", "/email-templates/{tmpl}", "manage"),
    Spec("seq-list", "GET", "/email-sequences", "member", _q),
    Spec("seq-create", "POST", "/email-sequences", "manage",
         body=lambda i: {"name": "n", "business_id": str(i["biz"])}),
    Spec("seq-get", "GET", "/email-sequences/{seq}", "member"),
    Spec("seq-update", "PATCH", "/email-sequences/{seq}", "manage", body={"name": "x"}),
    Spec("seq-analytics", "GET", "/email-sequences/{seq}/analytics", "member"),
    Spec("seq-delete", "DELETE", "/email-sequences/{seq}", "manage"),
    Spec("rule-list", "GET", "/chatbot-rules", "member", _q),
    Spec("rule-create", "POST", "/chatbot-rules", "manage",
         body=lambda i: {"name": "n", "intent": "i", "response_template": "r", "business_id": str(i["biz"])}),
    Spec("rule-update", "PATCH", "/chatbot-rules/{rule}", "manage", body={"name": "x"}),
    Spec("rule-delete", "DELETE", "/chatbot-rules/{rule}", "manage"),
    # The A/B endpoints answer 500 for the owner for a reason unrelated to access: the schema, router and
    # engine use WorkflowVariant.is_control but the model/table has no such column. Only the access decision
    # (403 before any of that) is asserted here; fixing the column is a schema change for its own PR.
    Spec("variant-create", "POST", "/workflows/{wf}/variants", "manage", body={"variant_name": "B"}, ok=False),
    Spec("variant-list", "GET", "/workflows/{wf}/variants", "member", ok=False),
    Spec("variant-update", "PATCH", "/workflows/{wf}/variants/{variant}", "manage", body={"variant_name": "Z"},
         ok=False),
    Spec("variant-delete", "DELETE", "/workflows/{wf}/variants/{variant}", "manage", ok=False),
    Spec("ab-results", "GET", "/workflows/{wf}/ab-test-results", "member", ok=False),
    Spec("content-generate", "POST", "/content/generate", "member", _q,
         body=lambda i: {"content_type": "copy", "catalog_item_id": str(i["catalog"])}),
    Spec("content-list", "GET", "/content", "member", _q),
    Spec("content-get", "GET", "/content/{content}", "member"),
    Spec("content-approve", "PATCH", "/content/{content}/approve", "member"),
    Spec("content-reject", "PATCH", "/content/{content}/reject", "member"),
    Spec("cal-list", "GET", "/calendar", "member", _q),
    Spec("cal-create", "POST", "/calendar", "member", _q, body=CAL_BODY),
    Spec("cal-update", "PATCH", "/calendar/{entry}", "member", body=CAL_BODY),
    Spec("cal-delete", "DELETE", "/calendar/{entry}", "member"),
    Spec("cal-publish", "POST", "/calendar/{entry}/publish", "member"),
    Spec("tools", "GET", "/content/tools", "member", _q, ok=False),
    Spec("tool-detail", "GET", "/content/tools/{slug}", "member", _q, ok=False),
    Spec("pricing", "GET", "/content/pricing", "member", _q, ok=False),
    Spec("usage", "GET", "/content/usage", "member", _q, ok=False),
    Spec("toggle-list", "GET", "/toggles/business/{biz}", "member"),
    Spec("toggle-search", "GET", "/toggles/business/{biz}/search", "member"),
    Spec("toggle-create", "POST", "/toggles/business/{biz}", "manage",
         body={"toggle_key": "new_key", "category": "agent", "display_name": "N"}),
    Spec("toggle-get", "GET", "/toggles/{toggle}", "member"),
    Spec("toggle-update", "PATCH", "/toggles/{toggle}", "manage", body={"is_enabled": True}),
    Spec("toggle-audit", "GET", "/toggles/{toggle}/audit", "member"),
    Spec("toggle-reset", "POST", "/toggles/{toggle}/reset-usage", "manage"),
    Spec("toggle-dashboard", "GET", "/toggles/dashboard/{biz}", "member"),
    Spec("toggle-seed", "POST", "/toggles/seed/{biz}", "manage"),
    Spec("sched-create", "POST", "/toggles/{toggle}/schedule", "manage",
         body=lambda i: {"toggle_id": str(i["toggle"]), "start_time": FUTURE, "action": "enable"}),
    Spec("sched-list", "GET", "/toggles/{toggle}/schedules", "member"),
    Spec("sched-update", "PATCH", "/schedule/{sched}", "manage", body={"reason": "r"}),
    Spec("sched-delete", "DELETE", "/schedule/{sched}", "manage"),
    Spec("nrule-create", "POST", "/toggles/{toggle}/notification-rule", "manage",
         body=lambda i: {"toggle_id": str(i["toggle"]), "event_type": "enabled"}),
    # recipients and the webhook secret live here: managers only, even to read
    Spec("nrule-list", "GET", "/toggles/{toggle}/notification-rules", "manage"),
    Spec("nrule-update", "PATCH", "/notification-rule/{nrule}", "manage", body={"notify_via_email": False}),
    Spec("nrule-delete", "DELETE", "/notification-rule/{nrule}", "manage"),
    Spec("nrule-logs", "GET", "/toggles/{toggle}/notification-logs", "member"),
]


def _norm(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path)


async def _call(client: httpx.AsyncClient, spec: Spec, ids: dict) -> httpx.Response:
    body = spec.body(ids) if callable(spec.body) else spec.body
    return await client.request(
        spec.method, "/api/v1/automations" + spec.path.format(**ids),
        params=spec.params(ids) if spec.params else None, json=body,
    )


def _client(app: FastAPI) -> httpx.AsyncClient:
    # raise_app_exceptions=False: a handler that needs a service this test does not provide answers 500
    # instead of aborting the test; the access decision (403) always happens before that.
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                             base_url="http://test")


async def _snapshot(factory) -> dict:
    async with factory() as s:
        return {
            m.__tablename__: sorted(repr(tuple(r)) for r in (await s.execute(select(m.__table__))).all())
            for m in MODELS
        }


def test_every_endpoint_is_in_the_matrix():
    routes = {
        (method, _norm(r.path_format))
        for r in automations.router.routes
        for method in r.methods
        if method not in {"HEAD", "OPTIONS"}
    }
    covered = {(s.method, _norm(s.path)) for s in SPECS}
    assert routes - covered == set(), "endpoint without an access test: add it to SPECS"
    assert covered - routes == set(), "SPECS entry for an endpoint that does not exist"


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.id)
async def test_access_rules(spec, factory, world):
    a, b = world["A"], world["B"]
    before = await _snapshot(factory)

    async def as_(actor: str, ids: dict) -> httpx.Response:
        async with _client(_build_app(factory, actor)) as c:
            return await _call(c, spec, ids)

    # Not in the business -> refused, and nothing was touched.
    for actor in ("STRANGER", "OTHER_OWNER", "INACTIVE"):
        r = await as_(actor, a)
        assert r.status_code == 403, f"{actor} on business A: {r.status_code} {r.text[:200]}"
    # A real owner, but of the *other* business: their id is not a key to this one.
    r = await as_("OWNER", b)
    assert r.status_code == 403, f"OWNER of A on business B: {r.status_code} {r.text[:200]}"
    if spec.level == "manage":
        r = await as_("MEMBER", a)
        assert r.status_code == 403, f"plain MEMBER on a manage endpoint: {r.status_code} {r.text[:200]}"
    assert await _snapshot(factory) == before, "a refused request changed data"

    # Allowed callers get through.
    r = await as_("OWNER", a)
    if spec.ok:
        assert 200 <= r.status_code < 300, f"OWNER: {r.status_code} {r.text[:300]}"
    else:
        assert r.status_code not in (401, 403), f"OWNER: {r.status_code} {r.text[:300]}"
    r = await as_("ADMIN", a)
    assert r.status_code not in (401, 403), f"ADMIN: {r.status_code} {r.text[:300]}"
    if spec.level == "member":
        r = await as_("MEMBER", a)
        assert r.status_code not in (401, 403), f"MEMBER: {r.status_code} {r.text[:300]}"


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.id)
async def test_requires_login(spec, factory, world):
    before = await _snapshot(factory)
    async with _client(_build_app(factory, None)) as c:
        r = await _call(c, spec, world["A"])
    assert r.status_code in (401, 403), f"{r.status_code} {r.text[:200]}"
    assert await _snapshot(factory) == before


# ── targeted regressions ────────────────────────────────────────────────────


async def test_generation_config_cannot_repoint_the_task_at_another_business(factory, world):
    a, b = world["A"], world["B"]
    body = {"content_type": "copy", "catalog_item_id": str(a["catalog"]),
            "generation_config": {"business_id": str(b["biz"]), "catalog_item_id": str(b["catalog"]),
                                  "style": "minimal"}}
    async with _client(_build_app(factory, "OWNER")) as c:
        r = await c.post("/api/v1/automations/content/generate", params={"business_id": str(a["biz"])}, json=body)
    assert r.status_code == 200, r.text
    assert len(TASK_CALLS) == 1
    assert TASK_CALLS[0]["business_id"] == str(a["biz"])
    assert TASK_CALLS[0]["catalog_item_id"] == str(a["catalog"])
    assert TASK_CALLS[0]["style"] == "minimal"  # harmless options still pass through


async def test_generate_refuses_a_product_of_another_business(factory, world):
    a, b = world["A"], world["B"]
    body = {"content_type": "copy", "catalog_item_id": str(b["catalog"])}
    async with _client(_build_app(factory, "OWNER")) as c:
        r = await c.post("/api/v1/automations/content/generate", params={"business_id": str(a["biz"])}, json=body)
    assert r.status_code == 400
    assert TASK_CALLS == []


async def test_calendar_entries_can_only_reference_the_same_business(factory, world):
    a, b = world["A"], world["B"]
    url = "/api/v1/automations/calendar"
    async with _client(_build_app(factory, "OWNER")) as c:
        for field in ("channel_connection_id", "catalog_item_id", "generated_content_id", "workflow_id"):
            foreign = {"channel_connection_id": b["channel"], "catalog_item_id": b["catalog"],
                       "generated_content_id": b["content"], "workflow_id": b["wf"]}[field]
            r = await c.post(url, params={"business_id": str(a["biz"])}, json={**CAL_BODY, field: str(foreign)})
            assert r.status_code == 400, f"create with a foreign {field}: {r.status_code} {r.text[:200]}"
            r = await c.patch(f"{url}/{a['entry']}", json={**CAL_BODY, field: str(foreign)})
            assert r.status_code == 400, f"update with a foreign {field}: {r.status_code} {r.text[:200]}"
        own = {"channel_connection_id": str(a["channel"]), "catalog_item_id": str(a["catalog"]),
               "generated_content_id": str(a["content"]), "workflow_id": str(a["wf"])}
        r = await c.post(url, params={"business_id": str(a["biz"])}, json={**CAL_BODY, **own})
        assert r.status_code == 201, r.text
    async with factory() as s:
        entry = await s.get(am.ContentCalendar, a["entry"])
        assert entry.channel_connection_id is None and entry.workflow_id is None  # the refused updates changed nothing


BAD_WEBHOOKS = [
    "http://169.254.169.254/latest/meta-data/",  # cloud metadata
    "http://127.0.0.1/hook",
    "http://localhost/hook",  # resolves to loopback
    "http://10.0.0.5/hook",
    "http://[::1]/hook",
    "http://127.0.0.1:8000/hook",  # only ports 80/443
    "http://user:pass@example.com/hook",
    "ftp://example.com/hook",
    "file:///etc/passwd",
]


@pytest.mark.parametrize("url", BAD_WEBHOOKS)
async def test_webhook_url_must_be_a_public_address(url, factory, world):
    a = world["A"]
    base = f"/api/v1/automations/toggles/{a['toggle']}/notification-rule"
    body = {"toggle_id": str(a["toggle"]), "event_type": "disabled", "notify_via_webhook": True, "webhook_url": url}
    async with _client(_build_app(factory, "OWNER")) as c:
        r = await c.post(base, json=body)
        assert r.status_code == 400, f"create: {r.status_code} {r.text[:200]}"
        r = await c.patch(f"/api/v1/automations/notification-rule/{a['nrule']}", json={"webhook_url": url})
        assert r.status_code == 400, f"update: {r.status_code} {r.text[:200]}"
    async with factory() as s:
        rules = (await s.execute(select(am.ToggleNotificationRule))).scalars().all()
    assert all(rule.webhook_url is None for rule in rules)


async def test_a_public_webhook_url_is_accepted(factory, world):
    a = world["A"]
    async with _client(_build_app(factory, "OWNER")) as c:
        r = await c.post(
            f"/api/v1/automations/toggles/{a['toggle']}/notification-rule",
            json={"toggle_id": str(a["toggle"]), "event_type": "disabled", "notify_via_webhook": True,
                  "webhook_url": "https://hooks.example.com/sellia"})
        assert r.status_code == 201, r.text
        r = await c.patch(f"/api/v1/automations/notification-rule/{a['nrule']}",
                          json={"webhook_url": "https://hooks.example.com/other"})
        assert r.status_code == 200, r.text
    assert r.json()["webhook_url"] == "https://hooks.example.com/other"


class _FakeAsyncClient:
    posts: list[str] = []

    def __init__(self, *_a, **_k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_a):
        return False

    async def post(self, url, **_k):
        _FakeAsyncClient.posts.append(url)
        return SimpleNamespace(status_code=200)


@pytest.mark.parametrize("url,expected_posts,expected_status", [
    ("http://169.254.169.254/latest/meta-data/", 0, "failed"),  # DNS/data changed after the rule was saved
    ("http://localhost/hook", 0, "failed"),
    ("https://hooks.example.com/sellia", 1, "sent"),
])
async def test_notification_sender_rechecks_the_url_before_posting(url, expected_posts, expected_status, factory,
                                                                    world, monkeypatch):
    from app.domains.automations import tasks

    a = world["A"]
    _FakeAsyncClient.posts = []
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    async with factory() as s:
        rule = await s.get(am.ToggleNotificationRule, a["nrule"])
        rule.notify_via_email = False
        rule.notify_via_webhook = True
        rule.webhook_url = url  # written directly, as if it had been valid when saved
        await s.commit()
    async with factory() as s:
        await tasks.send_toggle_notification(db=s, toggle_id=a["toggle"], business_id=a["biz"],
                                             event_type="enabled", toggle_name="T")
    async with factory() as s:
        logs = (await s.execute(select(am.ToggleNotificationLog))).scalars().all()
    assert len(_FakeAsyncClient.posts) == expected_posts
    assert [log.status for log in logs] == [expected_status]


@pytest.mark.parametrize("path", ["tools", "pricing", "usage"])
async def test_static_content_routes_are_not_shadowed_by_the_content_id_route(path, factory, world):
    """GET /content/{content_id} used to match these first and answer 422 (not a valid UUID)."""
    async with _client(_build_app(factory, "OWNER")) as c:
        r = await c.get(f"/api/v1/automations/content/{path}", params={"business_id": str(world["A"]["biz"])})
    assert r.status_code != 422, r.text[:200]
