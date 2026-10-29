"""The monthly AI cap per business: metering, the limit, and every place that degrades instead of failing."""

# The db fixture comes from test_harvey, so every test argument "redefines" it.
# ruff: noqa: F811

import sys
import types
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from test_harvey import _Biz, _fake_model, _setup, db  # noqa: F401 - db is a pytest fixture

from app.domains.harvey import ai_budget, llm, onboarding
from app.domains.harvey import service as harvey_service
from app.domains.harvey.service import HarveyError
from app.domains.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus, UsageTracking
from app.domains.users.models import User


class _Owned(_Biz):
    """The test business stand-in with an owner, which is what the cap is charged to."""

    def __init__(self):
        super().__init__()
        self.user_id = uuid.uuid4()


@pytest_asyncio.fixture
async def billing(db):
    async with db.bind.begin() as conn:
        for m in (UsageTracking, SubscriptionPlan, Subscription, User):
            await conn.run_sync(lambda c, m=m: m.__table__.create(bind=c, checkfirst=True))
    return db


async def _used(db, user_id) -> int:
    rows = await db.execute(select(UsageTracking.quantity).where(UsageTracking.user_id == user_id))
    return sum(q for (q,) in rows.all())


async def _spend(db, biz, tokens):
    async with ai_budget.metered(db, biz):
        ai_budget.record_tokens(tokens)


# ── metering and the limit ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_tokens_used_inside_the_block_are_recorded_for_the_owner(billing):
    biz = _Owned()
    await _spend(billing, biz, 1200)
    await _spend(billing, biz, 300)
    assert await _used(billing, biz.user_id) == 1500
    st = await ai_budget.status(billing, biz.user_id)
    assert st["used"] == 1500 and st["limit"] == ai_budget.DEFAULT_MONTHLY["free"] and not st["exceeded"]


@pytest.mark.asyncio
async def test_nothing_is_recorded_outside_the_block_or_for_zero_tokens(billing):
    biz = _Owned()
    ai_budget.record_tokens(500)  # no meter active
    async with ai_budget.metered(billing, biz):
        pass
    assert await _used(billing, biz.user_id) == 0


@pytest.mark.asyncio
async def test_the_call_is_refused_once_the_month_is_used_up(billing):
    biz = _Owned()
    await _spend(billing, biz, ai_budget.DEFAULT_MONTHLY["free"])
    with pytest.raises(ai_budget.BudgetExceeded) as e:
        async with ai_budget.metered(billing, biz):
            raise AssertionError("the body must not run")
    assert "límite de IA" in str(e.value)
    st = await ai_budget.status(billing, biz.user_id)
    assert st["exceeded"] and st["remaining"] == 0 and st["percent"] == 100


@pytest.mark.asyncio
async def test_the_warning_starts_at_eighty_percent(billing):
    biz = _Owned()
    await _spend(billing, biz, int(0.79 * ai_budget.DEFAULT_MONTHLY["free"]))
    assert not (await ai_budget.status(billing, biz.user_id))["near_limit"]
    await _spend(billing, biz, int(0.02 * ai_budget.DEFAULT_MONTHLY["free"]))
    st = await ai_budget.status(billing, biz.user_id)
    assert st["near_limit"] and not st["exceeded"]


@pytest.mark.asyncio
async def test_one_owners_spend_never_counts_against_another(billing):
    a, b = _Owned(), _Owned()
    await _spend(billing, a, ai_budget.DEFAULT_MONTHLY["free"])
    assert (await ai_budget.status(billing, a.user_id))["exceeded"]
    assert (await ai_budget.status(billing, b.user_id))["used"] == 0


@pytest.mark.asyncio
async def test_a_plan_can_set_its_own_cap_and_unlimited_is_unlimited(billing):
    biz = _Owned()
    plan = SubscriptionPlan(name="Pro", slug="pro", limits={ai_budget.METRIC: 1000}, features=[])
    billing.add(plan)
    await billing.commit()
    billing.add(Subscription(user_id=biz.user_id, plan_id=plan.id, status=SubscriptionStatus.ACTIVE))
    await billing.commit()
    assert await ai_budget.monthly_limit(billing, biz.user_id) == 1000
    plan.limits = {ai_budget.METRIC: -1}
    await billing.commit()
    assert await ai_budget.monthly_limit(billing, biz.user_id) == -1
    await _spend(billing, biz, 10**7)  # still allowed
    assert not (await ai_budget.status(billing, biz.user_id))["exceeded"]


@pytest.mark.asyncio
async def test_a_plan_without_the_metric_falls_back_to_its_slug_default(billing):
    biz = _Owned()
    plan = SubscriptionPlan(name="Starter", slug="starter", limits={}, features=[])
    billing.add(plan)
    await billing.commit()
    billing.add(Subscription(user_id=biz.user_id, plan_id=plan.id, status=SubscriptionStatus.ACTIVE))
    await billing.commit()
    assert await ai_budget.monthly_limit(billing, biz.user_id) == ai_budget.DEFAULT_MONTHLY["starter"]


@pytest.mark.asyncio
async def test_billing_trouble_fails_open(db):
    biz = _Owned()  # no billing tables at all
    assert await ai_budget.monthly_limit(db, biz.user_id) == -1
    async with ai_budget.metered(db, biz):  # must not raise
        ai_budget.record_tokens(10)


