"""staff_tasks / feedback_alerts / dynamic_pricing over HTTP against a real database (SQLite).

Access matrix, per route and per caller: the business owner, an ADMIN member, a plain
MEMBER, a second MEMBER, an inactive member and a stranger. Every test gets a fresh
database, so a state change by one caller cannot hide a failure of the next.

Levels (see app.core.business_access):

* ``member``   owner, admin and member may call it; inactive member / stranger may not;
* ``manage``   owner and admin only (a plain member gets 403);
* ``self``     the person it concerns (the task's assignee, the alert's assignee, the
               staff_id in the path) plus managers; another plain member gets 403;
* ``receipt``  only the recipient of the notification.

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event, func, select
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.api.v1 import dynamic_pricing, feedback_alerts, staff_tasks
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.feedback.feedback_alert_models import (
    AlertStatus,
    FeedbackFollowUp,
    FeedbackSentiment,
    NPSAlert,
    NPSTrendMetric,
    SentimentTrend,
)
from app.domains.locations.checkin_models import LocationFeedback
from app.domains.pricing.pricing_models import (
    LocationDiscountCode,
    LocationPricingTier,
    LocationRevenueImpact,
    PricingABTest,
    PricingTransaction,
)
from app.domains.staff.task_models import (
    ShiftReadinessReport,
    StaffTask,
    TaskNotification,
    TaskStatus,
    TaskTemplate,
    TaskType,
)


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
    Business, Location, BusinessMember, StaffTask, TaskNotification, NPSAlert, NPSTrendMetric,
    SentimentTrend, FeedbackFollowUp, LocationPricingTier, LocationDiscountCode, PricingABTest,
    PricingTransaction, LocationRevenueImpact, ShiftReadinessReport, TaskTemplate, LocationFeedback,
]
COUNTED = [StaffTask, TaskNotification, NPSAlert, LocationDiscountCode, PricingABTest, PricingTransaction,
           LocationPricingTier, NPSTrendMetric, SentimentTrend, LocationRevenueImpact]

ACTORS = ["OWNER", "ADMIN", "MEMBER", "MEMBER2", "INACTIVE", "STRANGER"]
USERS = {name: SimpleNamespace(id=uuid.uuid4()) for name in ACTORS + ["OTHER_OWNER"]}
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
SHIFT = "2026-10-20T09:00:00Z"


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


def _build_app(factory, who: dict | None) -> FastAPI:
    app = FastAPI()
    for module in (staff_tasks, feedback_alerts, dynamic_pricing):
        app.include_router(module.router)

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    if who is not None:  # None -> the real get_current_user (no token => rejected)
        app.dependency_overrides[get_current_user] = lambda: who["user"]
    return app


@pytest_asyncio.fixture
async def world(factory):
    now = datetime.now(timezone.utc)
    u = {k: v.id for k, v in USERS.items()}
    async with factory() as s:
        biz_a = Business(user_id=u["OWNER"], name="A")
        biz_b = Business(user_id=u["OTHER_OWNER"], name="B")
        s.add_all([biz_a, biz_b])
        await s.flush()
        loc_a = Location(business_id=biz_a.id, name="A1", address="x", city="BA", latitude=-34.6, longitude=-58.4)
        loc_b = Location(business_id=biz_b.id, name="B1", address="y", city="BA", latitude=-34.6, longitude=-58.4)
        s.add_all([loc_a, loc_b])
        s.add_all([
            BusinessMember(business_id=biz_a.id, user_id=u["ADMIN"], role=BusinessMemberRole.ADMIN),
            BusinessMember(business_id=biz_a.id, user_id=u["MEMBER"], role=BusinessMemberRole.MEMBER),
            BusinessMember(business_id=biz_a.id, user_id=u["MEMBER2"], role=BusinessMemberRole.MEMBER),
            BusinessMember(business_id=biz_a.id, user_id=u["INACTIVE"], role=BusinessMemberRole.ADMIN, is_active=False),
        ])
        await s.flush()

        def task(biz, loc, who):
            return StaffTask(location_id=loc.id, business_id=biz.id, assigned_to_staff_id=who,
                             assigned_at=now, task_type=TaskType.FOLLOW_UP_CALL, title="Llamar",
                             due_date=now + timedelta(days=1))

        t1, t_other_biz = task(biz_a, loc_a, u["MEMBER"]), task(biz_b, loc_b, u["MEMBER"])
        s.add_all([t1, t_other_biz])
        await s.flush()
        notif = TaskNotification(task_id=t1.id, staff_id=u["MEMBER"], notification_type="assigned")
        al1 = NPSAlert(location_id=loc_a.id, business_id=biz_a.id, feedback_id=uuid.uuid4(), nps_score=2,
                       sentiment=FeedbackSentiment.NEGATIVE)
        al2 = NPSAlert(location_id=loc_a.id, business_id=biz_a.id, feedback_id=uuid.uuid4(), nps_score=3,
                       sentiment=FeedbackSentiment.NEGATIVE, status=AlertStatus.ESCALATED,
                       assigned_to_staff_id=u["MEMBER"])
        al_other = NPSAlert(location_id=loc_b.id, business_id=biz_b.id, feedback_id=uuid.uuid4(), nps_score=1,
                            sentiment=FeedbackSentiment.NEGATIVE, status=AlertStatus.ESCALATED,
                            assigned_to_staff_id=u["MEMBER"])
        fb = LocationFeedback(location_id=loc_a.id, business_id=biz_a.id, nps_score=2, sentiment="negative")
        fb_b = LocationFeedback(location_id=loc_b.id, business_id=biz_b.id, nps_score=1, sentiment="negative")
        s.add_all([fb, fb_b])
        await s.flush()
        ab = PricingABTest(location_id=loc_a.id, business_id=biz_a.id, test_name="t", control_price=10, started_at=now)
        s.add_all([notif, al1, al2, al_other, ab])
        await s.commit()
        ids = SimpleNamespace(biz=biz_a.id, loc=loc_a.id, biz_b=biz_b.id, loc_b=loc_b.id, task=t1.id,
                              task_other=t_other_biz.id, notif=notif.id, alert1=al1.id, alert2=al2.id,
                              ab=ab.id, fb=fb.id, fb_b=fb_b.id, M=u["MEMBER"], users=u)

    who = {"user": USERS["OWNER"]}
    app = _build_app(factory, who)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, factory=factory, **vars(ids))


def _ghost(w: SimpleNamespace) -> SimpleNamespace:
    g = SimpleNamespace(**vars(w))
    for name in ("biz", "loc", "task", "notif", "alert1", "alert2", "ab", "fb"):
        setattr(g, name, uuid.uuid4())
    return g


def _routes(w: SimpleNamespace) -> dict[str, tuple]:
    """name -> (method, url, body, level, has_resource)"""
    due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    return {
        "assign": ("POST", "/api/v1/tasks/assign", {
            "location_id": str(w.loc), "assigned_to_staff_id": str(w.M), "task_type": "follow_up_call",
            "title": "Llamar", "due_date": due}, "manage", True),
        "task-queue": ("GET", f"/api/v1/locations/{w.loc}/task-queue", None, "member", True),
        "auto-assign": ("POST", f"/api/v1/staff/{w.M}/tasks/auto-assign?location_id={w.loc}&shift_start={SHIFT}",
                        None, "manage", True),
        "ack": ("POST", f"/api/v1/tasks/{w.task}/acknowledge", None, "self", True),
        "start": ("POST", f"/api/v1/tasks/{w.task}/start", None, "self", True),
        "complete": ("POST", f"/api/v1/tasks/{w.task}/complete", {"task_id": str(w.task)}, "self", True),
        "cancel": ("POST", f"/api/v1/tasks/{w.task}/cancel", None, "manage", True),
        "task-notifications": ("GET", f"/api/v1/tasks/{w.task}/notifications", None, "self", True),
        "notification-read": ("POST", f"/api/v1/notifications/{w.notif}/read", None, "receipt", True),
        "staff-tasks": ("GET", f"/api/v1/staff/{w.M}/tasks", None, "self", False),
        "shift-report": ("GET", f"/api/v1/staff/{w.M}/shift-report?location_id={w.loc}&shift_start={SHIFT}",
                         None, "self", True),
        "task-performance": ("GET", f"/api/v1/staff/{w.M}/task-performance", None, "self", False),
        "evaluate": ("POST", "/api/v1/feedback/evaluate", {
            "location_id": str(w.loc), "feedback_id": str(w.fb), "nps_score": 2, "sentiment": "negative",
            "comment": "malo"}, "member", True),
        "alert-ack": ("POST", f"/api/v1/alerts/{w.alert1}/acknowledge", None, "manage", True),
        "alert-escalate": ("POST", f"/api/v1/alerts/{w.alert1}/escalate?assigned_to_staff_id={w.M}", None,
                           "manage", True),
        "alert-resolve": ("POST", f"/api/v1/alerts/{w.alert2}/resolve", None, "self", True),
        "location-alerts": ("GET", f"/api/v1/locations/{w.loc}/alerts", None, "member", True),
        "nps-update": ("POST", f"/api/v1/locations/{w.loc}/nps-metrics/update", None, "manage", True),
        "nps-dashboard": ("GET", f"/api/v1/locations/{w.loc}/nps-dashboard", None, "member", True),
        "sentiment-trend": ("POST", f"/api/v1/locations/{w.loc}/sentiment-trend?date={TODAY}", None, "manage", True),
        "assigned-alerts": ("GET", f"/api/v1/staff/{w.M}/assigned-alerts", None, "self", False),
        "price-calc": ("POST", "/api/v1/pricing/calculate", {"location_id": str(w.loc), "base_price": "100"},
                       "member", True),
        "price-log": ("POST", "/api/v1/pricing/log-transaction", {
            "location_id": str(w.loc), "order_id": "o-1", "base_price": "100", "final_price": "90"}, "member", True),
        "tier-get": ("GET", f"/api/v1/locations/{w.loc}/pricing-tier", None, "member", True),
        "tier-set": ("POST", f"/api/v1/locations/{w.loc}/pricing-tier",
                     {"tier": "flagship", "tier_multiplier": "1.2"}, "manage", True),
        "code-create": ("POST", f"/api/v1/locations/{w.loc}/discount-codes",
                        {"code": "SAVE10", "discount_value": "10"}, "manage", True),
        "code-validate": ("GET", f"/api/v1/discount-codes/SAVE10/validate?location_id={w.loc}", None, "member", True),
        "ab-create": ("POST", f"/api/v1/locations/{w.loc}/ab-tests",
                      {"test_name": "t2", "control_price": "10"}, "manage", True),
        "ab-results": ("GET", f"/api/v1/ab-tests/{w.ab}/results", None, "member", True),
        "revenue-impact": ("GET", f"/api/v1/locations/{w.loc}/revenue-impact?date={TODAY}", None, "manage", True),
        "pricing-analytics": ("GET", f"/api/v1/locations/{w.loc}/pricing-analytics", None, "member", True),
    }


ALLOWED = {
    "member": {"OWNER", "ADMIN", "MEMBER", "MEMBER2"},
    "manage": {"OWNER", "ADMIN"},
    "self": {"OWNER", "ADMIN", "MEMBER"},
    "receipt": {"MEMBER"},
}
NAMES = sorted(_routes(SimpleNamespace(
    loc=0, biz=0, task=0, notif=0, alert1=0, alert2=0, ab=0, fb=0, M=0)))
CASES = [(n, a) for n in NAMES for a in ACTORS]


async def _call(client: httpx.AsyncClient, spec: tuple) -> httpx.Response:
    method, url, body, *_ = spec
    return await client.request(method, url, json=body)


async def _snapshot(factory) -> dict:
    async with factory() as s:
        counts = {m.__name__: (await s.execute(select(func.count()).select_from(m))).scalar_one() for m in COUNTED}
        tasks = sorted(str(x) for x in (await s.execute(select(StaffTask.status))).scalars())
        alerts = sorted(str(x) for x in (await s.execute(select(NPSAlert.status))).scalars())
    return {"counts": counts, "tasks": tasks, "alerts": alerts}


# ------------------------------------------------------------------ the access matrix


@pytest.mark.parametrize(("name", "actor"), CASES, ids=[f"{n}:{a}" for n, a in CASES])
async def test_access_matrix(world, name, actor) -> None:
    spec = _routes(world)[name]
    level = spec[3]
    world.who["user"] = USERS[actor]
    before = await _snapshot(world.factory)

    r = await _call(world.client, spec)

    if actor in ALLOWED[level]:
        assert r.status_code == 200, f"{actor} on {name} ({level}): {r.status_code} {r.text[:300]}"
    else:
        assert r.status_code == 403, f"{actor} on {name} ({level}): {r.status_code} {r.text[:300]}"
        assert await _snapshot(world.factory) == before, f"{actor} changed data on {name} despite the 403"


@pytest.mark.parametrize("name", [n for n in NAMES if _routes(_ghost(SimpleNamespace(
    loc=0, biz=0, task=0, notif=0, alert1=0, alert2=0, ab=0, fb=0, M=0)))[n][4]])
async def test_unknown_ids_are_404(world, name) -> None:
    spec = _routes(_ghost(world))[name]

    r = await _call(world.client, spec)

    assert r.status_code == 404, f"{name}: {r.status_code} {r.text[:300]}"


@pytest.mark.parametrize("name", NAMES)
async def test_no_login_is_rejected(factory, world, name) -> None:
    app = _build_app(factory, None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as anon:
        r = await _call(anon, _routes(world)[name])

    assert r.status_code in (401, 403), f"{name}: {r.status_code} {r.text[:200]}"


# ------------------------------------------------------------------ cross-business isolation


async def test_other_businesses_ids_are_403_even_for_an_owner(world) -> None:
    """OWNER owns business A; B's location / alert / task must stay out of reach."""
    probes = [
        ("GET", f"/api/v1/locations/{world.loc_b}/task-queue", None),
        ("GET", f"/api/v1/locations/{world.loc_b}/alerts", None),
        ("GET", f"/api/v1/locations/{world.loc_b}/pricing-tier", None),
        ("POST", f"/api/v1/tasks/{world.task_other}/cancel", None),
        ("POST", f"/api/v1/alerts/{world.alert1}/resolve", None),  # A's, sanity: owner may
    ]
    for method, url, body in probes[:-1]:
        r = await world.client.request(method, url, json=body)
        assert r.status_code == 403, f"{method} {url}: {r.status_code}"
    assert (await world.client.request(*probes[-1][:2])).status_code == 200


