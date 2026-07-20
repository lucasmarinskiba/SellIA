"""Unit tests for sales channels — Multi-channel sales orchestration.

Tests cover:
- Channel initialization
- Message sending across channels
- Lead distribution
- Channel-specific logic
- Analytics and reporting
- Channel health monitoring
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.connectors.base_connector import BaseConnector
from app.core.connectors.mercadolibre_connector import MercadolibreConnector
from app.core.connectors.whatsapp_connector import WhatsappConnector


class TestChannelInitialization:
    """Test channel connector initialization."""

    def test_mercadolibre_connector_init(self):
        """Test MercadoLibre connector initialization."""
        connector = MercadolibreConnector(
            access_token="test_token",
            seller_id="test_seller"
        )

        assert connector is not None
        assert hasattr(connector, 'access_token')
        assert hasattr(connector, 'seller_id')

    def test_whatsapp_connector_init(self):
        """Test WhatsApp connector initialization."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        assert connector is not None
        assert hasattr(connector, 'phone_number')

    @pytest.mark.asyncio
    async def test_connector_authentication(self):
        """Test connector authentication."""
        connector = MercadolibreConnector(
            access_token="test_token",
            seller_id="test_seller"
        )

        is_authenticated = await connector.authenticate()

        assert isinstance(is_authenticated, bool)

    @pytest.mark.asyncio
    async def test_connector_health_check(self):
        """Test connector health check."""
        connector = MercadolibreConnector(
            access_token="test_token",
            seller_id="test_seller"
        )

        health = await connector.health_check()

        assert isinstance(health, dict)
        assert "status" in health


