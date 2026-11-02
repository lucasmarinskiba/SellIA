"""The voice dashboard's endpoints: the signed-in user's own calls, in the shape the page reads.

The page used to call /voice/calls/user/{id} and /voice/analytics/{id}. The first did not exist, and the
second took a business id, not a user id. These tests go through HTTP with a real login and a real database.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest


@pytest.fixture
async def business(db_session, test_user):
    from app.domains.businesses.models import Business

    row = Business(user_id=test_user.id, name=f"Dashboard {uuid.uuid4().hex[:6]}")
    db_session.add(row)
    await db_session.commit()
    business_id = row.id
    yield row
    from app.domains.voice.models import AIAgentVoiceCall

    await db_session.execute(AIAgentVoiceCall.__table__.delete().where(AIAgentVoiceCall.business_id == business_id))
    await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
    await db_session.commit()


async def _add_call(db, business_id, *, status="completed", duration=None, sentiment=None, phone="+5491100000001", direction="outbound"):
    from app.domains.voice.models import AIAgentVoiceCall

    extra = {"sentiment": sentiment} if sentiment else {}
    db.add(
        AIAgentVoiceCall(
            business_id=business_id,
            customer_id=uuid.uuid4(),
            phone_number=phone,
            direction=direction,
            status=status,
            recording_duration=duration,
            extra_data=extra,
            created_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()


async def test_the_dashboard_gets_its_calls_in_the_shape_it_reads(db_session, async_client, auth_headers, test_user, business) -> None:
    await _add_call(db_session, business.id, duration=90, sentiment="positive", phone="+5491100000001", direction="outbound")

    response = await async_client.get(f"/api/v1/voice/calls/user/{test_user.id}", params={"limit": 20}, headers=auth_headers)

    assert response.status_code == 200, response.text
    calls = response.json()["calls"]
    assert len(calls) == 1
    assert calls[0]["contact_number"] == "+5491100000001"
    assert calls[0]["call_type"] == "outbound"
    assert calls[0]["duration_seconds"] == 90
    assert calls[0]["sentiment"] == "positive"


async def test_a_user_cannot_read_another_users_calls(async_client, auth_headers) -> None:
    response = await async_client.get(f"/api/v1/voice/calls/user/{uuid.uuid4()}", headers=auth_headers)

    assert response.status_code == 403, response.text


async def test_no_login_no_calls(async_client, test_user) -> None:
    response = await async_client.get(f"/api/v1/voice/calls/user/{test_user.id}")

    assert response.status_code in (401, 403), response.text


async def test_analytics_count_the_completed_calls_and_their_duration(db_session, async_client, auth_headers, test_user, business) -> None:
    await _add_call(db_session, business.id, status="completed", duration=60, sentiment="positive")
    await _add_call(db_session, business.id, status="failed", duration=None)

    response = await async_client.get(f"/api/v1/voice/analytics/user/{test_user.id}", headers=auth_headers)

    assert response.status_code == 200, response.text
    analytics = response.json()["analytics"]
    assert analytics["total_calls"] == 2
    assert analytics["completed_calls"] == 1
    assert analytics["completion_rate"] == 0.5
    assert analytics["avg_duration_seconds"] == 60.0
    assert analytics["avg_sentiment_score"] == 1.0


async def test_no_sentiment_on_any_call_means_no_score_not_zero(db_session, async_client, auth_headers, test_user, business) -> None:
    """The page shows the score as a percentage. With no labelled call it must show nothing, not 0%."""
    await _add_call(db_session, business.id, status="completed", duration=30)

    response = await async_client.get(f"/api/v1/voice/analytics/user/{test_user.id}", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert response.json()["analytics"]["avg_sentiment_score"] is None


async def test_no_calls_gives_zero_totals_and_an_empty_list(async_client, auth_headers, test_user) -> None:
    calls = await async_client.get(f"/api/v1/voice/calls/user/{test_user.id}", headers=auth_headers)
    analytics = await async_client.get(f"/api/v1/voice/analytics/user/{test_user.id}", headers=auth_headers)

    assert calls.status_code == 200 and calls.json()["calls"] == []
    assert analytics.status_code == 200
    assert analytics.json()["analytics"]["total_calls"] == 0
