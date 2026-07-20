"""Auth flow tests."""
import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_signup_returns_token(client, fake_signup_payload):
    r = await client.post("/v1/auth/signup", json=fake_signup_payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["access_token"]
    assert data["role"] == "owner"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_signup_duplicate_email_409(client, fake_signup_payload):
    r1 = await client.post("/v1/auth/signup", json=fake_signup_payload)
    assert r1.status_code == 201
    r2 = await client.post("/v1/auth/signup", json=fake_signup_payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_login_correct_password(client, fake_signup_payload):
    await client.post("/v1/auth/signup", json=fake_signup_payload)
    r = await client.post("/v1/auth/login", json={
        "email": fake_signup_payload["email"],
        "password": fake_signup_payload["password"],
    })
    assert r.status_code == 200
    assert r.json()["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_401(client, fake_signup_payload):
    await client.post("/v1/auth/signup", json=fake_signup_payload)
    r = await client.post("/v1/auth/login", json={
        "email": fake_signup_payload["email"],
        "password": "wrong-password",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint_requires_auth(client):
    r = await client.get("/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint_returns_user(client, fake_signup_payload):
    sig = await client.post("/v1/auth/signup", json=fake_signup_payload)
    token = sig.json()["access_token"]
    r = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "owner"
    assert body["tenant_id"]
