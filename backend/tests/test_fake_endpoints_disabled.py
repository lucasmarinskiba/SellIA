"""Los endpoints que devolvían datos de muestra o un éxito falso responden 501.

Si alguien vuelve a poner un valor fijo o un "success" sin trabajo real detrás,
estos tests fallan. El handshake de URL de Slack sí es protocolo real y se prueba aparte.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)
HEADERS = {"account-id": "acc_test", "x-hub-signature": "sha256=test"}  # FastAPI mapea account_id a account-id
CONFIG = {"platform_type": "tiktok_shop", "api_key": "key_test", "webhook_url": "https://example.com/hook"}
ALERT = {"title": "Aviso", "message": "Mensaje de prueba"}
SHOP = "/api/v1/platforms"
MARKET = "/api/v1/marketplace-expansion"


@pytest.mark.parametrize(
    "method, path, kwargs",
    [
        # marketplace-expansion
        ("GET", f"{MARKET}/platforms/performance", {"params": {"seller_id": "s1"}}),
        ("GET", f"{MARKET}/opportunities/analyze", {"params": {"seller_id": "s1"}}),
        ("POST", f"{MARKET}/inventory/sync-strategy", {"params": {"seller_id": "s1"}}),
        # sync y métricas de tiendas
        ("POST", f"{SHOP}/facebook-shop/sync/products", {"headers": HEADERS, "json": {"platform_type": "facebook_shop"}}),
        ("GET", f"{SHOP}/facebook-shop/orders/order_1", {"headers": HEADERS}),
        ("POST", f"{SHOP}/instagram-shop/sync/products", {"headers": HEADERS, "json": {"platform_type": "instagram_shop"}}),
        ("GET", f"{SHOP}/instagram-shop/analytics", {"headers": HEADERS}),
        # webhooks y configuración sin procesar
        ("POST", f"{SHOP}/facebook-shop/webhooks/orders", {"headers": HEADERS, "json": {}}),
        ("POST", f"{SHOP}/facebook-shop/config", {"headers": HEADERS, "json": {**CONFIG, "platform_type": "facebook_shop"}}),
        ("POST", f"{SHOP}/instagram-shop/webhooks/orders", {"headers": HEADERS, "json": {}}),
        ("POST", f"{SHOP}/tiktok-shop/webhooks/orders", {"headers": HEADERS, "json": {}}),
        ("POST", f"{SHOP}/tiktok-shop/config", {"headers": HEADERS, "json": CONFIG}),
        # calendly, slack y telegram
        ("POST", f"{SHOP}/calendly/webhooks/events", {"headers": HEADERS, "json": {}}),
        ("POST", f"{SHOP}/calendly/config", {"headers": HEADERS, "json": {**CONFIG, "platform_type": "calendly"}}),
        ("GET", f"{SHOP}/calendly/events", {"headers": HEADERS}),
        ("POST", f"{SHOP}/slack/commands", {"headers": HEADERS, "json": {}}),
        ("POST", f"{SHOP}/slack/alerts", {"headers": HEADERS, "json": ALERT}),
        ("POST", f"{SHOP}/slack/events", {"headers": HEADERS, "json": {"type": "event_callback"}}),
        ("POST", f"{SHOP}/telegram/webhooks/updates", {"headers": HEADERS, "json": {}}),
        ("POST", f"{SHOP}/telegram/config", {"headers": HEADERS, "json": {**CONFIG, "platform_type": "telegram"}}),
        ("POST", f"{SHOP}/telegram/send-notification", {"headers": HEADERS, "json": ALERT}),
    ],
)
def test_fake_endpoint_answers_501_not_fixed_data(method, path, kwargs):
    response = client.request(method, path, **kwargs)

    assert response.status_code == 501, response.text
    assert "detail" in response.json()


def test_slack_url_verification_still_answers_the_challenge():
    response = client.post(
        f"{SHOP}/slack/events",
        headers=HEADERS,
        json={"type": "url_verification", "challenge": "abc123"},
    )

    assert response.status_code == 200
    assert response.json() == {"challenge": "abc123"}


def test_health_does_not_claim_every_platform_is_ok():
    response = client.get(f"{SHOP}/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unknown"
    assert set(body["platforms"].values()) == {"unknown"}