@pytest.mark.asyncio
async def test_a_business_without_an_owner_is_simply_not_metered(billing):
    async with ai_budget.metered(billing, _Biz()) as meter:
        ai_budget.record_tokens(10)
    assert meter.tokens == 0


# ── the model client feeds the meter ──────────────────────────────────────
@pytest.mark.asyncio
async def test_the_model_client_reports_the_tokens_the_api_says_it_used(monkeypatch, billing):
    class _Messages:
        async def create(self, **kw):
            block = types.SimpleNamespace(type="text", text='{"subject": "hola", "body": "x"}')
            return types.SimpleNamespace(content=[block], usage=types.SimpleNamespace(input_tokens=700, output_tokens=150))

    class _Client:
        def __init__(self, **kw):
            self.messages = _Messages()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(AsyncAnthropic=_Client))
    monkeypatch.setattr(llm, "_api_key", lambda: "test-key")
    biz = _Owned()
    async with ai_budget.metered(billing, biz) as meter:
        out = await llm.ask_json("sys", "prompt")
    assert out == {"subject": "hola", "body": "x"} and meter.tokens == 850
    assert await _used(billing, biz.user_id) == 850


# ── what each feature does when the month is used up ──────────────────────
@pytest.mark.asyncio
async def test_drafting_stops_with_a_clear_429_and_never_calls_the_model(billing, monkeypatch):
    biz = _Owned()
    svc, biz, profile, prospect = await _setup(billing, biz)
    await _spend(billing, biz, ai_budget.DEFAULT_MONTHLY["free"])

    async def boom(*a, **k):
        raise AssertionError("model called")

    monkeypatch.setattr(harvey_service, "ask_json", boom)
    monkeypatch.setattr(harvey_service, "llm_available", lambda: True)
    with pytest.raises(HarveyError) as e:
        await svc.draft_first_email(biz, profile, prospect)
    assert e.value.status_code == 429 and "límite de IA" in str(e.value)


@pytest.mark.asyncio
async def test_a_reply_still_gets_recorded_and_goes_to_a_person_when_the_month_is_used_up(billing, monkeypatch):
    biz = _Owned()
    svc, biz, profile, prospect = await _setup(billing, biz)
    await _spend(billing, biz, ai_budget.DEFAULT_MONTHLY["free"])

    async def boom(*a, **k):
        raise AssertionError("model called")

    monkeypatch.setattr(harvey_service, "ask_json", boom)
    reply = await svc.record_reply(biz, profile, prospect, "¿Podemos hablar del precio?")
    assert reply.classification == "handoff" and reply.needs_human


@pytest.mark.asyncio
async def test_a_normal_draft_is_metered_through_the_service(billing, monkeypatch):
    biz = _Owned()
    svc, biz, profile, prospect = await _setup(billing, biz)

    async def fake(system, prompt, **kw):
        ai_budget.record_tokens(900)  # what the real client does with the API's usage numbers
        return {"subject": "hola", "body": "¿Cómo reciben pedidos?"}

    monkeypatch.setattr(harvey_service, "ask_json", fake)
    monkeypatch.setattr(harvey_service, "llm_available", lambda: True)
    await svc.draft_first_email(biz, profile, prospect)
    assert await _used(billing, biz.user_id) == 900


@pytest.mark.asyncio
async def test_the_website_suggestion_falls_back_to_the_sites_own_words(billing, monkeypatch):
    biz = _Owned()
    await _spend(billing, biz, ai_budget.DEFAULT_MONTHLY["free"])

    async def boom(*a, **k):
        raise AssertionError("model called")

    async def fake_site(client, url):
        return {"url": "https://x.com", "title": "X", "description": "Pan artesanal", "headlines": ["Pan"], "text": "t"}

    monkeypatch.setattr(onboarding, "ask_json", boom)
    monkeypatch.setattr(onboarding, "llm_available", lambda: True)
    monkeypatch.setattr(onboarding, "read_site", fake_site)
    out = await onboarding.suggest("x.com", "X", db=billing, business=biz)
    assert out["source"] == "facts" and out["offer"] == "Pan artesanal"


@pytest.mark.asyncio
async def test_the_status_reports_the_allowance(billing):
    biz = _Owned()
    svc, biz, profile, prospect = await _setup(billing, biz)
    await _spend(billing, biz, 5000)
    st = await svc.status(biz, profile)
    assert st["ai_budget"]["used"] == 5000 and st["ai_budget"]["limit"] == ai_budget.DEFAULT_MONTHLY["free"]


def test_the_weekly_summary_warns_before_and_after_the_cap():
    from app.domains.harvey import weekly

    base = {
        "sent": 0, "prospects_total": 5, "prospects_new": 0, "pending_review": 0, "needs_you": 0,
        "replies": {"total": 0}, "deals": {"won": 0}, "meetings": 0,
    }
    near = weekly.next_steps({**base, "ai_budget": {"near_limit": True, "exceeded": False, "percent": 85}})
    assert any("85%" in t for t in near)
    out = weekly.next_steps({**base, "ai_budget": {"near_limit": True, "exceeded": True, "percent": 100}})
    assert any("se terminó la ia" in t.lower() for t in out) and not any("85%" in t for t in out)
    assert weekly.next_steps({**base, "ai_budget": None}) == []
