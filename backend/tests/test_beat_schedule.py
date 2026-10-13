"""Beat calendar: long-interval tasks must run at fixed times, not "N seconds after last run".

``backend/celerybeat-schedule`` (beat's state file) was committed with last-run times from
May. Beat read it on every start, decided every task was long overdue and sent ~50 of them
at once (weekly report, dunning, token rotation, ...) on each deploy. Interval schedules
depend on that file surviving; crontab entries do not, so everything of an hour or more is
now absolute, and the file is no longer in the image.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from celery.schedules import crontab

REPO_ROOT = Path(__file__).resolve().parents[2]

# What every entry of an hour or more used to be, in seconds. The new calendar must keep
# (about) the same number of runs; a change of cadence is a decision, not a side effect.
OLD_INTERVALS: dict[str, float] = {
    **{n: 3600.0 for n in (
        "check-deals-stalled", "check-no-reply", "request-pending-confirmations", "payment-reminder-check",
        "cleanup-expired-ip-blocks", "fatigue-score-recalculation", "auto-close-evaluator",
        "pipeline-automation-trigger-scanner", "brand-transformation-automations",
        "summarize-conversations-hourly", "update-deal-scores", "check-ab-test-winners")},
    "finance-reconcile": 7200.0,
    "ledger-bank-reconciliation": 10800.0,
    **{n: 21600.0 for n in (
        "check-hot-leads-no-deal", "check-expiring-subscriptions", "send-transfer-reminders",
        "expire-pending-transfers", "sync-mercadopago-preapprovals", "director-executive-loop",
        "auto-resolve-tickets", "generate-fomo-cadence")},
    **{n: 86400.0 for n in (
        "check-abandoned-carts", "auto-generate-catalog-content", "cleanup-old-generated-content",
        "generate-recurring-invoices", "selia-director-daily", "rfm-segmentation", "bi-analytics-daily",
        "autopilot-daily-report-generator", "health-score-recalculation", "churn-prevention-activator",
        "proactive-outreach-scheduler", "briefing-delivery", "churn-shield-analysis", "generate-support-stats",
        "finance-auto-deliver", "finance-dunning", "finance-cash-flow", "ledger-month-close", "ad-budget-cycles",
        "forecasting-nightly", "deep-system-optimization", "daily-growth-cycle", "fetch-nightly-analytics",
        "monitor-fomo-decay", "compute-positioning-scores", "compute-store-positioning-scores")},
    **{n: 604800.0 for n in (
        "weekly-authority-snapshot", "analyze-content-performance", "data-retention-cleanup",
        "security-audit-report", "experiment-evaluator", "auto-optimizer-runner", "ab-test-winner-applier",
        "forecasting-accuracy-weekly", "weekly-executive-report", "send-upsell-campaigns",
        "compute-analytics-summaries")},
    "send-follow-ups": 259200.0,
    "send-winback-campaigns": 1209600.0,
    "rotate-webhook-tokens": 7776000.0,
}


@pytest.fixture(scope="module")
def beat() -> dict:
    from app.tasks.celery_app import celery_app

    return celery_app.conf.beat_schedule


def _midnight() -> datetime:
    from app.tasks.celery_app import celery_app

    return celery_app.now().replace(hour=0, minute=0, second=0, microsecond=0)


def _runs(entry: crontab, start: datetime, days: int) -> list[datetime]:
    """Every time ``entry`` fires in ``[start, start + days)``, found the way beat finds them."""
    end, out, cursor = start + timedelta(days=days), [], start
    while True:
        last, delta, _now = entry.remaining_delta(cursor)  # delta is relative to ``cursor``, not to the wall clock
        cursor = last + delta
        if cursor >= end:
            return out
        out.append(cursor)
        cursor += timedelta(seconds=1)


def test_nothing_of_an_hour_or_more_is_a_plain_interval(beat) -> None:
    offenders = sorted(
        n for n, e in beat.items() if not isinstance(e["schedule"], crontab) and e["schedule"] >= 3600
    )
    assert not offenders, f"use crontab for: {offenders}"


def test_every_previous_long_interval_entry_still_exists_as_crontab(beat) -> None:
    missing = sorted(set(OLD_INTERVALS) - set(beat))
    not_cron = sorted(n for n in OLD_INTERVALS if n in beat and not isinstance(beat[n]["schedule"], crontab))
    assert not missing and not not_cron, (missing, not_cron)


def test_short_intervals_are_left_as_they_were(beat) -> None:
    short = {n: e["schedule"] for n, e in beat.items() if not isinstance(e["schedule"], crontab)}
    assert short, "polling tasks are expected to stay intervals"
    assert all(isinstance(v, (int, float)) and v < 3600 for v in short.values()), short


def test_a_fresh_start_has_nothing_due(beat) -> None:
    """The reported incident. A beat with no state starts 'now'; no crontab entry may be due."""
    from app.tasks.celery_app import celery_app

    now = celery_app.now()
    due = [n for n, e in beat.items() if isinstance(e["schedule"], crontab) and e["schedule"].is_due(now)[0]]
    assert due == []


@pytest.mark.parametrize("name", sorted(OLD_INTERVALS))
def test_runs_per_period_match_the_old_interval(beat, name: str) -> None:
    days = 400
    got = len(_runs(beat[name]["schedule"], _midnight(), days))
    expected = days * 86400 / OLD_INTERVALS[name]
    assert expected * 0.85 <= got <= expected * 1.2, f"{name}: {got} runs in {days} days, expected ~{expected:.1f}"


def test_work_is_spread_out_not_piled_on_one_minute(beat) -> None:
    per_minute: Counter = Counter()
    for entry in beat.values():
        if isinstance(entry["schedule"], crontab):
            per_minute.update(_runs(entry["schedule"], _midnight(), 120))
    worst_minute, count = per_minute.most_common(1)[0]
    assert count <= 6, f"{count} tasks at {worst_minute}"


def test_webhook_token_rotation_is_quarterly_and_fixed(beat) -> None:
    sched = beat["rotate-webhook-tokens"]["schedule"]
    assert sched.day_of_month == {1} and sched.month_of_year == {1, 4, 7, 10}


def test_weekly_executive_report_runs_on_mondays_at_8(beat) -> None:
    runs = _runs(beat["weekly-executive-report"]["schedule"], _midnight(), 60)
    assert runs and all(r.weekday() == 0 and (r.hour, r.minute) == (8, 0) for r in runs)


def test_task_arguments_survive_the_conversion(beat) -> None:
    assert beat["daily-growth-cycle"]["args"] == ({"name": "SellIA Pro", "price": 499, "niche": "sales"},)


def test_beat_does_not_read_a_schedule_file_shipped_in_the_image() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile.celery-beat").read_text(encoding="utf-8")
    cmd = re.search(r"^CMD (.+)$", dockerfile, re.MULTILINE)
    assert cmd and '"--schedule", "/tmp/celerybeat-schedule"' in cmd.group(1)
    assert "celerybeat-schedule*" in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