async def test_staff_lists_never_leak_across_businesses(world) -> None:
    """MEMBER has a task in A and one in B (where they are not a member): only A's is visible."""
    world.who["user"] = USERS["MEMBER"]
    own = await world.client.get(f"/api/v1/staff/{world.M}/tasks")
    assert [t["task_id"] for t in own.json()["tasks"]] == [str(world.task)], own.text

    world.who["user"] = USERS["ADMIN"]  # manages A only
    seen = await world.client.get(f"/api/v1/staff/{world.M}/tasks")
    assert [t["task_id"] for t in seen.json()["tasks"]] == [str(world.task)], seen.text
    perf = await world.client.get(f"/api/v1/staff/{world.M}/task-performance")
    assert perf.json()["total_tasks"] == 1, perf.text  # not 2

    alerts = await world.client.get(f"/api/v1/staff/{world.M}/assigned-alerts")
    assert [a["alert_id"] for a in alerts.json()["alerts"]] == [str(world.alert2)], alerts.text


# ------------------------------------------------------------------ rules beyond the matrix


async def test_cannot_assign_work_to_someone_outside_the_business(world) -> None:
    due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    for who in ("STRANGER", "INACTIVE"):
        r = await world.client.post("/api/v1/tasks/assign", json={
            "location_id": str(world.loc), "assigned_to_staff_id": str(USERS[who].id),
            "task_type": "follow_up_call", "title": "x", "due_date": due})
        assert r.status_code == 400, (who, r.text)
    esc = await world.client.post(f"/api/v1/alerts/{world.alert1}/escalate?assigned_to_staff_id={USERS['STRANGER'].id}")
    assert esc.status_code == 400, esc.text
    auto = await world.client.post(
        f"/api/v1/staff/{USERS['STRANGER'].id}/tasks/auto-assign?location_id={world.loc}&shift_start={SHIFT}")
    assert auto.status_code == 400, auto.text


