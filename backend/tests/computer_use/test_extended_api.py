"""Tests para Computer Use Extended API"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.domains.computer_use.models_extended import (
    ComputerUseTemplate, ComputerUseScheduledTask, ComputerUseAnnotation,
    ComputerUseBrowserProfile, ComputerUseProxyConfig, ComputerUseSessionShare,
    ComputerUseBatchJob, ComputerUseSessionTag, ComputerUseWebhook,
)


@pytest.mark.asyncio
async def test_create_template(auth_client, db_session, test_user):
    response = await auth_client.post(
        "/api/v1/computer-use/templates",
        json={
            "name": "Test Template",
            "task_description": "Test task",
            "start_url": "https://example.com",
            "tags": ["test", "demo"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Template"
    assert data["task_description"] == "Test task"


@pytest.mark.asyncio
async def test_list_templates(auth_client, db_session, test_user):
    # Create template
    template = ComputerUseTemplate(
        user_id=test_user.id,
        name="My Template",
        task_description="Do something",
    )
    db_session.add(template)
    await db_session.commit()

    response = await auth_client.get("/api/v1/computer-use/templates")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_create_annotation(auth_client, db_session, test_user):
    # Create session first
    from app.domains.computer_use.models import ComputerUseSession
    session = ComputerUseSession(
        user_id=test_user.id,
        task_description="Test",
        status="completed",
    )
    db_session.add(session)
    await db_session.commit()

    response = await auth_client.post(
        f"/api/v1/computer-use/sessions/{session.id}/annotations",
        json={"step_number": 1, "content": "This is important", "color": "#ff0000"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "This is important"
    assert data["step_number"] == 1


@pytest.mark.asyncio
async def test_list_annotations(auth_client, db_session, test_user):
    from app.domains.computer_use.models import ComputerUseSession
    session = ComputerUseSession(
        user_id=test_user.id,
        task_description="Test",
        status="completed",
    )
    db_session.add(session)
    await db_session.commit()

    ann = ComputerUseAnnotation(
        session_id=session.id,
        step_number=1,
        user_id=test_user.id,
        content="Note 1",
    )
    db_session.add(ann)
    await db_session.commit()

    response = await auth_client.get(
        f"/api/v1/computer-use/sessions/{session.id}/annotations",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Note 1"


@pytest.mark.asyncio
async def test_create_browser_profile(auth_client, db_session, test_user):
    response = await auth_client.post(
        "/api/v1/computer-use/browser-profiles",
        json={
            "name": "Mobile Profile",
            "viewport_width": 375,
            "viewport_height": 667,
            "user_agent": "Mozilla/5.0 (iPhone...)",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Mobile Profile"
    assert data["viewport_width"] == 375


@pytest.mark.asyncio
async def test_create_batch_job(auth_client, db_session, test_user):
    response = await auth_client.post(
        "/api/v1/computer-use/batch-jobs",
        json={
            "name": "Scrape Products",
            "task_description": "Extract product info",
            "urls": ["https://site1.com", "https://site2.com", "https://site3.com"],
            "concurrency": 2,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Scrape Products"
    assert data["total_count"] == 3
    assert data["concurrency"] == 2


@pytest.mark.asyncio
async def test_add_session_tag(auth_client, db_session, test_user):
    from app.domains.computer_use.models import ComputerUseSession
    session = ComputerUseSession(
        user_id=test_user.id,
        task_description="Test",
        status="completed",
    )
    db_session.add(session)
    await db_session.commit()

    response = await auth_client.post(
        f"/api/v1/computer-use/sessions/{session.id}/tags",
        json={"tag": "important", "color": "#ff0000"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tag"] == "important"


@pytest.mark.asyncio
async def test_search_by_tag(auth_client, db_session, test_user):
    from app.domains.computer_use.models import ComputerUseSession
    session = ComputerUseSession(
        user_id=test_user.id,
        task_description="Test task",
        status="completed",
    )
    db_session.add(session)
    await db_session.commit()

    tag = ComputerUseSessionTag(session_id=session.id, tag="demo", color="#3b82f6")
    db_session.add(tag)
    await db_session.commit()

    response = await auth_client.get("/api/v1/computer-use/tags/search?tag=demo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_webhook(auth_client, db_session, test_user):
    response = await auth_client.post(
        "/api/v1/computer-use/webhooks",
        json={
            "name": "My Webhook",
            "url": "https://example.com/webhook",
            "events": ["session.completed", "session.failed"],
            "secret": "mysecret",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Webhook"
    assert "session.completed" in data["events"]


@pytest.mark.asyncio
async def test_analytics_summary(auth_client, db_session, test_user):
    # Seed some data
    from app.domains.computer_use.models import ComputerUseSession
    for i in range(3):
        session = ComputerUseSession(
            user_id=test_user.id,
            task_description=f"Task {i}",
            status="completed" if i < 2 else "failed",
            total_steps=10,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        db_session.add(session)
    await db_session.commit()

    response = await auth_client.get("/api/v1/computer-use/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_sessions"] >= 3
    assert data["completed_sessions"] >= 2
    assert data["failed_sessions"] >= 1


@pytest.mark.asyncio
async def test_share_session(auth_client, db_session, test_user):
    from app.domains.computer_use.models import ComputerUseSession
    session = ComputerUseSession(
        user_id=test_user.id,
        task_description="Test",
        status="completed",
    )
    db_session.add(session)
    await db_session.commit()

    response = await auth_client.post(
        f"/api/v1/computer-use/sessions/{session.id}/shares",
        json={"permission": "view", "expires_days": 7},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["permission"] == "view"
    assert data["token"] is not None
    assert len(data["token"]) > 20
