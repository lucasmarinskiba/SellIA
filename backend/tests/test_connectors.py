import pytest
from app.domains.channels.connectors.whatsapp import WhatsAppConnector
from app.domains.channels.connectors.email import EmailConnector
from app.domains.channels.connectors.instagram import InstagramConnector
from app.domains.channels.connectors.telegram import TelegramConnector
from app.domains.channels.connectors.mercadolibre import MercadoLibreConnector
from app.domains.channels.connectors.facebook_ads import FacebookAdsConnector
from app.domains.channels.connectors.meta_ads import MetaAdsConnector
from app.domains.channels.connectors.google_ads import GoogleAdsConnector
from app.domains.channels.connectors.shopify import ShopifyConnector
from app.domains.channels.connectors.tiktok_ads import TikTokAdsConnector
from app.domains.channels.connectors.amazon import AmazonSellerConnector
from app.domains.channels.connectors.beacons import BeaconsConnector
from app.domains.channels.connectors.twitter import XConnector
from app.domains.channels.connectors.threads import ThreadsConnector
from app.domains.channels.models import ChannelPlatform


@pytest.mark.asyncio
async def test_whatsapp_parse_webhook():
    connector = WhatsAppConnector({"api_token": "test", "phone_number_id": "123"}, {})
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "metadata": {"phone_number_id": "123"},
                    "messages": [{"from": "5491112345678", "text": {"body": "Hola"}}],
                    "contacts": [{"profile": {"name": "Juan"}}]
                }
            }]
        }]
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.WHATSAPP
    assert result.external_id == "5491112345678"
    assert result.sender_name == "Juan"
    assert result.content == "Hola"


@pytest.mark.asyncio
async def test_email_parse_webhook():
    connector = EmailConnector({"smtp_user": "test@test.com"}, {})
    payload = {"from": "cliente@example.com", "from_name": "Cliente", "body": "Consulta sobre producto"}
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.EMAIL
    assert result.external_id == "cliente@example.com"
    assert result.sender_name == "Cliente"
    assert result.content == "Consulta sobre producto"


