"""
FOOM Amplification: Aggressive FOOM mechanics for SellIA acquisition
- Social proof at scale
- Scarcity automation
- Success story packaging
- Fear-of-missing-out loops
- Competitive positioning
- Exclusivity tiering
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List
from decimal import Decimal


class SocialProofAmplification:
    """Amplify social proof signals across all channels"""

    @staticmethod
    def generate_social_proof_assets() -> Dict:
        """Generate social proof content for every FOOM touchpoint"""
        return {
            "proof_types": {
                "user_count": {
                    "stat": "15,340+ sellers trust SellIA",
                    "growth_rate": "+50% MoM",
                    "display": "Live counter on homepage",
                },
                "revenue_generated": {
                    "stat": "$2.3M+ generated for customers",
                    "growth_rate": "+$500K/month",
                    "display": "Live counter + testimonials",
                },
                "average_increase": {
                    "stat": "+42% average conversion increase",
                    "range": "10%-340%",
                    "display": "Case studies + testimonials",
                },
                "reviews": {
                    "rating": "4.8/5 stars",
                    "count": "3,284 reviews",
                    "platforms": ["G2", "Trustpilot", "ProductHunt"],
                },
                "awards": {
                    "awards": [
                        "Best AI Sales Tool 2026",
                        "Fastest Growing SaaS",
                        "Top 10 E-commerce Automation",
                    ],
                    "publications": ["TechCrunch", "VentureBeat", "Forbes"],
                },
                "logos": {
                    "enterprise_customers": "Shopify agencies, WooCommerce experts",
                    "integrations": "Stripe, MercadoPago, Mailchimp",
                    "affiliates": "50+ agencies, influencers",
                },
            },
            "distribution": {
                "homepage": "Live counters (users, revenue, reviews)",
                "landing_pages": "Social proof widgets + testimonials",
                "ads": "Social proof in ad creative",
                "email": "Social proof in sequences",
                "sms": "Achievement milestones",
                "social_media": "Daily proof posts",
                "community": "User success stories",
            },
        }

    @staticmethod
    def create_testimonial_automation() -> Dict:
        """Automate collection + distribution of testimonials"""
        return {
            "collection_triggers": [
                {
                    "trigger": "First successful campaign",
                    "timing": "Day 1",
                    "message": "Share your win on SellIA! 🎉",
                    "incentive": "Featured on leaderboard + $50 credit",
                },
                {
                    "trigger": "Reached $1K revenue milestone",
                    "timing": "Immediately",
                    "message": "You just made $1K! Video testimonial?",
                    "incentive": "$100 credit + exclusive features",
                },
                {
                    "trigger": "Reached 10,000 monthly revenue",
                    "timing": "Immediately",
                    "message": "Case study feature + revenue share opportunity",
                    "incentive": "$1K credit + ambassador program",
                },
            ],
            "formats": [
                "Text testimonial",
                "Video testimonial (30s-2min)",
                "Case study (5K words)",
                "LinkedIn recommendation",
                "Public review (G2, Trustpilot)",
            ],
            "distribution": {
                "website": "Homepage rotating testimonials",
                "landing_pages": "Specific case studies",
                "ads": "Video testimonials in ads",
                "email": "Weekly success stories",
                "social": "Instagram, TikTok, Twitter",
                "community": "User highlights",
            },
            "automation": {
                "request_timing": "Optimal moment detection",
                "content_editing": "AI video + text editing",
                "distribution": "Auto-post across channels",
                "tracking": "ROI measurement per testimonial",
            },
        }


class ScarcityAutomation:
    """Automate scarcity messaging across product"""

    @staticmethod
    def create_scarcity_triggers() -> Dict:
        """Real-time scarcity mechanics"""
        return {
            "seat_scarcity": {
                "mechanism": "Limited seats (100) for early access",
                "pricing_escalation": {
                    "0-20%_occupied": "$99/month",
                    "20-50%": "$119/month",
                    "50-80%": "$149/month",
                    "80-95%": "$199/month",
                    "95%+": "$299/month",
                },
                "messaging": {
                    "high_occupancy": "Only {seats} seats left",
                    "timer": "Price increases in {hours}",
                    "urgency": "Lock in $99 before prices rise",
                },
                "distribution": "Homepage + email + SMS",
            },
            "feature_scarcity": {
                "mechanism": "Early access for first 1K users",
                "features": [
                    "Advanced AI personalization (first 1K only)",
                    "Webhook automation (first 500 only)",
                    "Custom branding (limited to Pro+)",
                ],
                "messaging": "Get early access before prices increase",
            },
            "offer_scarcity": {
                "mechanism": "Limited-time discounts",
                "offers": [
                    {"discount": "30% OFF", "duration": "48 hours"},
                    {"discount": "40% OFF first 3 months", "limit": "first 100 signups"},
                    {"discount": "50% OFF annually", "limit": "early bird"},
                ],
            },
            "inventory_scarcity": {
                "mechanism": "Product-level stock indicators",
                "display": "Stock counts in user's dashboard",
                "automation_limits": "Trigger limits at 50%, 20%, 5% capacity",
            },
        }

    @staticmethod
    def create_countdown_timers() -> Dict:
        """Automated countdown urgency"""
        return {
            "trial_countdown": {
                "display": "Persistent countdown in app",
                "messaging_progression": [
                    {"day": 7, "message": "7 days left to lock in 30% OFF"},
                    {"day": 3, "message": "3 days left. Upgrade to $79/month"},
                    {"day": 1, "message": "Last day! 50% OFF if you upgrade today"},
                    {"hour": 1, "message": "60 minutes left. Act now."},
                ],
            },
            "offer_countdown": {
                "early_bird": "48-hour window for pricing lock",
                "flash_sale": "24-hour discount events (weekly)",
                "seasonal": "Launch + holiday countdowns",
            },
            "automation": {
                "sms_alerts": "3, 24, 1 hour before expiration",
                "email_sequence": "Escalating urgency",
                "push_notifications": "Mobile app alerts",
            },
        }


class SuccessStoryPackaging:
    """Package user wins as viral narratives"""

    @staticmethod
    def create_success_story_angles() -> List[Dict]:
        """Multiple angles for same success story"""
        return [
            {
                "angle": "The ROI Story",
                "hook": "Spent $100 on SellIA, made $10K in 30 days",
                "format": "Before/after + number visualization",
                "audience": "Cost-conscious sellers",
            },
            {
                "angle": "The Time-Saver Story",
                "hook": "Saved 20 hours/week on manual work",
                "format": "Video walkthrough + time tracking",
                "audience": "Busy entrepreneurs",
            },
            {
                "angle": "The Skill Story",
                "hook": "No marketing experience, but SellIA made me a pro",
                "format": "Interview + before/after metrics",
                "audience": "Non-technical sellers",
            },
            {
                "angle": "The Scale Story",
                "hook": "Grew from $10K to $100K/month revenue",
                "format": "Long-form case study + spreadsheets",
                "audience": "Growth-minded founders",
            },
            {
                "angle": "The First Sale Story",
                "hook": "Made first sale in 24 hours",
                "format": "Short video + celebration",
                "audience": "New sellers",
            },
            {
                "angle": "The Automation Story",
                "hook": "Running business on autopilot with workflows",
                "format": "Behind-the-scenes + setup guide",
                "audience": "Tech-savvy sellers",
            },
        ]

    @staticmethod
    def create_content_repurposing() -> Dict:
        """Repurpose one story across 20+ formats"""
        return {
            "source": "User case study (30 min interview)",
            "output_formats": [
                "Blog post (2000 words)",
                "LinkedIn article",
                "Twitter thread (20+ tweets)",
                "Email sequence (5 emails)",
                "Infographic",
                "Video testimonial (2 min)",
                "Video case study (15 min)",
                "YouTube shorts (5 x 30s clips)",
                "TikTok videos (5 x 15s)",
                "Instagram carousel (10 slides)",
                "Instagram stories (8 frames)",
                "Podcast episode (45 min)",
                "Podcast clips (5 x 60s)",
                "Webinar presentation",
                "Slide deck (40 slides)",
                "PDF guide",
                "Email template",
                "SMS testimonial",
                "Live stream highlights",
                "Community post",
            ],
            "distribution": {
                "timing": "Staggered releases (daily for 20 days)",
                "channels": "All owned + partner channels",
                "paid_amplification": "Ads for top 5 formats",
            },
        }


class CompetitivePositioning:
    """Position SellIA vs alternatives"""

    @staticmethod
    def create_comparison_content() -> Dict:
        """Aggressive comparison marketing"""
        return {
            "comparisons": [
                {
                    "vs": "Shopify native features",
                    "advantage": "10x more powerful AI",
                    "proof": "Customers see 3x better results",
                },
                {
                    "vs": "Klaviyo / email-only tools",
                    "advantage": "Omnichannel (email + SMS + web + social)",
                    "proof": "42% avg improvement vs single channel",
                },
                {
                    "vs": "Manual marketing",
                    "advantage": "Automate everything",
                    "proof": "Save 20 hours/week",
                },
                {
                    "vs": "Expensive agencies",
                    "advantage": "$99/month vs $5K/month",
                    "proof": "Better results at 1% cost",
                },
            ],
            "formats": [
                "Interactive comparison tool",
                "Blog comparison articles",
                "Video comparisons",
                "Spreadsheet comparisons",
                "Feature matrices",
            ],
            "messaging": "Why SellIA is the obvious choice",
        }


class ExclusivityTiering:
    """Create exclusivity ladder"""

    @staticmethod
    def create_vip_program() -> Dict:
        """VIP tiers with escalating benefits"""
        return {
            "tiers": [
                {
                    "tier": "Pro",
                    "price": "$99/month",
                    "benefits": ["Unlimited automations", "Email + SMS", "API"],
                    "exclusivity": "Standard tier",
                },
                {
                    "tier": "Pro+",
                    "price": "$199/month",
                    "benefits": ["Everything Pro", "Custom branding", "Priority support"],
                    "exclusivity": "For power users",
                    "limit": "500 users max",
                },
                {
                    "tier": "Founder",
                    "price": "$499/month",
                    "benefits": ["Everything Pro+", "Dedicated account manager", "Custom integrations"],
                    "exclusivity": "For top 100 users",
                    "limit": "100 users max",
                    "perks": "Revenue share, early features, board input",
                },
                {
                    "tier": "Enterprise",
                    "price": "Custom",
                    "benefits": ["Everything + custom everything", "SLA 99.9%", "Custom training"],
                    "exclusivity": "By invitation only",
                    "limit": "Handpicked",
                },
            ],
            "vip_benefits": {
                "founder_tier": {
                    "revenue_share": "10% of referred customer revenue",
                    "early_access": "New features 1 month early",
                    "community": "Exclusive Slack channel",
                    "events": "Quarterly mastermind (IRL)",
                    "perks": "$5K annual credit + free setup",
                },
            },
            "scarcity_messaging": {
                "pro_plus": "Limited to 500 users",
                "founder": "Limited to 100 users (89 left)",
                "enterprise": "Invite-only for top 1% performers",
            },
        }


class FearOfMissingOut:
    """Active FOMO loop creation"""

    @staticmethod
    def create_fomo_sequences() -> Dict:
        """Multi-touch FOMO sequences"""
        return {
            "signup_fomo": {
                "email_1": {
                    "timing": "Immediately",
                    "subject": "You just joined 15K sellers ✨",
                    "body": "See how they're making $10K/month",
                },
                "email_2": {
                    "timing": "Hour 2",
                    "subject": "Your first customer is waiting 🎯",
                    "body": "Start your first automation in 5 minutes",
                },
                "email_3": {
                    "timing": "Day 1",
                    "subject": "See what $50K/month sellers do",
                    "body": "3 automation strategies (copy-paste ready)",
                },
            },
            "trial_countdown_fomo": {
                "day_7": "Lock in 30% OFF before price jumps",
                "day_3": "3 days left for early bird pricing",
                "day_1": "Last day: 50% OFF expires tonight",
                "hour_1": "60 min left! Act now.",
            },
            "competitor_fomo": {
                "message": "Your competitors use SellIA",
                "proof": "See Shopify stores doing 10x better",
                "cta": "Don't get left behind",
            },
            "feature_access_foom": {
                "trigger": "User views competitor doing X with SellIA",
                "message": "Unlock this feature to compete",
                "cta": "Upgrade to see what you're missing",
            },
        }
