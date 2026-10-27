"""Mercado Libre: publicación de productos, órdenes y renovación de token.

Sin red: la API de Mercado Libre se simula con httpx.MockTransport y la base de
datos con mocks. Lo que no se puede probar sin una cuenta real queda en la
descripción del PR.
"""

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.domains.catalogs import sync_service as sync_mod
from app.domains.catalogs.sync_service import CatalogSyncService
from app.domains.channels.connectors.mercadolibre import (
    MercadoLibreAPIError,
    MercadoLibreAuthError,
    MercadoLibreConnector,
    refresh_credentials,
)
from app.domains.channels.models import ChannelPlatform
from app.domains.orders import marketplace_orders as orders_mod
from app.domains.orders.models import OrderStatus, PaymentStatus

CREDS = {"access_token": "tok_1", "refresh_token": "ref_1", "seller_id": "555"}


def _connector(handler, creds=CREDS):
    return MercadoLibreConnector(creds, {}, transport=httpx.MockTransport(handler))


# ---------- conector: publicación ----------


async def test_create_product_posts_item_without_description_then_the_description():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (request.method, request.url.path, json.loads(request.content or b"{}"))
        )
        if request.url.path == "/items":
            return httpx.Response(
                201,
                json={
                    "id": "MLA123",
                    "permalink": "https://articulo.mercadolibre.com.ar/MLA-123",
                },
            )
        return httpx.Response(200, json={})

    result = await _connector(handler).create_product(
        {
            "title": "Remera",
            "category_id": "MLA1",
            "price": 1500.0,
            "description": {"plain_text": "Algodón peinado"},
        }
    )

    assert result == {
        "id": "MLA123",
        "permalink": "https://articulo.mercadolibre.com.ar/MLA-123",
    }
    assert seen[0][:2] == ("POST", "/items")
    assert "description" not in seen[0][2]
    assert seen[1] == (
        "POST",
        "/items/MLA123/description",
        {"plain_text": "Algodón peinado"},
    )


async def test_create_product_keeps_the_error_message_from_mercadolibre():
    def handler(request):
        return httpx.Response(
            400, json={"message": "category_id invalida", "error": "validation_error"}
        )

    with pytest.raises(MercadoLibreAPIError) as exc:
        await _connector(handler).create_product({"title": "x", "category_id": "MLA-?"})

    assert exc.value.status_code == 400
    assert exc.value.message == "category_id invalida"


async def test_expired_token_raises_auth_error_not_api_error():
    def handler(request):
        return httpx.Response(401, json={"message": "invalid_token"})

    with pytest.raises(MercadoLibreAuthError):
        await _connector(handler).create_product({"title": "x"})


async def test_update_item_sends_only_the_fields_that_are_set():
    seen = {}

    def handler(request):
        seen["method"], seen["path"] = request.method, request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "MLA123"})

    await _connector(handler).update_item(
        "MLA123", price=2000.0, available_quantity=None
    )

    assert (seen["method"], seen["path"]) == ("PUT", "/items/MLA123")
    assert seen["body"] == {"price": 2000.0}


async def test_list_orders_asks_for_the_seller_window_and_page():
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"results": [{"id": 1}], "paging": {}})

    since = datetime(2026, 10, 20, 12, 30, tzinfo=timezone.utc)
    orders = await _connector(handler).list_orders(since, limit=50, offset=100)

    assert orders == [{"id": 1}]
    assert seen["params"]["seller"] == "555"
    assert seen["params"]["sort"] == "date_desc"
    assert seen["params"]["offset"] == "100"
    assert seen["params"]["order.date_created.from"] == "2026-10-20T12:30:00.000-00:00"


async def test_refresh_credentials_keeps_the_old_refresh_token_when_ml_omits_a_new_one(
    monkeypatch,
):
    from app.core import oauth_connectors

    monkeypatch.setattr(
        oauth_connectors.MercadoLibreOAuth,
        "refresh_token",
        AsyncMock(return_value={"access_token": "tok_2"}),
    )

    new = await refresh_credentials(CREDS)

    assert new["access_token"] == "tok_2"
    assert new["refresh_token"] == "ref_1"
    assert new["seller_id"] == "555"


async def test_refresh_without_a_refresh_token_is_not_attempted():
    assert await refresh_credentials({"access_token": "tok_1"}) is None


# ---------- mapeo de catálogo -> item de Mercado Libre ----------


