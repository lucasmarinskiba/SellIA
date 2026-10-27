"""Los endpoints que devolvían datos de muestra o un éxito falso responden 501.

Si alguien vuelve a poner un valor fijo o un "success" sin trabajo real detrás,
estos tests fallan.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)
SHOP_HEADERS = {"account-id": "acc_test"}  # FastAPI mapea account_id a account-id
SYNC_BODY = {"platform_type": "facebook_shop"}


@pytest.mark.parametrize(
    "method, path, kwargs",
    [
        ("GET", "/api/v1/marketplace-expansion/platforms/performance", {"params": {"seller_id": "s1"}}),
        ("GET", "/api/v1/marketplace-expansion/opportunities/analyze", {"params": {"seller_id": "s1"}}),
        ("POST", "/api/v1/marketplace-expansion/inventory/sync-strategy", {"params": {"seller_id": "s1"}}),
        ("POST", "/api/v1/platforms/facebook-shop/sync/products", {"headers": SHOP_HEADERS, "json": SYNC_BODY}),
        ("GET", "/api/v1/platforms/facebook-shop/orders/order_1", {"headers": SHOP_HEADERS}),
        ("POST", "/api/v1/platforms/instagram-shop/sync/products", {"headers": SHOP_HEADERS, "json": SYNC_BODY}),
        ("GET", "/api/v1/platforms/instagram-shop/analytics", {"headers": SHOP_HEADERS}),
    ],
)
def test_fake_endpoint_answers_501_not_fixed_data(method, path, kwargs):
    response = client.request(method, path, **kwargs)

    assert response.status_code == 501
    assert "detail" in response.json()