async def test_assign_uses_the_locations_real_business_and_notifies(world) -> None:
    due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    r = await world.client.post("/api/v1/tasks/assign", json={
        "location_id": str(world.loc), "assigned_to_staff_id": str(world.M), "task_type": "follow_up_call",
        "title": "Llamar", "due_date": due})

    assert r.status_code == 200, r.text
    async with world.factory() as s:
        created = (await s.execute(select(StaffTask).where(StaffTask.id == uuid.UUID(r.json()["task_id"])))).scalar_one()
        notified = (await s.execute(select(TaskNotification).where(TaskNotification.task_id == created.id))).scalars().all()
    assert created.business_id == world.biz  # used to be the all-zero UUID
    assert created.assigned_by_staff_id == USERS["OWNER"].id
    assert {n.staff_id for n in notified} == {world.M}
    assert sorted(n.notification_type for n in notified) == ["in_app", "push"]  # one per channel


async def test_task_lifecycle_for_the_assignee(world) -> None:
    world.who["user"] = USERS["MEMBER"]
    base = f"/api/v1/tasks/{world.task}"

    assert (await world.client.post(f"{base}/acknowledge")).status_code == 200
    assert (await world.client.post(f"{base}/start")).status_code == 200
    done = await world.client.post(f"{base}/complete", json={"task_id": str(world.task), "completion_notes": "ok"})
    assert done.status_code == 200, done.text
    async with world.factory() as s:
        assert (await s.get(StaffTask, world.task)).status == TaskStatus.COMPLETED