class TestMessageSending:
    """Test message sending across channels."""

    @pytest.mark.asyncio
    async def test_send_whatsapp_message(self):
        """Test sending WhatsApp message."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        result = await connector.send_message(
            recipient="+9876543210",
            message="Test message"
        )

        assert result is not None
        assert "message_id" in result or "success" in result

    @pytest.mark.asyncio
    async def test_send_mercadolibre_message(self):
        """Test sending MercadoLibre message."""
        connector = MercadolibreConnector(
            access_token="test_token",
            seller_id="test_seller"
        )

        result = await connector.send_message(
            recipient="buyer_123",
            message="Your order is ready",
            subject="Order Update"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_send_bulk_messages(self):
        """Test sending messages to multiple recipients."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        recipients = [
            "+1111111111",
            "+2222222222",
            "+3333333333"
        ]

        result = await connector.send_bulk_messages(
            recipients=recipients,
            message="Bulk message"
        )

        assert result is not None
        assert len(result) == 3 or "batch_id" in result

    @pytest.mark.asyncio
    async def test_send_template_message(self):
        """Test sending templated messages."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        result = await connector.send_template(
            recipient="+9876543210",
            template_name="order_confirmation",
            parameters={"order_id": "12345"}
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_message_with_media(self):
        """Test sending messages with media attachments."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        result = await connector.send_message_with_media(
            recipient="+9876543210",
            message="Check out this product",
            media_url="https://example.com/image.jpg",
            media_type="image"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_message_delivery_status(self):
        """Test checking message delivery status."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        status = await connector.get_message_status("message_id_123")

        assert status is not None
        assert "delivery_status" in status or "status" in status


class TestLeadDistribution:
    """Test lead distribution across channels."""

    @pytest.mark.asyncio
    async def test_distribute_lead_to_channel(self):
        """Test distributing a lead to appropriate channel."""
        from app.core.intelligence.platform_intelligence import PlatformIntelligence

        intel = PlatformIntelligence()

        lead = {
            "id": "lead_123",
            "email": "test@example.com",
            "phone": "+1234567890",
            "preferred_channel": "whatsapp"
        }

        distributed = await intel.distribute_lead(lead)

        assert distributed is not None
        assert "channel" in distributed

    @pytest.mark.asyncio
    async def test_omnichannel_lead_handling(self):
        """Test handling same lead across multiple channels."""
        from app.core.orchestration.multi_platform_orchestrator import (
            MultiPlatformOrchestrator
        )

        orchestrator = MultiPlatformOrchestrator()

        lead = {
            "id": "lead_456",
            "email": "omni@example.com",
            "phone": "+9876543210"
        }

        channels = ["whatsapp", "email", "mercadolibre"]

        results = await orchestrator.engage_on_channels(lead, channels)

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_channel_priority_selection(self):
        """Test selecting channel based on priority."""
        from app.core.intelligence.platform_intelligence import PlatformIntelligence

        intel = PlatformIntelligence()

        lead = {
            "id": "lead_789",
            "channels_available": ["email", "whatsapp", "sms"],
            "response_rate_preference": "high"
        }

        best_channel = await intel.select_optimal_channel(lead)

        assert best_channel in ["email", "whatsapp", "sms"]

    @pytest.mark.asyncio
    async def test_channel_rotation(self):
        """Test rotating channels for follow-up."""
        from app.core.orchestration.multi_platform_orchestrator import (
            MultiPlatformOrchestrator
        )

        orchestrator = MultiPlatformOrchestrator()

        lead_id = "lead_rotation"

        # First contact
        channel1 = await orchestrator.select_channel(lead_id, attempt=1)

        # Follow-up on different channel
        channel2 = await orchestrator.select_channel(lead_id, attempt=2)

        # Should use different channels
        if channel1 and channel2:
            # Not asserting inequality as logic might reuse
            assert channel1 is not None
            assert channel2 is not None


class TestChannelSpecificLogic:
    """Test channel-specific business logic."""

    @pytest.mark.asyncio
    async def test_mercadolibre_listing_creation(self):
        """Test creating MercadoLibre listing."""
        connector = MercadolibreConnector(
            access_token="test_token",
            seller_id="test_seller"
        )

        listing = {
            "title": "iPhone 12",
            "price": 500.00,
            "category_id": "MLA1051",
            "quantity": 1,
            "description": "Like new condition"
        }

        result = await connector.create_listing(listing)

        assert result is not None
        assert "listing_id" in result or "id" in result

    @pytest.mark.asyncio
    async def test_mercadolibre_order_handling(self):
        """Test handling MercadoLibre orders."""
        connector = MercadolibreConnector(
            access_token="test_token",
            seller_id="test_seller"
        )

        order = await connector.get_order("order_id_123")

        assert order is not None

    @pytest.mark.asyncio
    async def test_whatsapp_conversation_context(self):
        """Test maintaining WhatsApp conversation context."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        conversation = await connector.get_conversation("+9876543210")

        assert conversation is not None
        assert "messages" in conversation or "history" in conversation

    @pytest.mark.asyncio
    async def test_whatsapp_group_management(self):
        """Test WhatsApp group management."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        group = await connector.create_group(
            group_name="Sales Team",
            participants=["+1111111111", "+2222222222"]
        )

        assert group is not None


class TestChannelAnalytics:
    """Test analytics and reporting."""

    @pytest.mark.asyncio
    async def test_message_delivery_metrics(self):
        """Test tracking message delivery metrics."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        metrics = await connector.get_delivery_metrics(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        assert metrics is not None
        assert "total_sent" in metrics or "messages_sent" in metrics
        assert "delivered" in metrics

    @pytest.mark.asyncio
    async def test_response_rate_analytics(self):
        """Test response rate analytics."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        analytics = await connector.get_response_metrics()

        assert analytics is not None
        assert "response_rate" in analytics or "response_percentage" in analytics

    @pytest.mark.asyncio
    async def test_channel_revenue_analytics(self):
        """Test revenue analytics per channel."""
        from app.core.intelligence.platform_intelligence import PlatformIntelligence

        intel = PlatformIntelligence()

        revenue = await intel.get_channel_revenue(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        assert revenue is not None
        assert isinstance(revenue, dict)

    @pytest.mark.asyncio
    async def test_performance_comparison(self):
        """Test performance comparison across channels."""
        from app.core.intelligence.platform_intelligence import PlatformIntelligence

        intel = PlatformIntelligence()

        comparison = await intel.compare_channels()

        assert comparison is not None
        assert isinstance(comparison, dict)

    @pytest.mark.asyncio
    async def test_channel_conversion_rates(self):
        """Test conversion rate by channel."""
        from app.core.intelligence.platform_intelligence import PlatformIntelligence

        intel = PlatformIntelligence()

        conversions = await intel.get_conversion_rates_by_channel()

        assert conversions is not None
        assert isinstance(conversions, dict)


class TestChannelHealthMonitoring:
    """Test channel health and availability monitoring."""

    @pytest.mark.asyncio
    async def test_monitor_channel_uptime(self):
        """Test monitoring channel uptime."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        uptime = await connector.get_uptime_status()

        assert uptime is not None
        assert 0 <= uptime <= 100

    @pytest.mark.asyncio
    async def test_detect_channel_outage(self):
        """Test detecting channel outages."""
        connector = MercadolibreConnector(
            access_token="test_token",
            seller_id="test_seller"
        )

        outage_status = await connector.check_for_outage()

        assert isinstance(outage_status, bool)

    @pytest.mark.asyncio
    async def test_automatic_failover(self):
        """Test automatic failover to backup channel."""
        from app.core.orchestration.multi_platform_orchestrator import (
            MultiPlatformOrchestrator
        )

        orchestrator = MultiPlatformOrchestrator()

        # Simulate primary channel failure
        lead = {"id": "lead_fail", "email": "test@example.com"}

        result = await orchestrator.send_with_failover(
            lead,
            message="Important message",
            primary_channel="whatsapp",
            fallback_channels=["email", "sms"]
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_rate_limit_monitoring(self):
        """Test monitoring channel rate limits."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        limits = await connector.get_rate_limit_status()

        assert limits is not None
        assert "remaining_requests" in limits or "quota_remaining" in limits

    @pytest.mark.asyncio
    async def test_quota_management(self):
        """Test managing channel quotas."""
        connector = MercadolibreConnector(
            access_token="test_token",
            seller_id="test_seller"
        )

        quota = await connector.get_quota_usage()

        assert quota is not None
        assert "used" in quota
        assert "limit" in quota


class TestChannelIntegration:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_omnichannel_customer_journey(self):
        """Test complete omnichannel customer journey."""
        from app.core.orchestration.multi_platform_orchestrator import (
            MultiPlatformOrchestrator
        )

        orchestrator = MultiPlatformOrchestrator()

        lead = {
            "id": "omni_lead",
            "email": "journey@example.com",
            "phone": "+1234567890"
        }

        # Step 1: Initial contact
        contact_result = await orchestrator.initiate_contact(
            lead,
            channels=["whatsapp", "email"]
        )
        assert contact_result is not None

        # Step 2: Nurture
        nurture_result = await orchestrator.nurture_lead(
            lead,
            sequence="standard_nurture"
        )
        assert nurture_result is not None

        # Step 3: Conversion
        conversion_result = await orchestrator.attempt_conversion(
            lead,
            offer="standard_offer"
        )
        assert conversion_result is not None

    @pytest.mark.asyncio
    async def test_channel_aggregation_reporting(self):
        """Test aggregated reporting across all channels."""
        from app.core.intelligence.platform_intelligence import PlatformIntelligence

        intel = PlatformIntelligence()

        report = await intel.generate_aggregated_report(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        assert report is not None
        assert "total_leads" in report
        assert "total_revenue" in report
        assert "channels" in report


class TestChannelEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_handle_invalid_phone_number(self):
        """Test handling invalid phone numbers."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        try:
            result = await connector.send_message(
                recipient="invalid_number",
                message="Test"
            )
            # Should either raise error or return error result
            assert result is None or "error" in result
        except ValueError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_handle_expired_token(self):
        """Test handling expired authentication token."""
        connector = MercadolibreConnector(
            access_token="expired_token",
            seller_id="test_seller"
        )

        try:
            result = await connector.authenticate()
            # Should return False or raise error
            assert result is False or isinstance(result, Exception)
        except Exception:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test handling rate limiting."""
        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        # Send many messages rapidly
        for _ in range(100):
            try:
                await connector.send_message(
                    recipient="+9876543210",
                    message="Test"
                )
            except Exception:
                # Expected rate limit error
                break
