"""30+ Affiliate Sales Methods — Proven tactics for promoting affiliate products."""

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AffiliateMethod:
    """Single affiliate sales method."""
    method_id: str
    name: str
    category: str  # email|content|paid|partnership|organic|social|community
    effort_level: int  # 1-10
    time_to_conversion: str  # days/weeks/months
    roi_potential: float  # 1-10
    best_for: List[str]  # product types/audiences
    description: str
    steps: List[str]


AFFILIATE_METHODS = {
    # EMAIL METHODS (5)
    "email_001": AffiliateMethod(
        method_id="email_001",
        name="Email List Monetization",
        category="email",
        effort_level=3,
        time_to_conversion="days",
        roi_potential=8.5,
        best_for=["digital_products", "courses", "software"],
        description="Convert existing email list into affiliate revenue by promoting relevant products",
        steps=["Build/acquire email list", "Segment by interest", "Create email series", "Test subject lines", "Track conversions"],
    ),
    "email_002": AffiliateMethod(
        method_id="email_002",
        name="Lead Magnet + Affiliate Pitch",
        category="email",
        effort_level=4,
        time_to_conversion="weeks",
        roi_potential=7.0,
        best_for=["courses", "training", "coaching"],
        description="Use lead magnet to build list, warm up subscribers, then promote affiliate offers",
        steps=["Create valuable lead magnet", "Build landing page", "Drive traffic", "Email nurture sequence", "Affiliate pitch"],
    ),
    "email_003": AffiliateMethod(
        method_id="email_003",
        name="Affiliate Review Email Series",
        category="email",
        effort_level=5,
        time_to_conversion="weeks",
        roi_potential=8.0,
        best_for=["software", "tools", "courses"],
        description="Multi-part email series reviewing product, addressing objections, demonstrating value",
        steps=["Write honest review", "Identify objections", "Create benefit-focused emails", "Add social proof", "CTA optimization"],
    ),
    "email_004": AffiliateMethod(
        method_id="email_004",
        name="Flash Sale Promotion",
        category="email",
        effort_level=2,
        time_to_conversion="days",
        roi_potential=9.0,
        best_for=["any"],
        description="Promote limited-time affiliate offers to list using urgency and scarcity",
        steps=["Identify flash sale", "Create urgency copy", "Multi-email blitz", "Track clicks", "Analyze results"],
    ),
    "email_005": AffiliateMethod(
        method_id="email_005",
        name="Affiliate Newsletter",
        category="email",
        effort_level=3,
        time_to_conversion="weeks",
        roi_potential=6.5,
        best_for=["tools", "resources", "courses"],
        description="Regular newsletter featuring curated affiliate products/tools",
        steps=["Create newsletter structure", "Select products", "Write reviews", "Build consistency", "Grow subscriber base"],
    ),

    # CONTENT METHODS (8)
    "content_001": AffiliateMethod(
        method_id="content_001",
        name="Blog Post + Internal Linking",
        category="content",
        effort_level=5,
        time_to_conversion="months",
        roi_potential=8.0,
        best_for=["tools", "software", "courses"],
        description="Write SEO-optimized blog posts naturally mentioning affiliate products",
        steps=["Keyword research", "Write 2000+ word post", "Optimize SEO", "Add affiliate links", "Build backlinks"],
    ),
    "content_002": AffiliateMethod(
        method_id="content_002",
        name="Product Comparison Articles",
        category="content",
        effort_level=6,
        time_to_conversion="months",
        roi_potential=8.5,
        best_for=["software", "tools", "services"],
        description="Write detailed comparison posts (A vs B vs C) with affiliate links",
        steps=["Select competitor products", "Test thoroughly", "Create comparison matrix", "Write detailed review", "Rank on Google"],
    ),
    "content_003": AffiliateMethod(
        method_id="content_003",
        name="Ultimate Guide + Affiliate Tools",
        category="content",
        effort_level=7,
        time_to_conversion="months",
        roi_potential=9.0,
        best_for=["courses", "tools", "services"],
        description="Comprehensive guide on topic, recommending affiliate tools/courses throughout",
        steps=["Choose guide topic", "Outline comprehensively", "Research + write", "Recommend tools naturally", "Optimize for SEO"],
    ),
    "content_004": AffiliateMethod(
        method_id="content_004",
        name="YouTube Affiliate Videos",
        category="content",
        effort_level=6,
        time_to_conversion="weeks",
        roi_potential=8.5,
        best_for=["any"],
        description="Review/demo affiliate products in YouTube videos with link in description",
        steps=["Script review", "Film video", "Edit professionally", "Add affiliate links in description", "Build audience"],
    ),
    "content_005": AffiliateMethod(
        method_id="content_005",
        name="TikTok/Reels Demo",
        category="content",
        effort_level=4,
        time_to_conversion="weeks",
        roi_potential=7.0,
        best_for=["digital_products", "tools"],
        description="Quick demo/review of products on TikTok/Reels with link in bio",
        steps=["Create demo script", "Film short clip", "Edit for platform", "Post consistently", "Drive to link in bio"],
    ),
    "content_006": AffiliateMethod(
        method_id="content_006",
        name="Podcast Episodes",
        category="content",
        effort_level=5,
        time_to_conversion="weeks",
        roi_potential=7.5,
        best_for=["courses", "coaching", "digital_products"],
        description="Dedicated episodes reviewing/discussing affiliate products",
        steps=["Script episode", "Record audio", "Edit + publish", "Mention links in show notes", "Build audience"],
    ),
    "content_007": AffiliateMethod(
        method_id="content_007",
        name="Free Masterclass/Webinar",
        category="content",
        effort_level=6,
        time_to_conversion="weeks",
        roi_potential=8.0,
        best_for=["courses", "coaching"],
        description="Free training event promoting relevant affiliate products",
        steps=["Create valuable content", "Promote webinar", "Deliver masterclass", "Pitch affiliate offer", "Follow up"],
    ),
    "content_008": AffiliateMethod(
        method_id="content_008",
        name="Curated Resource List",
        category="content",
        effort_level=3,
        time_to_conversion="weeks",
        roi_potential=6.0,
        best_for=["tools", "resources"],
        description="Popular resource list/roundup featuring affiliate products",
        steps=["Choose category", "Research products", "Write descriptions", "Build landing page", "Promote"],
    ),

    # PAID ADVERTISING METHODS (6)
    "paid_001": AffiliateMethod(
        method_id="paid_001",
        name="Facebook/Instagram Ads",
        category="paid",
        effort_level=6,
        time_to_conversion="days",
        roi_potential=7.5,
        best_for=["courses", "digital_products"],
        description="Targeted ads driving to affiliate product landing pages",
        steps=["Create ad creatives", "Set up pixels", "Target audience", "Optimize bids", "Track ROAS"],
    ),
    "paid_002": AffiliateMethod(
        method_id="paid_002",
        name="Google Ads (Search)",
        category="paid",
        effort_level=7,
        time_to_conversion="days",
        roi_potential=8.0,
        best_for=["software", "tools", "courses"],
        description="High-intent search ads targeting product keywords",
        steps=["Keyword research", "Write ads", "Create landing page", "Set bid strategy", "Monitor conversions"],
    ),
    "paid_003": AffiliateMethod(
        method_id="paid_003",
        name="Google Ads (Display)",
        category="paid",
        effort_level=5,
        time_to_conversion="weeks",
        roi_potential=6.5,
        best_for=["any"],
        description="Retargeting and contextual display ads for affiliate products",
        steps=["Design banner ads", "Set up audiences", "Choose placements", "Optimize CTR", "Track conversions"],
    ),
    "paid_004": AffiliateMethod(
        method_id="paid_004",
        name="Pinterest Ads",
        category="paid",
        effort_level=4,
        time_to_conversion="weeks",
        roi_potential=7.0,
        best_for=["home", "fashion", "beauty", "digital_products"],
        description="Pinterest ads with affiliate links in Pins",
        steps=["Design pins", "Create affiliate landing page", "Set up ads", "Target keywords", "Optimize bids"],
    ),
    "paid_005": AffiliateMethod(
        method_id="paid_005",
        name="LinkedIn Ads",
        category="paid",
        effort_level=5,
        time_to_conversion="weeks",
        roi_potential=7.0,
        best_for=["B2B", "courses", "software"],
        description="B2B-focused ads targeting professionals",
        steps=["Define target audience", "Create professional ads", "Target by role/industry", "Monitor CTR", "Track leads"],
    ),
    "paid_006": AffiliateMethod(
        method_id="paid_006",
        name="Influencer Paid Partnerships",
        category="paid",
        effort_level=6,
        time_to_conversion="days",
        roi_potential=8.5,
        best_for=["any"],
        description="Pay micro/macro influencers to promote affiliate offers",
        steps=["Find influencers", "Negotiate rates", "Send product/info", "Track promo code", "Measure ROI"],
    ),

    # PARTNERSHIP METHODS (5)
    "partnership_001": AffiliateMethod(
        method_id="partnership_001",
        name="Joint Venture (Revenue Share)",
        category="partnership",
        effort_level=7,
        time_to_conversion="weeks",
        roi_potential=9.0,
        best_for=["any"],
        description="Partner with complementary business for revenue split",
        steps=["Identify partner", "Negotiate terms", "Create offer", "Coordinate launch", "Track results"],
    ),
    "partnership_002": AffiliateMethod(
        method_id="partnership_002",
        name="Bundle/Affiliate Cross-Promotion",
        category="partnership",
        effort_level=5,
        time_to_conversion="days",
        roi_potential=8.0,
        best_for=["digital_products"],
        description="Bundle multiple affiliate products together",
        steps=["Select products", "Negotiate bundle", "Create landing page", "Promote bundle", "Track conversions"],
    ),
    "partnership_003": AffiliateMethod(
        method_id="partnership_003",
        name="Affiliate Network Participation",
        category="partnership",
        effort_level=3,
        time_to_conversion="weeks",
        roi_potential=6.5,
        best_for=["any"],
        description="Join affiliate networks and promote through network",
        steps=["Join network", "Find products", "Get links", "Promote via channels", "Track commissions"],
    ),
    "partnership_004": AffiliateMethod(
        method_id="partnership_004",
        name="Agency/Marketing Partner Referrals",
        category="partnership",
        effort_level=4,
        time_to_conversion="weeks",
        roi_potential=7.5,
        best_for=["services"],
        description="Partner with agencies/consultants for referral commissions",
        steps=["Identify partners", "Create referral program", "Track referrals", "Pay commissions", "Build relationships"],
    ),
    "partnership_005": AffiliateMethod(
        method_id="partnership_005",
        name="Reseller Agreements",
        category="partnership",
        effort_level=6,
        time_to_conversion="weeks",
        roi_potential=8.5,
        best_for=["digital_products", "courses"],
        description="Resell products at discount, keep markup as profit",
        steps=["Negotiate discount", "Create storefront", "Market products", "Handle sales", "Pay wholesale"],
    ),

    # ORGANIC METHODS (5)
    "organic_001": AffiliateMethod(
        method_id="organic_001",
        name="SEO Blog Domination",
        category="organic",
        effort_level=8,
        time_to_conversion="months",
        roi_potential=9.5,
        best_for=["any"],
        description="Dominate search for product keywords organically",
        steps=["Keyword research", "Create content hub", "Internal linking", "Backlink building", "Monitor rankings"],
    ),
    "organic_002": AffiliateMethod(
        method_id="organic_002",
        name="YouTube Channel Building",
        category="organic",
        effort_level=7,
        time_to_conversion="months",
        roi_potential=8.5,
        best_for=["tools", "software", "courses"],
        description="Build YouTube channel, monetize with affiliate products",
        steps=["Choose niche", "Create content series", "Optimize for search", "Build subscribers", "Add affiliate links"],
    ),
    "organic_003": AffiliateMethod(
        method_id="organic_003",
        name="Community Building + Promotion",
        category="organic",
        effort_level=6,
        time_to_conversion="weeks",
        roi_potential=7.5,
        best_for=["any"],
        description="Build engaged community (Discord/Slack/Facebook Group), promote to community",
        steps=["Create community", "Grow members", "Build engagement", "Provide value", "Introduce affiliate offers"],
    ),
    "organic_004": AffiliateMethod(
        method_id="organic_004",
        name="Organic Social Media",
        category="organic",
        effort_level=5,
        time_to_conversion="weeks",
        roi_potential=6.5,
        best_for=["any"],
        description="Consistent social media posting mentioning affiliate products",
        steps=["Plan content calendar", "Create posts", "Engage followers", "Share affiliate offers", "Build following"],
    ),
    "organic_005": AffiliateMethod(
        method_id="organic_005",
        name="Guest Blogging + Links",
        category="organic",
        effort_level=5,
        time_to_conversion="weeks",
        roi_potential=7.0,
        best_for=["any"],
        description="Write guest posts including affiliate links",
        steps=["Find host blogs", "Pitch ideas", "Write posts", "Include affiliate links", "Build authority"],
    ),

    # SOCIAL METHODS (3)
    "social_001": AffiliateMethod(
        method_id="social_001",
        name="Instagram Stories + Swipe-Up",
        category="social",
        effort_level=3,
        time_to_conversion="days",
        roi_potential=6.5,
        best_for=["digital_products", "tools"],
        description="Promote affiliate products via Instagram Stories with swipe-up link",
        steps=["Create story", "Add swipe-up link", "Post consistently", "Track swipe-ups", "Optimize timing"],
    ),
    "social_002": AffiliateMethod(
        method_id="social_002",
        name="LinkedIn Posts + Comments",
        category="social",
        effort_level=4,
        time_to_conversion="weeks",
        roi_potential=7.0,
        best_for=["B2B", "courses"],
        description="Share insights with subtle affiliate product mentions on LinkedIn",
        steps=["Write thought leadership", "Mention products naturally", "Engage with comments", "Build network", "Track clicks"],
    ),
    "social_003": AffiliateMethod(
        method_id="social_003",
        name="Twitter/X Threads",
        category="social",
        effort_level=3,
        time_to_conversion="days",
        roi_potential=5.5,
        best_for=["digital_products", "tools"],
        description="Tweet threads discussing topics, recommending affiliate products",
        steps=["Write thread", "Add links", "Post thread", "Engage replies", "Track clicks"],
    ),

    # COMMUNITY METHODS (2)
    "community_001": AffiliateMethod(
        method_id="community_001",
        name="Forum/Reddit Recommendations",
        category="community",
        effort_level=4,
        time_to_conversion="weeks",
        roi_potential=6.0,
        best_for=["tools", "software"],
        description="Recommend affiliate products in relevant forums/Reddit with value-first approach",
        steps=["Find relevant communities", "Build reputation", "Answer questions", "Recommend when relevant", "Disclose affiliate"],
    ),
    "community_002": AffiliateMethod(
        method_id="community_002",
        name="Slack/Discord Community Promotion",
        category="community",
        effort_level=3,
        time_to_conversion="weeks",
        roi_potential=6.5,
        best_for=["courses", "tools"],
        description="Promote to niche Slack/Discord communities where relevant",
        steps=["Join relevant communities", "Build presence", "Share resources", "Recommend products", "Track conversions"],
    ),
}


def get_methods_by_category(category: str) -> List[AffiliateMethod]:
    """Get all methods in a category."""
    return [m for m in AFFILIATE_METHODS.values() if m.category == category]


def get_best_methods_for_product(
    product_type: str, budget: Optional[str] = None
) -> List[AffiliateMethod]:
    """Get recommended methods for product type."""
    all_methods = list(AFFILIATE_METHODS.values())
    recommended = [m for m in all_methods if product_type in m.best_for]

    if budget == "low":
        recommended = [m for m in recommended if m.effort_level <= 4]
    elif budget == "medium":
        recommended = [m for m in recommended if 4 <= m.effort_level <= 7]
    elif budget == "high":
        recommended = [m for m in recommended if m.effort_level >= 6]

    return sorted(recommended, key=lambda x: x.roi_potential, reverse=True)


def get_fastest_methods() -> List[AffiliateMethod]:
    """Get fastest-to-conversion methods."""
    methods = list(AFFILIATE_METHODS.values())
    time_order = {"days": 1, "weeks": 2, "months": 3}

    return sorted(
        methods,
        key=lambda m: (
            time_order.get(m.time_to_conversion, 4),
            -m.roi_potential,
        ),
    )