@pytest.mark.asyncio
async def test_instagram_parse_webhook():
    connector = InstagramConnector({"api_token": "test"}, {})
    payload = {
        "entry": [{
            "messaging": [{
                "sender": {"id": "123", "username": "usuario_ig"},
                "message": {"text": "Me interesa"}
            }]
        }]
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.INSTAGRAM
    assert result.external_id == "123"
    assert result.sender_name == "usuario_ig"
    assert result.content == "Me interesa"


@pytest.mark.asyncio
async def test_telegram_parse_webhook():
    connector = TelegramConnector({"bot_token": "test"}, {})
    payload = {
        "message": {
            "chat": {"id": 12345},
            "from": {"id": 67890, "first_name": "Pedro", "last_name": "Gomez"},
            "text": "Hola bot"
        }
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.TELEGRAM
    assert result.external_id == "12345"
    assert result.sender_name == "Pedro Gomez"
    assert result.content == "Hola bot"


@pytest.mark.asyncio
async def test_mercadolibre_message_parse():
    connector = MercadoLibreConnector({"access_token": "test", "seller_id": "123"}, {})
    payload = {
        "topic": "messages",
        "user_id": "123",
        "data": {
            "message": {
                "from": {"user_id": "456", "name": "Comprador"},
                "to": {"user_id": "123"},
                "text": "¿Tenés stock?"
            }
        }
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.MERCADOLIBRE
    assert result.external_id == "456"
    assert result.sender_name == "Comprador"
    assert result.content == "¿Tenés stock?"


@pytest.mark.asyncio
async def test_mercadolibre_order_parse():
    connector = MercadoLibreConnector({"access_token": "test", "seller_id": "123"}, {})
    payload = {
        "topic": "orders",
        "user_id": "123",
        "data": {
            "order": {
                "id": "200000123",
                "buyer": {"id": "456", "nickname": "CompradorML"}
            }
        }
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.MERCADOLIBRE
    assert result.external_id == "456"
    assert result.content == "Nueva orden #200000123 en MercadoLibre"


@pytest.mark.asyncio
async def test_facebook_ads_lead_parse():
    connector = FacebookAdsConnector({"access_token": "test"}, {})
    payload = {
        "entry": [{
            "changes": [{
                "field": "leadgen",
                "value": {
                    "leadgen_id": "lead_123",
                    "page_id": "page_456",
                    "form_id": "form_789",
                    "field_data": [
                        {"name": "full_name", "values": ["Ana Lopez"]},
                        {"name": "email", "values": ["ana@example.com"]},
                        {"name": "phone_number", "values": ["+5491112345678"]},
                    ]
                }
            }]
        }]
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.FACEBOOK_ADS
    assert result.external_id == "lead_123"
    assert result.sender_name == "Ana Lopez"
    assert result.sender_email == "ana@example.com"
    assert result.sender_phone == "+5491112345678"
    assert "lead" in result.content_type


@pytest.mark.asyncio
async def test_meta_ads_lead_parse():
    connector = MetaAdsConnector({"access_token": "test"}, {})
    payload = {
        "entry": [{
            "changes": [{
                "field": "leadgen",
                "value": {
                    "leadgen_id": "lead_123",
                    "page_id": "page_456",
                    "field_data": [
                        {"name": "full_name", "values": ["Carlos Ruiz"]},
                        {"name": "email", "values": ["carlos@test.com"]},
                    ]
                }
            }]
        }]
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.META_ADS
    assert result.external_id == "lead_123"
    assert result.sender_name == "Carlos Ruiz"


@pytest.mark.asyncio
async def test_google_ads_lead_parse():
    connector = GoogleAdsConnector({"access_token": "test"}, {})
    payload = {
        "lead_id": "gl_123",
        "campaign_id": "camp_456",
        "form_id": "form_789",
        "user_column_data": [
            {"column_name": "FULL_NAME", "column_value": "Maria Garcia"},
            {"column_name": "EMAIL", "column_value": "maria@example.com"},
            {"column_name": "PHONE_NUMBER", "column_value": "+541112345678"},
            {"column_name": "COMPANY_NAME", "column_value": "Acme Inc"},
        ]
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.GOOGLE_ADS
    assert result.external_id == "gl_123"
    assert result.sender_name == "Maria Garcia"
    assert result.sender_email == "maria@example.com"
    assert "Acme Inc" in result.content


@pytest.mark.asyncio
async def test_shopify_order_parse():
    connector = ShopifyConnector({"shop_domain": "test.myshopify.com"}, {})
    payload = {
        "_topic": "orders/create",
        "id": 12345,
        "name": "#1001",
        "total_price": "99.99",
        "currency": "USD",
        "financial_status": "paid",
        "customer": {"id": 67890, "first_name": "Lucia", "last_name": "Perez", "email": "lucia@test.com"},
        "line_items": [{"title": "Camiseta"}, {"title": "Pantalón"}],
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.SHOPIFY
    assert result.external_id == "67890"
    assert result.sender_name == "Lucia Perez"
    assert "Camiseta" in result.content
    assert "$99.99 USD" in result.content


@pytest.mark.asyncio
async def test_shopify_abandoned_cart_parse():
    connector = ShopifyConnector({"shop_domain": "test.myshopify.com"}, {})
    payload = {
        "_topic": "checkouts/create",
        "id": "abc123",
        "customer": {"id": "cust_1", "first_name": "Roberto", "email": "roberto@test.com"},
        "line_items": [{"title": "Zapatillas"}],
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.SHOPIFY
    assert result.content_type == "abandoned_cart"
    assert "Zapatillas" in result.content


@pytest.mark.asyncio
async def test_tiktok_ads_lead_parse():
    connector = TikTokAdsConnector({"access_token": "test"}, {})
    payload = {
        "lead_id": "tt_123",
        "advertiser_id": "adv_456",
        "campaign_id": "camp_789",
        "lead_data": {
            "name": "Sofia Martinez",
            "email": "sofia@test.com",
            "phone": "+5491112345678",
            "company": "TechCorp",
            "city": "Buenos Aires",
            "country": "AR",
        }
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.TIKTOK_ADS
    assert result.external_id == "tt_123"
    assert result.sender_name == "Sofia Martinez"
    assert "TechCorp" in result.content
    assert "Buenos Aires" in result.content


@pytest.mark.asyncio
async def test_amazon_order_parse():
    connector = AmazonSellerConnector({"access_token": "test"}, {})
    payload = {
        "NotificationType": "ORDER_CHANGE",
        "SellerId": "SELLER123",
        "Payload": {
            "OrderChangeNotification": {
                "OrderChange": {
                    "OrderId": "111-222-333",
                    "BuyerEmail": "buyer@amazon.com",
                    "OrderStatus": "Shipped",
                    "OrderItems": [{"Title": "Kindle Paperwhite"}]
                }
            }
        }
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.AMAZON
    assert result.external_id == "111-222-333"
    assert result.sender_email == "buyer@amazon.com"
    assert "Shipped" in result.content
    assert "Kindle Paperwhite" in result.content


@pytest.mark.asyncio
async def test_amazon_buyer_message_parse():
    connector = AmazonSellerConnector({"access_token": "test"}, {})
    payload = {
        "NotificationType": "BUYER_MESSAGE",
        "Payload": {
            "BuyerMessageNotification": {
                "BuyerMessage": {
                    "OrderId": "444-555-666",
                    "BuyerEmail": "buyer@amazon.com",
                    "Message": "¿Cuándo llega mi pedido?"
                }
            }
        }
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.AMAZON
    assert result.external_id == "444-555-666"
    assert result.content == "¿Cuándo llega mi pedido?"


@pytest.mark.asyncio
async def test_beacons_contact_form_parse():
    connector = BeaconsConnector({"api_key": "test"}, {})
    payload = {
        "event": "contact_form_submission",
        "data": {
            "creator_id": "creator_123",
            "fan_id": "fan_456",
            "name": "Diego Torres",
            "email": "diego@test.com",
            "message": "Quiero colaborar con vos",
            "submitted_at": "2024-01-01T00:00:00Z"
        }
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.BEACONS
    assert result.external_id == "fan_456"
    assert result.sender_name == "Diego Torres"
    assert result.content == "Quiero colaborar con vos"


@pytest.mark.asyncio
async def test_twitter_dm_webhook_parse():
    connector = XConnector({"bearer_token": "test"}, {})
    payload = {
        "event_type": "dm_event",
        "dm_event": {
            "sender_id": "123456",
            "message_create": {
                "message_data": {"text": "Hola, ¿tienen stock?"}
            }
        },
        "users": {
            "123456": {"name": "Juan Perez", "username": "juanp"}
        }
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.TWITTER
    assert result.external_id == "123456"
    assert result.sender_name == "Juan Perez"
    assert result.content == "Hola, ¿tienen stock?"


@pytest.mark.asyncio
async def test_twitter_mention_webhook_parse():
    connector = XConnector({"bearer_token": "test"}, {})
    payload = {
        "event_type": "tweet_create",
        "tweet_create_events": [
            {
                "text": "@sellia Me interesa el producto",
                "user": {"id": 789, "name": "Maria Lopez", "screen_name": "marial"}
            }
        ]
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.TWITTER
    assert result.external_id == "789"
    assert result.sender_name == "Maria Lopez"
    assert "@sellia" in result.content


@pytest.mark.asyncio
async def test_threads_reply_webhook_parse():
    connector = ThreadsConnector({"access_token": "test", "user_id": "456"}, {})
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "thread_id": "thread_123",
                    "from": {"id": "789", "username": "usuario_threads"},
                    "message": "¿Hacen envíos a Córdoba?"
                }
            }]
        }]
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.THREADS
    assert result.external_id == "789"
    assert result.sender_name == "usuario_threads"
    assert result.content == "¿Hacen envíos a Córdoba?"


@pytest.mark.asyncio
async def test_threads_mention_webhook_parse():
    connector = ThreadsConnector({"access_token": "test", "user_id": "456"}, {})
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "mention_data": {
                        "thread_id": "thread_456",
                        "user_id": "999",
                        "username": "ana_threads",
                        "text": "Mención en hilo"
                    }
                }
            }]
        }]
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.THREADS
    assert result.external_id == "999"
    assert result.sender_name == "ana_threads"
    assert result.content == "Mención en hilo"


@pytest.mark.asyncio
async def test_beacons_store_purchase_parse():
    connector = BeaconsConnector({"api_key": "test"}, {})
    payload = {
        "event": "store_purchase",
        "data": {
            "creator_id": "creator_123",
            "fan_id": "fan_789",
            "fan_name": "Valentina",
            "fan_email": "valentina@test.com",
            "product_name": "Curso de Fotografía",
            "amount": "49.99",
            "currency": "USD"
        }
    }
    result = await connector.parse_webhook(payload)
    assert result.platform == ChannelPlatform.BEACONS
    assert result.external_id == "fan_789"
    assert result.content_type == "order"
    assert "Curso de Fotografía" in result.content
    assert "$49.99 USD" in result.content
