"""Customer FOMO Campaign Tests - Layer 5"""

import pytest
from app.domains.fomo.customer_fomo_service import (
    CustomerFOMOCampaignService,
    CustomerFOMOTemplates,
)


class TestFOMOTemplates:
    """Test pre-built FOMO campaign templates"""

    def test_live_visitor_template(self):
        template = CustomerFOMOTemplates.get_live_visitor_count_template()
        assert template.name == "Live Visitor Counter"
        assert template.expected_conversion_lift == 0.15
        assert template.setup_time_minutes == 5
        assert len(template.widgets) > 0

    def test_purchase_notifications_template(self):
        template = CustomerFOMOTemplates.get_purchase_notifications_template()
        assert template.name == "Purchase Notifications"
        assert template.expected_conversion_lift == 0.22
        assert template.setup_time_minutes == 10

    def test_countdown_timer_template(self):
        template = CustomerFOMOTemplates.get_countdown_timer_template()
        assert template.name == "Countdown Timer"
        assert template.expected_conversion_lift == 0.35
        assert len(template.automations) > 0

    def test_stock_scarcity_template(self):
        template = CustomerFOMOTemplates.get_stock_scarcity_template()
        assert template.name == "Stock Scarcity"
        assert template.expected_conversion_lift == 0.28

    def test_cart_abandonment_template(self):
        template = CustomerFOMOTemplates.get_cart_abandonment_template()
        assert template.name == "Cart Abandonment Recovery"
        assert template.expected_conversion_lift == 0.42
        assert len(template.automations) > 0

    def test_flash_sale_template(self):
        template = CustomerFOMOTemplates.get_flash_sale_template()
        assert template.name == "Flash Sale Campaign"
        assert template.expected_conversion_lift == 0.65
        assert len(template.widgets) >= 2


class TestCampaignCreation:
    """Test campaign creation from templates"""

    @pytest.mark.asyncio
    async def test_create_campaign_from_live_visitor_template(self):
        campaign = await CustomerFOMOCampaignService.create_campaign_from_template(
            user_id="user123",
            business_id="biz456",
            template_type="live_visitor",
        )
        assert campaign["user_id"] == "user123"
        assert campaign["business_id"] == "biz456"
        assert campaign["template"] == "live_visitor"
        assert campaign["status"] == "draft"
        assert campaign["expected_conversion_lift"] == "15%"

    @pytest.mark.asyncio
    async def test_create_campaign_with_custom_config(self):
        custom = {
            "name": "Custom Campaign",
            "messaging": {"default": "Custom message"}
        }
        campaign = await CustomerFOMOCampaignService.create_campaign_from_template(
            user_id="user123",
            business_id="biz456",
            template_type="flash_sale",
            custom_config=custom,
        )
        assert campaign["name"] == "Custom Campaign"
        assert campaign["template"] == "flash_sale"

    @pytest.mark.asyncio
    async def test_campaign_creation_all_templates(self):
        templates = ["live_visitor", "purchases", "countdown", "scarcity", "cart", "flash_sale"]
        for template in templates:
            campaign = await CustomerFOMOCampaignService.create_campaign_from_template(
                user_id="user123",
                business_id="biz456",
                template_type=template,
            )
            assert campaign["template"] == template
            assert "campaign_id" in campaign

    @pytest.mark.asyncio
    async def test_invalid_template_raises_error(self):
        with pytest.raises(ValueError):
            await CustomerFOMOCampaignService.create_campaign_from_template(
                user_id="user123",
                business_id="biz456",
                template_type="invalid_template",
            )


class TestWidgetGeneration:
    """Test widget embed code generation"""

    @pytest.mark.asyncio
    async def test_generate_embed_code(self):
        embed = await CustomerFOMOCampaignService.generate_embed_code(
            campaign_id="camp123",
            widget_type="visitor_counter",
        )
        assert "script" in embed.lower()
        assert "camp123" in embed
        assert "visitor_counter" in embed
        assert "sellia-brain.vercel.app" in embed

    @pytest.mark.asyncio
    async def test_embed_code_contains_proper_attributes(self):
        embed = await CustomerFOMOCampaignService.generate_embed_code(
            campaign_id="test_camp",
            widget_type="countdown",
        )
        assert 'data-campaign-id' in embed
        assert 'data-widget-type' in embed


class TestCampaignActivation:
    """Test campaign activation"""

    @pytest.mark.asyncio
    async def test_activate_campaign(self):
        result = await CustomerFOMOCampaignService.activate_campaign("camp123")
        assert result["campaign_id"] == "camp123"
        assert result["status"] == "active"
        assert result["tracking_enabled"] is True

    @pytest.mark.asyncio
    async def test_activation_response_structure(self):
        result = await CustomerFOMOCampaignService.activate_campaign("camp123")
        assert "activated_at" in result
        assert "widgets_active" in result
        assert "automations_active" in result