async def test_complete_rejects_path_body_mismatch(world) -> None:
    r = await world.client.post(f"/api/v1/tasks/{world.task}/complete", json={"task_id": str(uuid.uuid4())})

    assert r.status_code == 400, r.text


async def test_a_manager_may_read_but_not_sign_for_a_notification(world) -> None:
    world.who["user"] = USERS["ADMIN"]
    assert (await world.client.get(f"/api/v1/tasks/{world.task}/notifications")).status_code == 200
    assert (await world.client.post(f"/api/v1/notifications/{world.notif}/read")).status_code == 403
    world.who["user"] = USERS["MEMBER"]
    read = await world.client.post(f"/api/v1/notifications/{world.notif}/read")
    assert read.status_code == 200, read.text
    async with world.factory() as s:
        assert (await s.get(TaskNotification, world.notif)).read_at is not None


async def test_only_the_assignee_or_a_manager_resolves_an_alert(world) -> None:
    world.who["user"] = USERS["MEMBER2"]
    assert (await world.client.post(f"/api/v1/alerts/{world.alert2}/resolve")).status_code == 403
    world.who["user"] = USERS["MEMBER"]
    assert (await world.client.post(f"/api/v1/alerts/{world.alert1}/resolve")).status_code == 403  # not theirs
    assert (await world.client.post(f"/api/v1/alerts/{world.alert2}/resolve")).status_code == 200
    async with world.factory() as s:
        assert (await s.get(NPSAlert, world.alert2)).status == AlertStatus.RESOLVED


