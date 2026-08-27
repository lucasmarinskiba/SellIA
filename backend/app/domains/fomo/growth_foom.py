"""
Growth FOOM: Acquisition channels to attract users to SellIA
- Organic SEO + viral loops
- Press + PR automation
- Influencer seeding
- Case studies + results proof
- Referral mechanics
- Partnership integrations
- Waitlist FOMO
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID
import asyncio


class SeoFOOMService:
    """SEO + Organic search optimization"""

    @staticmethod
    async def generate_seo_content_calendar(
        days: int = 90,
    ) -> List[Dict]:
        """
        Generate 90-day SEO content calendar targeting high-intent keywords
        Focus: Problem-solution-result narrative
        """

        content_plan = [
            # Week 1: Problem awareness
            {
                "week": 1,
                "title": "¿Por qué tus clientes no compran? 5 razones científicas",
                "keyword": "aumentar conversiones tienda online",
                "type": "blog",
                "format": "long-form (3000 words)",
                "cta": "Free conversion audit",
            },
            {
                "week": 1,
                "title": "El costo de NO tener automatización de ventas",
                "keyword": "automatizar ventas online",
                "type": "blog",
                "format": "case study + math",
                "cta": "See ROI calculator",
            },

            # Week 2: Solution intro
            {
                "week": 2,
                "title": "¿Cómo SellIA aumentó las ventas de Ana García 340%?",
                "keyword": "aumentar ventas ecommerce",
                "type": "case_study",
                "format": "video + blog",
                "metrics": "+340% conversiones, +$45K/mes",
                "cta": "Start free trial",
            },
            {
                "week": 2,
                "title": "Comparativa: SellIA vs Shopify, WooCommerce, Klaviyo",
                "keyword": "mejor herramienta ecommerce 2026",
                "type": "comparison",
                "format": "interactive table",
                "cta": "Try free for 14 days",
            },

            # Week 3-4: Social proof at scale
            {
                "week": 3,
                "title": "Testimonios: 47 usuarios comparten resultados reales",
                "keyword": "reviews SellIA",
                "type": "testimonials",
                "format": "video collage",
                "cta": "Join 15K+ happy users",
            },
            {
                "week": 4,
                "title": "Awards & Recognition: 'Best AI Sales Tool 2026'",
                "keyword": "best sales automation tool",
                "type": "awards",
                "format": "press release",
                "cta": "See all awards",
            },

            # Week 5-8: Problem-specific content
            {
                "week": 5,
                "title": "Cart Abandonment: Recover $X por mes (sin coding)",
                "keyword": "recuperar carritos abandonados",
                "type": "how-to",
                "format": "step-by-step guide",
                "estimated_results": "+20-35% recovery",
                "cta": "Try free",
            },
            {
                "week": 6,
                "title": "Email Marketing Automation: Template + Setup (2 horas)",
                "keyword": "automatizar email marketing",
                "type": "tutorial",
                "format": "video tutorial",
                "cta": "Copy template",
            },
            {
                "week": 7,
                "title": "¿Tus competidores usan AI? Acá están todas (mapa interactivo)",
                "keyword": "competencia ecommerce",
                "type": "research",
                "format": "interactive tool",
                "cta": "See competitor analysis",
            },
            {
                "week": 8,
                "title": "Multiplicar conversiones: Playbook de 30 días",
                "keyword": "playbook conversiones",
                "type": "playbook",
                "format": "PDF guide",
                "cta": "Download free",
            },
        ]

        return content_plan

    @staticmethod
    async def optimize_for_serp_features(
        content_type: str,
    ) -> Dict:
        """
        Optimize content to rank in Google SERP features:
        - Featured snippets (FAQ schema)
        - People also ask
        - Video carousel
        - Top stories
        """

        optimizations = {
            "case_study": {
                "schema": "Article + LocalBusiness",
                "faq_block": 5,  # 5 FAQ blocks for PAA
                "video_embed": True,
                "testimonial_schema": True,
                "aggregate_rating": "4.8/5 stars",
            },
            "comparison": {
                "schema": "Table + Compare",
                "structured_data": "Product comparison",
                "featured_snippet_target": "Comparison table (position 0)",
                "video_demo": True,
            },
            "how_to": {
                "schema": "HowTo",
                "step_count": 8,
                "estimated_time": "15 min read",
                "video_per_step": True,
                "featured_snippet_target": "Step-by-step",
            },
        }

        return optimizations.get(content_type, {})


class ViralLoopsService:
    """Viral mechanics: referrals, word-of-mouth, community"""

    @staticmethod
    async def create_referral_program() -> Dict:
        """
        2-sided referral program:
        Referrer gets $50 credit + Pro month free
        New user gets 30% OFF first month
        """

        return {
            "name": "SellIA Referral Program",
            "referrer_reward": {
                "cash_credit": 50,
                "free_plan_months": 1,
                "exclusive_feature_early_access": True,
            },
            "referee_reward": {
                "discount_percent": 30,
                "trial_extension_days": 14,
                "bonus_templates": 20,
            },
            "viral_coefficient": 1.8,  # Each user refers 1.8 others
            "payback_period_days": 14,
            "mechanics": {
                "share_link": "sellsia.io/ref/{user_id}",
                "viral_trigger": "First successful campaign",
                "reminder_frequency": "Weekly email",
                "social_share": True,  # Easy share to Twitter, LinkedIn
            },
        }

    @staticmethod
    async def create_community_program() -> Dict:
        """
        Discord/Slack community for users to share wins
        Gamification: leaderboards, badges, exclusive perks
        """

        return {
            "platform": "Discord + Slack",
            "channels": [
                "wins-and-case-studies",
                "strategy-discussion",
                "product-roadmap",
                "early-access-beta",
                "help-and-support",
            ],
            "gamification": {
                "leaderboards": "By conversion increase %",
                "badges": ["First sale", "100K revenue", "$1M milestone"],
                "perks": {
                    "top_10_monthly": "Free Pro plan upgrade",
                    "most_helpful": "Exclusive training session",
                    "ambassador": "Revenue share + early features",
                },
            },
            "ugc_campaign": {
                "hashtag": "#SellIAWins",
                "repost_best": True,
                "featured_users": "Monthly spotlight",
                "incentive": "$100 credit for best story",
            },
        }

    @staticmethod
    async def create_waitlist_fomo() -> Dict:
        """
        Pre-launch/new feature waitlist with scarcity messaging
        Limited early access, pricing locks, exclusive bonuses
        """

        return {
            "features": [
                "Limited spots (first 100)",
                "Lifetime 50% OFF pricing lock",
                "Exclusive early access (72h before public)",
                "Direct access to product team",
                "Private training sessions",
                "Custom integrations",
            ],
            "messaging": {
                "main": "Be in the first 100. Lock in 50% OFF forever.",
                "urgency": "Only {spots_left} spots left",
                "exclusivity": "Early access member benefits",
                "social_proof": "{count} have joined",
            },
            "mechanics": {
                "email_sequence": 5,  # 5-email nurture
                "sms_alerts": True,  # When spots fill up
                "progress_bar": True,  # Visual scarcity
                "referral_boost": "Each referral = +1 spot reserved",
            },
        }


class CaseStudyFOOMService:
    """Generate case studies proving real results"""

    @staticmethod
    async def generate_case_study_from_user(
        user_id: UUID,
        before_metrics: Dict,
        after_metrics: Dict,
        industry: str,
        business_size: str,
    ) -> Dict:
        """
        Transform user success into case study
        Calculate % improvement for FOMO narrative
        """

        cr_improvement = (
            (after_metrics["conversion_rate"] - before_metrics["conversion_rate"])
            / before_metrics["conversion_rate"]
            * 100
        )
        revenue_improvement = (
            (after_metrics["monthly_revenue"] - before_metrics["monthly_revenue"])
            / before_metrics["monthly_revenue"]
            * 100
        )

        case_study = {
            "title": f"How {before_metrics.get('business_name', 'This Business')} Increased Conversions {cr_improvement:.0f}%",
            "before_after": {
                "before": before_metrics,
                "after": after_metrics,
                "improvements": {
                    "conversion_rate_percent": f"+{cr_improvement:.0f}%",
                    "monthly_revenue": f"+${after_metrics['monthly_revenue'] - before_metrics['monthly_revenue']:,.0f}",
                    "monthly_revenue_percent": f"+{revenue_improvement:.0f}%",
                    "aov_increase": f"+${after_metrics.get('aov', 0) - before_metrics.get('aov', 0):.0f}",
                },
            },
            "testimonial": {
                "quote": "SellIA transformed how I sell. No technical skills needed.",
                "name": before_metrics.get("owner_name", "Happy Customer"),
                "title": "Business Owner",
                "photo": f"https://cdn.sellsia.com/avatars/{user_id}.jpg",
                "rating": 5,
            },
            "format_types": [
                "Blog post (2000 words)",
                "Video case study (5 min)",
                "Infographic",
                "LinkedIn article",
                "Podcast interview",
            ],
            "distribution": {
                "blog": True,
                "landing_page": True,
                "email_sequence": 3,
                "social_media": ["LinkedIn", "Twitter", "Instagram"],
                "slack_community": True,
                "press_release": True,
            },
        }

        return case_study


class PressAndPRService:
    """Automated PR + press release generation"""

    @staticmethod
    async def generate_press_release(
        news_type: str,  # "milestone", "award", "feature", "funding", "partnership"
        details: Dict,
    ) -> Dict:
        """
        Auto-generate press releases to distribute to media
        """

        templates = {
            "milestone": {
                "headline": "SellIA Reaches {milestone_number} Users, ${milestone_revenue}M in Client Revenue",
                "lede": "AI-powered sales automation platform hits major adoption milestone",
                "boilerplate": "SellIA is a no-code platform that automates {feature}...",
                "quote": "We're democratizing enterprise sales technology...",
                "cta": "Try free at sellsia.io",
            },
            "award": {
                "headline": "SellIA Named 'Best AI Sales Tool 2026' by {publication}",
                "lede": "Industry recognition for innovation in sales automation",
                "quote": "This award validates our mission to...",
            },
            "feature": {
                "headline": "SellIA Launches {feature_name}: Increase Conversions by {expected_increase}%",
                "lede": "New feature powered by breakthrough AI...",
            },
            "partnership": {
                "headline": "SellIA Partners with {partner} to Expand Capabilities",
                "lede": "Integration brings {benefit} to users",
            },
        }

        press_release = {
            "content": templates.get(news_type, {}),
            "distribution_channels": [
                "PRWeb",
                "BusinessWire",
                "GlobeNewswire",
                "Crunchbase",
                "Product Hunt",
                "HackerNews",
                "Tech media (Forbes, TechCrunch, VentureBeat)",
                "Industry-specific press",
            ],
            "social_amplification": {
                "twitter_threads": 3,
                "linkedin_posts": 2,
                "instagram_reels": 1,
            },
            "follow_up": {
                "email_announcement": True,
                "product_update_blog": True,
                "webinar": "Live demo + Q&A",
                "podcast_outreach": True,
            },
        }

        return press_release

    @staticmethod
    async def create_influencer_seeding() -> Dict:
        """
        Seed SellIA with micro-influencers in ecommerce/entrepreneurship space
        Free Pro access + commission structure
        """

        return {
            "target_influencers": {
                "tier_1": {
                    "follower_range": "100K-500K",
                    "incentive": "Free Pro + 30% revenue share",
                    "commitment": "1 video/month + 2 posts",
                },
                "tier_2": {
                    "follower_range": "10K-100K",
                    "incentive": "Free Pro + 20% revenue share + exclusive features",
                    "commitment": "2 videos/month + weekly posts",
                },
                "tier_3": {
                    "follower_range": "<10K",
                    "incentive": "Free Pro + 10% revenue share + community spotlight",
                    "commitment": "Content + community engagement",
                },
            },
            "content_requirements": [
                "Before/after demos",
                "Case studies of their customers",
                "Tutorial/how-to content",
                "Comparison vs alternatives",
                "Personal success stories",
            ],
            "tracking": {
                "unique_link": "sellsia.io/ref/{influencer_name}",
                "commission_tracking": "Real-time dashboard",
                "top_performer_bonuses": "$1K/month",
            },
        }


class ProductLedGrowthService:
    """Product-led growth: free trial → paid conversion"""

    @staticmethod
    async def optimize_free_trial_foom() -> Dict:
        """
        14-day free trial with scarcity mechanics
        Limit features, show "upgrade" CTAs, create urgency
        """

        return {
            "trial_length_days": 14,
            "trial_limits": {
                "products": 10,
                "campaigns": 3,
                "api_calls": 1000,
                "support": "Community only",
            },
            "upsell_triggers": [
                {
                    "event": "Create 3rd campaign",
                    "message": "Upgrade to create unlimited campaigns",
                    "discount": "40% OFF first month",
                },
                {
                    "event": "Day 7 of trial",
                    "message": "You have 7 days left. Lock in 30% OFF",
                    "type": "email + in-app",
                },
                {
                    "event": "First successful automation",
                    "message": "Great job! Upgrade to keep running more automations",
                    "incentive": "Free $50 credit",
                },
                {
                    "event": "Day 13 (last day)",
                    "message": "Last chance: 50% OFF if you upgrade today",
                    "type": "aggressive (email + SMS + push)",
                },
            ],
            "conversion_optimization": {
                "trial_to_paid_target": "15-20%",
                "payback_period": 6,  # months
                "ltv_target": 1500,  # $1500
            },
        }

    @staticmethod
    async def create_feature_gates_for_fomo() -> Dict:
        """
        Gate premium features behind paywall
        Show "unlock" CTA with benefit messaging
        """

        features = {
            "free": [
                "1 automation",
                "10 products",
                "Basic email/SMS",
                "Community support",
            ],
            "pro": [
                "Unlimited automations",
                "Unlimited products",
                "Advanced AI + personalization",
                "Email + SMS + webhooks",
                "Email support",
                "API access",
                "Custom integrations",
            ],
            "enterprise": [
                "Everything in Pro",
                "Dedicated account manager",
                "SLA guarantee",
                "Custom development",
                "Training + onboarding",
                "Phone support 24/7",
            ],
        }

        gates = []
        for feature_name, benefit in [
            ("advanced_personalization", "Increase conversions by +40%"),
            ("webhook_automation", "Connect to any tool"),
            ("api_access", "Build custom integrations"),
            ("priority_support", "1-hour response time"),
            ("custom_branding", "White-label solution"),
        ]:
            gates.append({
                "feature": feature_name,
                "gate": "Pro plan required",
                "cta": f"Unlock {benefit}",
                "discount": "40% OFF first month",
            })

        return {
            "feature_tiers": features,
            "feature_gates": gates,
        }


class PartnershipFOOMService:
    """Partnerships for distribution + co-marketing"""

    @staticmethod
    async def create_partnerships() -> List[Dict]:
        """
        Partnership channels to amplify SellIA reach
        """

        return [
            {
                "partner_type": "E-commerce platforms",
                "examples": ["Shopify", "WooCommerce", "BigCommerce", "Wix"],
                "integration": "Native app in marketplace",
                "benefit": "Co-marketing + revenue share",
                "expected_mau": "+1000/month per platform",
            },
            {
                "partner_type": "Payment processors",
                "examples": ["Stripe", "Square", "MercadoPago"],
                "integration": "Plugin for checkout optimization",
                "benefit": "Increase conversion rates",
                "expected_mau": "+2000/month",
            },
            {
                "partner_type": "Email platforms",
                "examples": ["Mailchimp", "ConvertKit", "ActiveCampaign"],
                "integration": "2-way sync",
                "benefit": "Unified customer data",
                "expected_mau": "+1500/month",
            },
            {
                "partner_type": "CRM platforms",
                "examples": ["HubSpot", "Pipedrive", "Zoho"],
                "integration": "Contact + deal sync",
                "benefit": "Sales + marketing alignment",
                "expected_mau": "+2500/month",
            },
            {
                "partner_type": "Learning platforms",
                "examples": ["Skillshare", "MasterClass", "Udemy"],
                "integration": "Course on SellIA best practices",
                "benefit": "Passive referral channel",
                "expected_mau": "+500/month",
            },
            {
                "partner_type": "Agency networks",
                "examples": ["Shopify agencies", "WooCommerce agencies"],
                "integration": "White-label or affiliate",
                "benefit": "Recurring agency referrals",
                "expected_mau": "+1000/month",
            },
        ]


class ViralMechanicsService:
    """Growth hacks + viral loops"""

    @staticmethod
    async def create_viral_mechanics() -> Dict:
        """
        Built-in viral mechanics in SellIA product
        """

        return {
            "mechanics": [
                {
                    "name": "Public profile",
                    "desc": "Shareable success page (#{metric} increase)",
                    "incentive": "Featured on leaderboard",
                    "viral_coeff": 0.3,
                },
                {
                    "name": "Invite team members",
                    "desc": "Free account for each invite",
                    "incentive": "+1 seat reserve",
                    "viral_coeff": 2.1,
                },
                {
                    "name": "Achievement badges",
                    "desc": "Social share badges (1st sale, $1K revenue)",
                    "incentive": "Exclusive community status",
                    "viral_coeff": 0.8,
                },
                {
                    "name": "Refer a friend",
                    "desc": "$50 credit + PRO month",
                    "incentive": "Unlimited referral income",
                    "viral_coeff": 1.8,
                },
                {
                    "name": "Leaderboard competition",
                    "desc": "Monthly: highest CR increase wins $1K",
                    "incentive": "Status + cash",
                    "viral_coeff": 0.5,
                },
            ],
            "viral_coefficient_target": 1.5,  # Each user brings 1.5 more users
            "k_factor": 2.0,  # 2.0 = exponential growth
        }


class BrandBuildingService:
    """Long-term brand building for acquisition"""

    @staticmethod
    async def create_thought_leadership() -> Dict:
        """
        Position SellIA founder/team as experts
        """

        return {
            "channels": [
                {
                    "channel": "Podcast",
                    "format": "Weekly: "The SellIA Hour" with success stories",
                    "guests": "Top users + industry experts",
                    "distribution": "Spotify, Apple Podcasts, YouTube",
                    "expected_listeners": "10K+/week",
                },
                {
                    "channel": "YouTube",
                    "format": "Weekly tutorials + case studies + market analysis",
                    "seo_target": "How to [increase sales strategy]",
                    "expected_subs": "50K+ subs",
                },
                {
                    "channel": "Twitter",
                    "format": "Daily tips + live threads during major events",
                    "engagement": "High-value audience (founders, marketers)",
                },
                {
                    "channel": "Newsletter",
                    "format": "Weekly: market trends + customer wins + product updates",
                    "subscribers": "100K+ target",
                },
                {
                    "channel": "Speaking",
                    "format": "Conferences + webinars + summit keynotes",
                    "events": ["Growth Summit", "E-commerce Expo", "SaaS Conference"],
                },
            ],
            "brand_positioning": "The AI that sells for you",
            "target_audience": "Ambitious entrepreneurs + agencies + sellers",
        }
