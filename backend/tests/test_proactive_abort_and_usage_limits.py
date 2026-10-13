"""Two Celery task bugs seen in the production worker logs.

* ``detect_opportunities_task``: one detector failed (``relation "customer_memories" does
  not exist``), the error was swallowed without leaving the transaction in a usable state,
  and every detector after it, then every one of the 55 other businesses in the same run,
  failed with ``InFailedSQLTransactionError`` (56 tracebacks in one second).
* ``check_usage_alerts``: ``TypeError: '<=' not supported between instances of 'str' and
  'int'``. ``SubscriptionPlan.limits`` mixes numbers, booleans and text, and the task
  treated every entry as a numeric quota.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError


@pytest.fixture
async def business(db_session, test_user):
    from app.domains.businesses.models import Business

    b = Business(user_id=test_user.id, name=f"Proactive Co {uuid.uuid4().hex[:6]}")
    db_session.add(b)
    await db_session.commit()
    yield b
    await db_session.delete(b)
    await db_session.commit()


# ── proactive: a failed detector must not poison the session ─────────────────

async def test_a_failed_sql_statement_aborts_the_shared_transaction(db_session) -> None:
    """The database fact behind the cascade: after one failure, every statement fails."""
    with pytest.raises(DBAPIError):
        await db_session.execute(text("select * from a_table_that_does_not_exist"))
    with pytest.raises(DBAPIError, match="InFailedSQLTransactionError|current transaction is aborted"):
        await db_session.execute(text("select 1"))
    await db_session.rollback()


async def test_one_failing_detector_does_not_stop_the_others_or_expire_loaded_rules(
    db_session, business
) -> None:
    from app.domains.proactive.engine import ProactiveEngine
    from app.domains.proactive.models import OutreachRule

    rule = OutreachRule(
        business_id=business.id, rule_name="re-engage", rule_type="re_engagement",
        conditions={"inactive_days": 45}, message_template="hola", channel="whatsapp",
    )
    db_session.add(rule)
    await db_session.commit()

    engine = ProactiveEngine(db_session)
    ran: list[str] = []
    seen_conditions: list[dict] = []

    async def missing_table(business_id, rules_by_type):
        ran.append("product_recommendation")
        await db_session.execute(text("select * from customer_memories_that_does_not_exist"))

    def healthy(name: str):
        async def detector(business_id, rules_by_type):
            await db_session.execute(text("select 1"))  # raises if the transaction is aborted
            # Reads an ORM object loaded BEFORE the failure: a plain rollback() would expire it.
            for loaded in rules_by_type.get("re_engagement", []):
                seen_conditions.append(loaded.conditions)
            ran.append(name)
            return []
        return detector

    engine._detect_cart_abandonment = healthy("cart_abandonment")
    engine._detect_re_engagement = healthy("re_engagement")
    engine._detect_product_recommendation = missing_table
    engine._detect_anniversary_birthday = healthy("anniversary")
    engine._detect_churn_risk = healthy("churn_risk")
    engine._detect_price_drop_back_in_stock = healthy("price_drop")

    await engine.detect_opportunities(business.id)

    assert ran == [
        "cart_abandonment", "re_engagement", "product_recommendation",
        "anniversary", "churn_risk", "price_drop",
    ], "detectors after the failing one must still run"
    # each of the 5 healthy detectors read the rule loaded before the failure, none hit an
    # expired instance
    assert seen_conditions == [{"inactive_days": 45}] * 5

    # and the session is still healthy for the next business in the loop
    assert (await db_session.execute(text("select 1"))).scalar_one() == 1
    assert (await db_session.execute(select(OutreachRule).where(OutreachRule.id == rule.id))).scalar_one()

    await db_session.delete(rule)
    await db_session.commit()


# ── usage alerts: only real numeric quotas are limits ────────────────────────

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (100, 100), (2000, 2000), (1.0, 1.0),        # quotas (counts, decimals)
        (-1, None), (0, None),                        # unlimited / not included
        (True, None), (False, None),                  # flags, not quotas
        ("1024x1024", None), ("unlimited", None),     # text settings
        (None, None), ([], None), ({}, None),
    ],
)
def test_usage_limit_only_accepts_real_numeric_quotas(value, expected) -> None:
    from app.tasks.subscription_tasks import _usage_limit

    assert _usage_limit(value) == expected


async def test_usage_alert_task_logic_survives_a_plan_with_mixed_limit_types(db_session, test_user) -> None:
    from app.domains.subscriptions.models import (
        Subscription,
        SubscriptionPlan,
        SubscriptionStatus,
        UsageAlert,
        UsageTracking,
    )
    from app.tasks.subscription_tasks import _check_usage_alerts

    plan = SubscriptionPlan(
        name="Mixed", slug=f"mixed-{uuid.uuid4().hex[:8]}",
        limits={
            "conversations_per_month": 100,              # 90 used -> crosses 80%
            "storage_mb": -1,                            # unlimited
            "shipments_per_month": 0,                    # not included
            "multi_business": True,                      # flag
            "content_max_image_resolution": "1024x1024",  # text: this one raised TypeError
            "content_daily_budget_usd": 1.0,             # decimal quota, no usage recorded
        },
    )
    db_session.add(plan)
    await db_session.flush()
    sub = Subscription(user_id=test_user.id, plan_id=plan.id, status=SubscriptionStatus.ACTIVE)
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    usage = UsageTracking(
        user_id=test_user.id, metric_type="conversations_per_month", quantity=90, period_month=month,
    )
    db_session.add_all([sub, usage])
    await db_session.commit()

    await _check_usage_alerts(db_session)  # used to raise TypeError

    alerts = (await db_session.execute(select(UsageAlert).where(UsageAlert.user_id == test_user.id))).scalars().all()
    assert [(a.metric_type, a.threshold_percent) for a in alerts] == [("conversations_per_month", 80)]

    for row in (*alerts, usage, sub, plan):
        await db_session.delete(row)
    await db_session.commit()