async def test_evaluate_feedback_alerts_with_the_real_business_id(world) -> None:
    world.who["user"] = USERS["MEMBER"]
    r = await world.client.post("/api/v1/feedback/evaluate", json={
        "location_id": str(world.loc), "feedback_id": str(world.fb), "nps_score": 1,
        "sentiment": "negative", "comment": "pésimo", "visitor_email": "v@x.test"})

    assert r.status_code == 200, r.text
    async with world.factory() as s:
        created = (await s.execute(select(NPSAlert).where(NPSAlert.comment == "pésimo"))).scalars().all()
    assert [a.business_id for a in created] == [world.biz]


async def test_complete_alert_flow_ack_escalate(world) -> None:
    ack = await world.client.post(f"/api/v1/alerts/{world.alert1}/acknowledge")
    esc = await world.client.post(f"/api/v1/alerts/{world.alert1}/escalate?assigned_to_staff_id={world.M}&resolution_plan=llamar")

    assert ack.status_code == esc.status_code == 200, (ack.text, esc.text)
    async with world.factory() as s:
        alert = await s.get(NPSAlert, world.alert1)
    assert alert.status == AlertStatus.ESCALATED
    assert alert.assigned_to_staff_id == world.M


# ------------------------------------------------------------------ pricing


async def test_pricing_flow_with_real_business_ids(world) -> None:
    c = world.client
    assert (await c.post(f"/api/v1/locations/{world.loc}/pricing-tier",
                         json={"tier": "flagship", "tier_multiplier": "1.2"})).status_code == 200
    assert (await c.post(f"/api/v1/locations/{world.loc}/discount-codes",
                         json={"code": "SAVE10", "discount_value": "10", "usage_limit": 5})).status_code == 200
    ab = await c.post(f"/api/v1/locations/{world.loc}/ab-tests", json={"test_name": "t2", "control_price": "10"})
    assert ab.status_code == 200, ab.text

    world.who["user"] = USERS["MEMBER"]  # a cashier: may price, validate and log, not configure
    valid = await c.get(f"/api/v1/discount-codes/SAVE10/validate?location_id={world.loc}")
    price = await c.post("/api/v1/pricing/calculate", json={
        "location_id": str(world.loc), "base_price": "100", "discount_code": "SAVE10"})
    logged = await c.post("/api/v1/pricing/log-transaction", json={
        "location_id": str(world.loc), "order_id": "o-9", "base_price": "100", "final_price": "108",
        "discount_code": "SAVE10", "discount_amount": "12"})
    assert valid.status_code == price.status_code == logged.status_code == 200, (valid.text, price.text, logged.text)

    async with world.factory() as s:
        tier = (await s.execute(select(LocationPricingTier))).scalar_one()
        code = (await s.execute(select(LocationDiscountCode))).scalar_one()
        tx = (await s.execute(select(PricingTransaction))).scalar_one()
        new_ab = (await s.execute(select(PricingABTest).where(PricingABTest.test_name == "t2"))).scalar_one()
    assert {tier.business_id, code.business_id, tx.business_id, new_ab.business_id} == {world.biz}

    world.who["user"] = USERS["ADMIN"]
    impact = await c.get(f"/api/v1/locations/{world.loc}/revenue-impact?date={TODAY}")
    analytics = await c.get(f"/api/v1/locations/{world.loc}/pricing-analytics")
    assert impact.status_code == analytics.status_code == 200, (impact.text, analytics.text)
    assert analytics.json()["total_transactions"] >= 1, analytics.text


