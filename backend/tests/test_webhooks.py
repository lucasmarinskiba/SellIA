import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock

from app.api.v1.channels import receive_webhook
from app.domains.channels.models import ChannelConnection, ChannelPlatform


@pytest.mark.asyncio
async def test_webhook_with_valid_token():
    db = AsyncMock()
    channel = MagicMock()
    channel.id = "test-id"
    channel.business_id = "biz-id"
    channel.credentials = {}
    channel.settings = {}
    channel.is_active = True

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = channel
    db.execute.return_value = result_mock

    request = MagicMock()
    request.body = AsyncMock(return_value=b'{}')
    request.json = AsyncMock(return_value={"text": "Hola"})
    request.headers = {}

    response = await receive_webhook(
        platform=ChannelPlatform.TELEGRAM,
        request=request,
        token="valid_token_123",
        db=db,
    )
    assert response["status"] == "accepted"


@pytest.mark.asyncio
async def test_webhook_with_invalid_token():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute.return_value = result_mock

    request = MagicMock()
    request.body = AsyncMock(return_value=b'{}')
    request.json = AsyncMock(return_value={})
    request.headers = {}

    with pytest.raises(HTTPException) as exc_info:
        await receive_webhook(
            platform=ChannelPlatform.TELEGRAM,
            request=request,
            token="invalid_token",
            db=db,
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_webhook_missing_channel():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute.return_value = result_mock

    request = MagicMock()
    request.body = AsyncMock(return_value=b'{}')
    request.json = AsyncMock(return_value={"user_id": "unknown"})
    request.headers = {}

    with pytest.raises(HTTPException) as exc_info:
        await receive_webhook(
            platform=ChannelPlatform.MERCADOLIBRE,
            request=request,
            token=None,
            db=db,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_shopify_webhook_valid_hmac():
    import hmac
    import hashlib

    db = AsyncMock()
    channel = MagicMock()
    channel.id = "shopify-id"
    channel.credentials = {"shop_domain": "test.myshopify.com", "webhook_secret": "secret123"}
    channel.settings = {}
    channel.is_active = True

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = channel
    db.execute.return_value = result_mock

    raw_body = b'{"id":123}'
    digest = hmac.new(b"secret123", raw_body, hashlib.sha256).hexdigest()

    request = MagicMock()
    request.body = AsyncMock(return_value=raw_body)
    request.json = AsyncMock(return_value={"id": 123})
    request.headers = {
        "X-Shopify-Shop-Domain": "test.myshopify.com",
        "X-Shopify-Hmac-SHA256": digest,
    }

    response = await receive_webhook(
        platform=ChannelPlatform.SHOPIFY,
        request=request,
        token=None,
        db=db,
    )
    assert response["status"] == "accepted"


@pytest.mark.asyncio
async def test_shopify_webhook_invalid_hmac():
    db = AsyncMock()
    channel = MagicMock()
    channel.credentials = {"shop_domain": "test.myshopify.com", "webhook_secret": "secret123"}
    channel.settings = {}
    channel.is_active = True

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = channel
    db.execute.return_value = result_mock

    request = MagicMock()
    request.body = AsyncMock(return_value=b'{"id":123}')
    request.json = AsyncMock(return_value={"id": 123})
    request.headers = {
        "X-Shopify-Shop-Domain": "test.myshopify.com",
        "X-Shopify-Hmac-SHA256": "invalid_hmac",
    }

    with pytest.raises(HTTPException) as exc_info:
        await receive_webhook(
            platform=ChannelPlatform.SHOPIFY,
            request=request,
            token=None,
            db=db,
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_whatsapp_webhook_valid_signature():
    import hmac
    import hashlib

    db = AsyncMock()
    channel = MagicMock()
    channel.id = "wa-id"
    channel.credentials = {"phone_number_id": "123", "app_secret": "appsecret123"}
    channel.settings = {}
    channel.is_active = True

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = channel
    db.execute.return_value = result_mock

    raw_body = b'{"entry":[{"changes":[{"value":{"metadata":{"phone_number_id":"123"},"messages":[{"from":"5491112345678","text":{"body":"Hola"}}],"contacts":[{"profile":{"name":"Juan"}}]}}]}]}'
    expected = "sha256=" + hmac.new(b"appsecret123", raw_body, hashlib.sha256).hexdigest()

    request = MagicMock()
    request.body = AsyncMock(return_value=raw_body)
    request.json = AsyncMock(return_value={
        "entry": [{"changes": [{"value": {"metadata": {"phone_number_id": "123"}, "messages": [{"from": "5491112345678", "text": {"body": "Hola"}}], "contacts": [{"profile": {"name": "Juan"}}]}}]}]
    })
    request.headers = {"X-Hub-Signature-256": expected}

    response = await receive_webhook(
        platform=ChannelPlatform.WHATSAPP,
        request=request,
        token=None,
        db=db,
    )
    assert response["status"] == "accepted"


@pytest.mark.asyncio
async def test_whatsapp_webhook_invalid_signature():
    db = AsyncMock()
    channel = MagicMock()
    channel.credentials = {"phone_number_id": "123", "app_secret": "appsecret123"}
    channel.settings = {}
    channel.is_active = True

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = channel
    result_mock.scalars.return_value.all.return_value = [channel]
    db.execute.return_value = result_mock

    raw_body = b'{"entry":[]}'

    request = MagicMock()
    request.body = AsyncMock(return_value=raw_body)
    request.json = AsyncMock(return_value={"entry": []})
    request.headers = {"X-Hub-Signature-256": "sha256=invalid"}

    with pytest.raises(HTTPException) as exc_info:
        await receive_webhook(
            platform=ChannelPlatform.WHATSAPP,
            request=request,
            token=None,
            db=db,
        )
    assert exc_info.value.status_code == 401