class TestCampaignPerformance:
    """Test campaign performance metrics"""

    @pytest.mark.asyncio
    async def test_get_campaign_performance(self):
        perf = await CustomerFOMOCampaignService.get_campaign_performance("camp123")
        assert perf["campaign_id"] == "camp123"
        assert perf["impressions"] > 0
        assert perf["conversions"] > 0
        assert perf["roi"] > 0

    @pytest.mark.asyncio
    async def test_performance_has_daily_breakdown(self):
        perf = await CustomerFOMOCampaignService.get_campaign_performance("camp123")
        assert "daily_breakdown" in perf
        assert len(perf["daily_breakdown"]) >= 3
        for day in perf["daily_breakdown"]:
            assert "date" in day
            assert "impressions" in day
            assert "conversions" in day

    @pytest.mark.asyncio
    async def test_performance_metrics_realistic(self):
        perf = await CustomerFOMOCampaignService.get_campaign_performance("camp123")
        assert perf["ctr"] > 0 and perf["ctr"] < 1
        assert perf["conversion_rate"] > 0 and perf["conversion_rate"] < 1
        assert perf["conversion_lift"] > 0
        assert float(perf["revenue"]) > 0


class TestAutomationSequences:
    """Test multi-step automation sequences"""

    @pytest.mark.asyncio
    async def test_cart_abandonment_sequence(self):
        sequence = await CustomerFOMOCampaignService.create_automation_sequence(
            campaign_id="camp123",
            automation_type="cart_abandonment",
            channels=["email", "sms"],
            messages={
                "email_1": "Complete your purchase",
                "email_2": "Others are buying this",
                "sms_1": "50% OFF code inside",
            }
        )
        assert sequence["type"] == "cart_abandonment"
        assert len(sequence["steps"]) == 3
        assert "estimated_conversions" in sequence

    @pytest.mark.asyncio
    async def test_flash_sale_sequence(self):
        sequence = await CustomerFOMOCampaignService.create_automation_sequence(
            campaign_id="camp123",
            automation_type="flash_sale",
            channels=["email", "sms", "push"],
            messages={}
        )
        assert sequence["type"] == "flash_sale"
        assert len(sequence["steps"]) == 4
        assert "email" in str(sequence["steps"])

    @pytest.mark.asyncio
    async def test_automation_sequence_has_projections(self):
        sequence = await CustomerFOMOCampaignService.create_automation_sequence(
            campaign_id="camp123",
            automation_type="cart_abandonment",
            channels=["email"],
            messages={}
        )
        assert "estimated_reach" in sequence
        assert "estimated_conversions" in sequence
        assert "estimated_revenue" in sequence


class TestROICalculation:
    """Test ROI and campaign metrics calculation"""

    @pytest.mark.asyncio
    async def test_calculate_roi(self):
        roi = await CustomerFOMOCampaignService.calculate_roi(
            campaign_id="camp123",
            revenue=10000,
            cost=2000,
            baseline_conversion=0.025,
        )
        assert roi["campaign_id"] == "camp123"
        assert roi["revenue_generated"] == 10000
        assert roi["campaign_cost"] == 2000
        assert roi["roi_percent"] == 400  # (10000 - 2000) / 2000 * 100

    @pytest.mark.asyncio
    async def test_roi_with_zero_cost(self):
        roi = await CustomerFOMOCampaignService.calculate_roi(
            campaign_id="camp123",
            revenue=5000,
            cost=0,
            baseline_conversion=0.025,
        )
        assert roi["revenue_per_dollar_spent"] == 0

    @pytest.mark.asyncio
    async def test_roi_realistic_payback(self):
        roi = await CustomerFOMOCampaignService.calculate_roi(
            campaign_id="camp123",
            revenue=12000,  # $12000 total revenue
            cost=3000,  # $3000 campaign cost
            baseline_conversion=0.025,
        )
        assert roi["payback_days"] > 0
        assert roi["roi_percent"] > 0
        assert roi["roi_percent"] == 300  # (12000-3000)/3000 * 100


