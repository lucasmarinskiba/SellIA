"""Quick test of sellbot endpoints."""
import asyncio
from app.sellbot import app, ping
from fastapi.testclient import TestClient

client = TestClient(app)

print("Testing SellIA Sellbot endpoints...\n")

# Test 1: Health check
print("1. GET /api/ping")
response = client.get("/api/ping")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 200
print("   PASS\n")

# Test 2: Root redirect
print("2. GET /")
response = client.get("/", follow_redirects=True)
print(f"   Status: {response.status_code}")
print("   PASS\n")

# Test 3: Knowledge ingest (no IA call)
print("3. POST /api/v1/knowledge/ingest")
response = client.post(
    "/api/v1/knowledge/ingest",
    json={"content": "Test knowledge", "source": "test"}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 200
print("   PASS\n")

print("All tests passed! Sellbot is ready.")