@pytest.mark.parametrize(("url", "body"), [
    ("/api/v1/locations/{loc}/pricing-tier", {"tier": "x", "tier_multiplier": "-1"}),
    ("/api/v1/locations/{loc}/pricing-tier", {"tier": "x", "tier_multiplier": "1", "peak_discount_pct": "150"}),
    ("/api/v1/locations/{loc}/discount-codes", {"code": "X", "discount_value": "150"}),
    ("/api/v1/locations/{loc}/discount-codes", {"code": "X", "discount_value": "0"}),
    ("/api/v1/locations/{loc}/discount-codes", {"code": "X", "discount_value": "5", "valid_days": 0}),
    ("/api/v1/pricing/calculate", {"location_id": "{loc}", "base_price": "-5"}),
])
async def test_pricing_rejects_nonsense_amounts(world, url, body) -> None:
    body = {k: (str(world.loc) if v == "{loc}" else v) for k, v in body.items()}

    r = await world.client.post(url.format(loc=world.loc), json=body)

    assert r.status_code == 422, r.text
    async with world.factory() as s:
        assert (await s.execute(select(func.count()).select_from(LocationDiscountCode))).scalar_one() == 0


async def test_evaluate_rejects_feedback_from_another_location_or_that_does_not_exist(world) -> None:
    """Postgres' FK only proves the feedback row exists; it must also belong to the location."""
    for feedback_id in (world.fb_b, uuid.uuid4()):  # business B's feedback, and one that does not exist
        r = await world.client.post("/api/v1/feedback/evaluate", json={
            "location_id": str(world.loc), "feedback_id": str(feedback_id), "nps_score": 1, "sentiment": "negative"})
        assert r.status_code == 404, (feedback_id, r.status_code, r.text)
    async with world.factory() as s:
        assert (await s.execute(select(func.count()).select_from(NPSAlert).where(NPSAlert.nps_score == 1))).scalar_one() == 1  # only the seeded B alert


async def test_nps_score_must_be_between_0_and_10(world) -> None:
    for bad in (-1, 11):
        r = await world.client.post("/api/v1/feedback/evaluate", json={
            "location_id": str(world.loc), "feedback_id": str(world.fb), "nps_score": bad, "sentiment": "negative"})
        assert r.status_code == 422, (bad, r.text)


async def test_sentiment_trend_is_stored_under_the_real_business(world) -> None:
    """Used to insert the all-zero business_id, which only Postgres' FK noticed."""
    r = await world.client.post(f"/api/v1/locations/{world.loc}/sentiment-trend?date={TODAY}")

    assert r.status_code == 200 and r.json()["calculated"] is True, r.text
    async with world.factory() as s:
        trend = (await s.execute(select(SentimentTrend))).scalar_one()
    assert trend.business_id == world.biz and trend.location_id == world.loc
