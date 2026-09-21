"""Signup must work on a database created from the models (fresh install / CI).

The endpoint uses a hand-written INSERT, so a NOT NULL column added to the User
model without a server default breaks it on fresh databases, while existing
databases keep working because the startup ALTERs (app/sellbot.py) add those
columns with a DEFAULT. This regression test runs against a freshly created
schema, which is what the E2E job and every new environment get.
"""

import uuid

import httpx


async def test_signup_succeeds_on_fresh_schema(async_client: httpx.AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"signup-{uuid.uuid4().hex[:8]}@test.local",
            "password": "E2eTest-123!",
            "full_name": "Signup Test",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user_id"]
    assert body["access_token"]
