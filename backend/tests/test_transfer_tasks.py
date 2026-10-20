"""The bank-transfer Celery tasks must run, and remind each order once.

``send_transfer_reminders`` and ``expire_pending_transfers`` did ``select(BankTransferPayment, User).join(User)``;
``bank_transfer_payments`` has two foreign keys to ``users`` (``user_id`` and ``confirmed_by_admin_id``), so
SQLAlchemy raised ``AmbiguousForeignKeysError`` on every run. Once that works, the reminder must not become
a new flood: the task runs every 6 hours and has no "reminded" column, so it only looks at orders that expire
in the 6-hour window (18 h, 24 h].
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

NOW = datetime.now(timezone.utc)


@pytest.fixture
async def orders(db_session):
    """Create users and bank-transfer orders; deletes them afterwards."""
    from app.domains.subscriptions.models import BankTransferPayment
    from app.domains.users.models import User

    users: list[uuid.UUID] = []
    created: list[uuid.UUID] = []
    emails: dict[uuid.UUID, str] = {}

    async def make(*, expires_in: timedelta, status: str = "pending") -> uuid.UUID:
        email = f"buyer-{uuid.uuid4().hex[:10]}@example.com"
        user = User(id=uuid.uuid4(), email=email, hashed_password="x", full_name="Buyer", is_active=True)
        db_session.add(user)
        await db_session.flush()
        users.append(user.id)
        order = BankTransferPayment(
            user_id=user.id, amount=100, currency="ARS", order_number=f"TR-{uuid.uuid4().hex[:10]}",
            status=status, expires_at=NOW + expires_in,
        )
        db_session.add(order)
        await db_session.commit()
        created.append(order.id)
        emails[order.id] = email
        return order.id

    make.emails = emails
    yield make
    await db_session.execute(BankTransferPayment.__table__.delete().where(BankTransferPayment.id.in_(created)))
    await db_session.execute(User.__table__.delete().where(User.id.in_(users)))
    await db_session.commit()


@pytest.fixture
def sent_emails(monkeypatch):
    from app.core import email_service

    sent: list[str] = []

    async def fake_send_email(to, subject, html, text=None, *args, **kwargs):
        sent.append(to)
        return True

    monkeypatch.setattr(email_service, "send_email", fake_send_email)
    return sent


async def _run(task) -> None:
    await asyncio.to_thread(task.run)  # a worker thread has no running loop, like a Celery process


async def _status(db, order_id) -> str:
    from app.domains.subscriptions.models import BankTransferPayment

    db.expire_all()
    return (await db.execute(select(BankTransferPayment.status).where(BankTransferPayment.id == order_id))).scalar_one()


async def test_expire_marks_overdue_pending_orders_and_tells_the_buyer(db_session, orders, sent_emails) -> None:
    from app.tasks.subscription_tasks import expire_pending_transfers

    overdue = await orders(expires_in=timedelta(hours=-1))
    still_open = await orders(expires_in=timedelta(hours=5))
    confirmed = await orders(expires_in=timedelta(hours=-1), status="confirmed")

    await _run(expire_pending_transfers)

    assert await _status(db_session, overdue) == "expired"
    assert await _status(db_session, still_open) == "pending"
    assert await _status(db_session, confirmed) == "confirmed"       # only pending orders expire
    assert sent_emails == [orders.emails[overdue]]


async def test_expire_twice_does_not_notify_twice(db_session, orders, sent_emails) -> None:
    from app.tasks.subscription_tasks import expire_pending_transfers

    overdue = await orders(expires_in=timedelta(hours=-1))
    await _run(expire_pending_transfers)
    await _run(expire_pending_transfers)

    assert sent_emails == [orders.emails[overdue]]


async def test_reminder_goes_to_orders_expiring_in_the_last_day_window_only(db_session, orders, sent_emails) -> None:
    from app.tasks.subscription_tasks import send_transfer_reminders

    in_window = await orders(expires_in=timedelta(hours=20))      # in (18 h, 24 h]: reminded
    await orders(expires_in=timedelta(hours=30))      # too early
    await orders(expires_in=timedelta(hours=10))      # its window already passed
    await orders(expires_in=timedelta(hours=-2))      # already overdue: the expiry task handles it

    await _run(send_transfer_reminders)

    assert sent_emails == [orders.emails[in_window]]


async def test_an_order_is_reminded_once_across_the_four_runs_of_its_last_day(db_session, orders, sent_emails) -> None:
    """Runs are 6 hours apart: as the expiry gets closer the same order must be reminded only once."""
    from app.domains.subscriptions.models import BankTransferPayment
    from app.tasks.subscription_tasks import send_transfer_reminders

    order_id = await orders(expires_in=timedelta(hours=23))
    for hours_left in (23, 17, 11, 5):      # what each of the 4 consecutive runs sees
        await db_session.execute(
            update(BankTransferPayment).where(BankTransferPayment.id == order_id)
            .values(expires_at=datetime.now(timezone.utc) + timedelta(hours=hours_left))
        )
        await db_session.commit()
        await _run(send_transfer_reminders)

    assert sent_emails == [orders.emails[order_id]]