class TestIndustryBenchmarks:
    """Test industry-specific benchmarks"""

    @pytest.mark.asyncio
    async def test_ecommerce_benchmarks(self):
        benchmarks = await CustomerFOMOCampaignService.get_competitor_benchmarks("ecommerce")
        assert benchmarks["avg_conversion_rate"] == 0.025
        assert benchmarks["avg_ctr"] == 0.045
        assert benchmarks["fomo_lift_potential"] == 0.35

    @pytest.mark.asyncio
    async def test_saas_benchmarks(self):
        benchmarks = await CustomerFOMOCampaignService.get_competitor_benchmarks("saas")
        assert benchmarks["avg_conversion_rate"] == 0.05
        assert benchmarks["fomo_lift_potential"] == 0.42

    @pytest.mark.asyncio
    async def test_services_benchmarks(self):
        benchmarks = await CustomerFOMOCampaignService.get_competitor_benchmarks("services")
        assert benchmarks["avg_conversion_rate"] == 0.03

    @pytest.mark.asyncio
    async def test_default_benchmarks(self):
        benchmarks = await CustomerFOMOCampaignService.get_competitor_benchmarks("unknown")
        assert "avg_conversion_rate" in benchmarks


class TestAnalyticsExport:
    """Test analytics data export"""

    @pytest.mark.asyncio
    async def test_export_as_csv(self):
        csv = await CustomerFOMOCampaignService.export_analytics("camp123", "csv")
        assert "date" in csv
        assert "impressions" in csv
        assert "conversions" in csv

    @pytest.mark.asyncio
    async def test_export_as_json(self):
        import json
        json_data = await CustomerFOMOCampaignService.export_analytics("camp123", "json")
        data = json.loads(json_data)
        assert data["campaign_id"] == "camp123"
        assert "export_date" in data

    @pytest.mark.asyncio
    async def test_export_invalid_format(self):
        result = await CustomerFOMOCampaignService.export_analytics("camp123", "xml")
        assert result == ""


class TestEmbeddingGuides:
    """Test widget embedding guides"""

    @pytest.mark.asyncio
    async def test_get_visitor_counter_guide(self):
        guide = await CustomerFOMOCampaignService.get_widget_embedding_guide("visitor_counter")
        assert "html_setup" in guide
        assert "positioning" in guide
        assert guide["real_time"] is True

    @pytest.mark.asyncio
    async def test_get_purchase_feed_guide(self):
        guide = await CustomerFOMOCampaignService.get_widget_embedding_guide("purchase_feed")
        assert "html_setup" in guide
        assert "bottom-left" in guide["positioning"]

    @pytest.mark.asyncio
    async def test_get_countdown_guide(self):
        guide = await CustomerFOMOCampaignService.get_widget_embedding_guide("countdown")
        assert "customization" in guide
        assert "timezone" in guide["customization"]

    @pytest.mark.asyncio
    async def test_get_stock_badge_guide(self):
        guide = await CustomerFOMOCampaignService.get_widget_embedding_guide("stock_badge")
        assert "threshold_colors" in guide["customization"]

    @pytest.mark.asyncio
    async def test_invalid_widget_guide(self):
        guide = await CustomerFOMOCampaignService.get_widget_embedding_guide("invalid")
        assert guide == {}


class TestConversionLifts:
    """Test FOMO conversion lift expectations"""

    def test_all_templates_have_lift_projections(self):
        templates_to_test = [
            ("live_visitor", 0.15),
            ("purchases", 0.22),
            ("countdown", 0.35),
            ("scarcity", 0.28),
            ("cart", 0.42),
            ("flash_sale", 0.65),
        ]

        template_methods = {
            "live_visitor": CustomerFOMOTemplates.get_live_visitor_count_template,
            "purchases": CustomerFOMOTemplates.get_purchase_notifications_template,
            "countdown": CustomerFOMOTemplates.get_countdown_timer_template,
            "scarcity": CustomerFOMOTemplates.get_stock_scarcity_template,
            "cart": CustomerFOMOTemplates.get_cart_abandonment_template,
            "flash_sale": CustomerFOMOTemplates.get_flash_sale_template,
        }

        for template_id, expected_lift in templates_to_test:
            template = template_methods[template_id]()
            assert template.expected_conversion_lift == expected_lift

    def test_lift_progression(self):
        """Flash sale should have highest lift, visitor counter lowest"""
        visitor = CustomerFOMOTemplates.get_live_visitor_count_template()
        flash = CustomerFOMOTemplates.get_flash_sale_template()
        assert flash.expected_conversion_lift > visitor.expected_conversion_lift


class TestSetupTime:
    """Test setup time estimates"""

    def test_setup_times_reasonable(self):
        templates = [
            CustomerFOMOTemplates.get_live_visitor_count_template(),
            CustomerFOMOTemplates.get_countdown_timer_template(),
            CustomerFOMOTemplates.get_flash_sale_template(),
        ]

        for template in templates:
            assert 5 <= template.setup_time_minutes <= 30

    def test_flash_sale_takes_longest(self):
        flash = CustomerFOMOTemplates.get_flash_sale_template()
        visitor = CustomerFOMOTemplates.get_live_visitor_count_template()
        assert flash.setup_time_minutes > visitor.setup_time_minutes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