def _item(**overrides):
    base = dict(
        id=uuid.uuid4(),
        name="Remera",
        description="Algodón",
        price=Decimal("1500.00"),
        currency="ARS",
        stock=4,
        is_available=True,
        images=[],
        tags=[],
        extra_data={"ml_category_id": "MLA1051"},
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _format(item):
    return CatalogSyncService._item_to_platform_format(
        CatalogSyncService(AsyncMock()), item, ChannelPlatform.MERCADOLIBRE
    )


def test_ml_item_needs_an_explicit_category():
    with pytest.raises(ValueError, match="ml_category_id"):
        _format(_item(extra_data={}))


def test_ml_item_needs_a_known_stock():
    with pytest.raises(ValueError, match="stock"):
        _format(_item(stock=None))


def test_ml_item_uses_the_real_category_and_stock():
    payload = _format(_item())

    assert payload["category_id"] == "MLA1051"
    assert payload["available_quantity"] == 4
    assert payload["price"] == 1500.0


# ---------- órdenes ----------

ML_ORDER = {
    "id": 9001,
    "status": "paid",
    "total_amount": 3000,
    "currency_id": "ARS",
    "buyer": {"nickname": "COMPRADOR1", "email": "c@example.com"},
    "order_items": [
        {
            "item": {"title": "Remera", "seller_sku": "REM-M"},
            "quantity": 2,
            "unit_price": 1500,
        }
    ],
}


def test_paid_ml_order_maps_to_paid_and_completed_payment():
    fields = orders_mod.order_fields(ML_ORDER)

    assert fields["external_id"] == "9001"
    assert fields["external_platform"] == "mercadolibre"
    assert fields["status"] == OrderStatus.PAID
    assert fields["payment_status"] == PaymentStatus.COMPLETED
    assert fields["total_amount"] == Decimal("3000")
    assert fields["items"] == [
        {"name": "Remera", "qty": 2, "price": "1500", "sku": "REM-M"}
    ]


def _db_returning(row):
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    return db


async def test_upsert_creates_an_order_when_none_exists():
    db = _db_returning(None)
    business = uuid.uuid4()

    row = await orders_mod.upsert_order(db, business, ML_ORDER)

    db.add.assert_called_once_with(row)
    assert row.business_id == business
    assert row.external_id == "9001"


async def test_upsert_updates_status_of_an_existing_order_without_duplicating_it():
    existing = SimpleNamespace(
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        total_amount=0,
        currency="ARS",
        items=[],
        customer_name="",
        customer_email=None,
    )
    db = _db_returning(existing)

    row = await orders_mod.upsert_order(db, uuid.uuid4(), ML_ORDER)

    db.add.assert_not_called()
    assert row is existing
    assert existing.status == OrderStatus.PAID


class _FakeConnector:
    """Búsqueda de órdenes: 53 en total, de a 50 por página."""

    orders = [{**ML_ORDER, "id": i} for i in range(53)]
    calls: list = []

    def __init__(self, creds, settings):
        self.creds = creds

    async def list_orders(self, since=None, *, limit, offset):
        _FakeConnector.calls.append((offset, limit))
        return _FakeConnector.orders[offset : offset + limit]


def _channels_db(channel):
    db = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [channel]
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    return db


async def test_reconcile_reads_every_page_upserts_and_stamps_last_sync(monkeypatch):
    _FakeConnector.calls = []
    monkeypatch.setattr(orders_mod, "MercadoLibreConnector", _FakeConnector)
    channel = SimpleNamespace(
        id=uuid.uuid4(),
        business_id=uuid.uuid4(),
        credentials=CREDS,
        settings={},
        last_sync_at=None,
        is_active=True,
        platform=ChannelPlatform.MERCADOLIBRE,
    )
    upserted = []

    async def fake_upsert(db_, business_id, order):
        upserted.append(order["id"])

    monkeypatch.setattr(orders_mod, "upsert_order", fake_upsert)
    now = datetime(2026, 10, 21, 10, 0, tzinfo=timezone.utc)

    summary = await orders_mod.reconcile_mercadolibre_orders(
        _channels_db(channel), now=now
    )

    assert _FakeConnector.calls == [(0, 50), (50, 50)]
    assert len(upserted) == 53
    assert summary == {"channels": 1, "orders": 53, "failed_channels": 0}
    assert channel.last_sync_at == now


async def test_reconcile_counts_a_failing_channel_instead_of_raising(monkeypatch):
    class Broken:
        def __init__(self, creds, settings):
            pass

        async def list_orders(self, since=None, *, limit, offset):
            raise MercadoLibreAPIError(500, "down")

    monkeypatch.setattr(orders_mod, "MercadoLibreConnector", Broken)
    channel = SimpleNamespace(
        id=uuid.uuid4(),
        business_id=uuid.uuid4(),
        credentials={"access_token": "t", "seller_id": "1"},
        settings={},
        last_sync_at=None,
        is_active=True,
    )

    summary = await orders_mod.reconcile_mercadolibre_orders(_channels_db(channel))

    assert summary == {"channels": 1, "orders": 0, "failed_channels": 1}
    assert channel.last_sync_at is None


# ---------- push del catálogo: resultado honesto y publicaciones sin duplicar ----------


class _FakeML:
    """Conector de Mercado Libre con respuestas programables."""

    def __init__(self, create_results=()):
        self._create_results = list(create_results)
        self.created = []
        self.updated = []

    async def create_product(self, product):
        self.created.append(product)
        outcome = self._create_results.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def update_item(self, item_id, *, price=None, available_quantity=None):
        self.updated.append((item_id, price, available_quantity))
        return {}


def _service(monkeypatch, connector, items):
    monkeypatch.setattr(
        sync_mod, "get_connector", lambda platform, creds, settings: connector
    )
    channel = SimpleNamespace(
        credentials={"access_token": "t", "refresh_token": "r", "seller_id": "1"},
        settings={},
    )
    svc = CatalogSyncService(AsyncMock())
    svc.get_connected_channels = AsyncMock(return_value=[channel])
    svc.get_catalog_items = AsyncMock(return_value=items)
    return svc, channel


async def test_push_is_not_a_success_when_an_item_fails_and_keeps_the_listing_ids(
    monkeypatch,
):
    ok = _item(name="Remera")
    broken = _item(name="Pantalón", stock=None)
    connector = _FakeML(create_results=[{"id": "MLA9", "permalink": "https://x"}])
    svc, _ = _service(monkeypatch, connector, [ok, broken])

    result = await svc.push_to_platform(uuid.uuid4(), ChannelPlatform.MERCADOLIBRE)

    assert result.success is False
    assert "1 publicados" in result.message
    assert "1 con error" in result.message
    assert ok.extra_data["external"]["mercadolibre"] == {
        "id": "MLA9",
        "permalink": "https://x",
    }


async def test_second_push_updates_the_existing_listing_instead_of_creating_it_again(
    monkeypatch,
):
    item = _item(
        extra_data={
            "ml_category_id": "MLA1",
            "external": {"mercadolibre": {"id": "MLA9"}},
        },
        price=Decimal("900"),
    )
    connector = _FakeML()
    svc, _ = _service(monkeypatch, connector, [item])

    result = await svc.push_to_platform(uuid.uuid4(), ChannelPlatform.MERCADOLIBRE)

    assert result.success is True
    assert connector.created == []
    assert connector.updated == [("MLA9", 900.0, 4)]


async def test_platform_without_product_creation_is_reported_as_failure(monkeypatch):
    class NoPublish:
        pass

    svc, _ = _service(monkeypatch, NoPublish(), [_item()])

    result = await svc.push_to_platform(uuid.uuid4(), ChannelPlatform.MERCADOLIBRE)

    assert result.success is False
    assert "no permite publicar" in result.message


async def test_expired_token_is_refreshed_once_and_the_push_continues(monkeypatch):
    first = _FakeML(create_results=[MercadoLibreAuthError("vencido")])
    second = _FakeML(create_results=[{"id": "MLA7", "permalink": None}])
    connectors = iter([first, second])
    monkeypatch.setattr(
        sync_mod, "get_connector", lambda platform, creds, settings: next(connectors)
    )
    new_creds = {"access_token": "tok_nuevo", "refresh_token": "r2", "seller_id": "1"}
    refresh = AsyncMock(return_value=new_creds)
    monkeypatch.setattr(sync_mod, "refresh_credentials", refresh)
    channel = SimpleNamespace(
        credentials={"access_token": "viejo", "refresh_token": "r", "seller_id": "1"},
        settings={},
    )
    svc = CatalogSyncService(AsyncMock())
    svc.get_connected_channels = AsyncMock(return_value=[channel])
    svc.get_catalog_items = AsyncMock(return_value=[_item()])

    result = await svc.push_to_platform(uuid.uuid4(), ChannelPlatform.MERCADOLIBRE)

    assert result.success is True
    assert channel.credentials["access_token"] == "tok_nuevo"
    assert refresh.await_count == 1
