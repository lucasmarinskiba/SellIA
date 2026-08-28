"""Growth FOOM endpoint tests"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestSeoEndpoints:
    def test_get_seo_content_calendar(self):
        response = client.get("/fomo/growth/seo/content-calendar?days=90")
        assert response.status_code == 200
        assert "plan" in response.json()
        assert response.json()["total_pieces"] > 0

    def test_seo_content_calendar_default_days(self):
        response = client.get("/fomo/growth/seo/content-calendar")
        assert response.status_code == 200
        assert response.json()["timeline"]

    def test_serp_optimization_case_study(self):
        response = client.get("/fomo/growth/seo/serp-optimization/case_study")
        assert response.status_code == 200
        assert "optimization" in response.json()

    def test_serp_optimization_all_types(self):
        for content_type in ["case_study", "comparison", "how_to"]:
            response = client.get(f"/fomo/growth/seo/serp-optimization/{content_type}")
            assert response.status_code == 200
            assert response.json()["content_type"] == content_type


class TestViralEndpoints:
    def test_referral_program(self):
        response = client.get("/fomo/growth/viral/referral-program")
        assert response.status_code == 200
        data = response.json()
        assert data["viral_coefficient"] > 1.0
        assert data["referrer_reward"]["cash_credit"] > 0

    def test_community_program(self):
        response = client.get("/fomo/growth/viral/community-program")
        assert response.status_code == 200
        data = response.json()
        assert len(data["channels"]) >= 3
        assert "gamification" in data

    def test_waitlist_program(self):
        response = client.get("/fomo/growth/viral/waitlist")
        assert response.status_code == 200
        data = response.json()
        assert len(data["features"]) >= 5
        assert "messaging" in data

    def test_viral_mechanics(self):
        response = client.get("/fomo/growth/viral/mechanics")
        assert response.status_code == 200
        data = response.json()
        assert len(data["mechanics"]) >= 5
        assert data["k_factor"] >= 1.5


class TestCaseStudyEndpoints:
    def test_generate_case_study(self):
        response = client.get(
            "/fomo/growth/case-studies/generate?"
            "business_name=TestShop&"
            "cr_improvement_percent=150&"
            "revenue_improvement_percent=250"
        )
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "before_after" in data
        assert "testimonial" in data

    def test_case_study_formats(self):
        response = client.get(
            "/fomo/growth/case-studies/generate?"
            "business_name=Shop&"
            "cr_improvement_percent=100&"
            "revenue_improvement_percent=100"
        )
        data = response.json()
        assert "format_types" in data


class TestPressEndpoints:
    def test_press_release_milestone(self):
        response = client.get("/fomo/growth/press/release-template/milestone")
        assert response.status_code == 200
        data = response.json()
        assert "distribution_channels" in data
        assert len(data["distribution_channels"]) > 5

    def test_press_release_award(self):
        response = client.get("/fomo/growth/press/release-template/award")
        assert response.status_code == 200

    def test_influencer_seeding(self):
        response = client.get("/fomo/growth/press/influencer-seeding")
        assert response.status_code == 200
        data = response.json()
        assert "tier_1" in data["target_influencers"]
        assert "tier_2" in data["target_influencers"]
        assert "tier_3" in data["target_influencers"]


class TestProductLedEndpoints:
    def test_trial_optimization(self):
        response = client.get("/fomo/growth/plg/free-trial-optimization")
        assert response.status_code == 200
        data = response.json()
        assert data["trial_length_days"] == 14
        assert len(data["upsell_triggers"]) >= 4

    def test_feature_gates(self):
        response = client.get("/fomo/growth/plg/feature-gates")
        assert response.status_code == 200
        data = response.json()
        assert "free" in data["feature_tiers"]
        assert "pro" in data["feature_tiers"]
        assert len(data["feature_gates"]) >= 5


class TestPartnershipEndpoints:
    def test_partnerships_list(self):
        response = client.get("/fomo/growth/partnerships/list")
        assert response.status_code == 200
        data = response.json()
        assert len(data["partnerships"]) >= 6
        assert data["total_expected_mau"] > 8000


class TestBrandEndpoints:
    def test_thought_leadership(self):
        response = client.get("/fomo/growth/brand/thought-leadership")
        assert response.status_code == 200
        data = response.json()
        assert len(data["channels"]) >= 5
        channels = [c["channel"] for c in data["channels"]]
        assert "Podcast" in channels
        assert "YouTube" in channels
        assert "Newsletter" in channels


class TestGrowthSummary:
    def test_growth_summary_dashboard(self):
        response = client.get("/fomo/growth/dashboard/growth-summary")
        assert response.status_code == 200
        data = response.json()
        assert "acquisition_channels" in data
        assert data["total_estimated_mau"] == "12000-20000"
        assert "$" in str(data["blended_cac"])

    def test_summary_includes_all_channels(self):
        response = client.get("/fomo/growth/dashboard/growth-summary")
        data = response.json()
        channels = data["acquisition_channels"]
        assert "organic_seo" in channels
        assert "referral_viral" in channels
        assert "partnerships" in channels
        assert "product_led_growth" in channels
        assert "brand_building" in channels

    def test_summary_realistic_metrics(self):
        response = client.get("/fomo/growth/dashboard/growth-summary")
        data = response.json()
        # CAC should be $40-60
        assert "40" in str(data["blended_cac"]) or "50" in str(data["blended_cac"])
        # Payback around 5 months
        assert data["payback_period_avg"] == "5 months"


class TestGrowthAmplification:
    def test_social_proof_amplification(self):
        from app.domains.fomo.foom_amplification import SocialProofAmplification

        assets = SocialProofAmplification.generate_social_proof_assets()
        assert "proof_types" in assets
        assert "user_count" in assets["proof_types"]
        assert "revenue_generated" in assets["proof_types"]

    def test_scarcity_automation(self):
        from app.domains.fomo.foom_amplification import ScarcityAutomation

        triggers = ScarcityAutomation.create_scarcity_triggers()
        assert "seat_scarcity" in triggers
        assert triggers["seat_scarcity"]["pricing_escalation"]["0-20%_occupied"] == "$99/month"
        assert triggers["seat_scarcity"]["pricing_escalation"]["95%+"] == "$299/month"

    def test_countdown_timers(self):
        from app.domains.fomo.foom_amplification import ScarcityAutomation

        timers = ScarcityAutomation.create_countdown_timers()
        assert "trial_countdown" in timers
        assert len(timers["trial_countdown"]["messaging_progression"]) >= 4

    def test_success_story_angles(self):
        from app.domains.fomo.foom_amplification import SuccessStoryPackaging

        angles = SuccessStoryPackaging.create_success_story_angles()
        assert len(angles) >= 6
        angle_names = [a["angle"] for a in angles]
        assert "The ROI Story" in angle_names
        assert "The Automation Story" in angle_names

    def test_content_repurposing(self):
        from app.domains.fomo.foom_amplification import SuccessStoryPackaging

        repurposing = SuccessStoryPackaging.create_content_repurposing()
        assert len(repurposing["output_formats"]) >= 20

    def test_competitive_positioning(self):
        from app.domains.fomo.foom_amplification import CompetitivePositioning

        positioning = CompetitivePositioning.create_comparison_content()
        assert len(positioning["comparisons"]) >= 4
        vs_targets = [c["vs"] for c in positioning["comparisons"]]
        assert any("Shopify" in v for v in vs_targets)

    def test_vip_program(self):
        from app.domains.fomo.foom_amplification import ExclusivityTiering

        vip = ExclusivityTiering.create_vip_program()
        assert len(vip["tiers"]) == 4
        tier_names = [t["tier"] for t in vip["tiers"]]
        assert "Pro" in tier_names
        assert "Founder" in tier_names
        assert "Enterprise" in tier_names

    def test_fomo_sequences(self):
        from app.domains.fomo.foom_amplification import FearOfMissingOut

        sequences = FearOfMissingOut.create_fomo_sequences()
        assert "signup_fomo" in sequences
        assert "trial_countdown_fomo" in sequences
        assert "competitor_fomo" in sequences


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
