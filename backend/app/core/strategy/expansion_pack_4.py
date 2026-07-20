"""Expansion Pack 4: 30 Customer Acquisition Methods - Content, Ads, Referral, Viral with Real Metrics."""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum


class AcquisitionMethod(str, Enum):
    """Customer acquisition method identifiers (30 strategies)."""
    # Content-Driven (6)
    CONTENT_MARKETING_SEO = "acq_content_seo"
    BLOG_THOUGHT_LEADERSHIP = "acq_blog_thought_leadership"
    VIDEO_CONTENT_YOUTUBE = "acq_video_youtube"
    PODCAST_HOSTING = "acq_podcast"
    WEBINAR_MARKETING = "acq_webinar"
    EBOOK_LEAD_MAGNET = "acq_ebook_lead"

    # Paid Ads (6)
    GOOGLE_SEARCH_ADS = "acq_google_search"
    FACEBOOK_INSTAGRAM_ADS = "acq_facebook_instagram"
    LINKEDIN_ADS = "acq_linkedin"
    TIKTOK_ADS = "acq_tiktok"
    YOUTUBE_PREROLL = "acq_youtube_preroll"
    PROGRAMMATIC_DISPLAY = "acq_programmatic"

    # Referral & Viral (6)
    REFERRAL_PROGRAM = "acq_referral_program"
    AFFILIATE_MARKETING = "acq_affiliate"
    VIRAL_LOOPS = "acq_viral_loops"
    AMBASSADOR_PROGRAM = "acq_ambassador"
    INFLUENCER_MARKETING = "acq_influencer"
    USER_GENERATED_CONTENT = "acq_ugc"

    # Community & Organic (6)
    COMMUNITY_BUILDING = "acq_community"
    TWITTER_TRACTION = "acq_twitter"
    PRODUCT_HUNT = "acq_product_hunt"
    HACKER_NEWS = "acq_hacker_news"
    REDDIT_MARKETING = "acq_reddit"
    LINKEDIN_NETWORK = "acq_linkedin_network"

    # Growth Hacking (6)
    VIRAL_PRODUCT_FEATURE = "acq_viral_feature"
    EMAIL_SEQUENCES = "acq_email"
    PARTNERSHIP_SWAPS = "acq_partnerships"
    GIVEAWAY_CONTESTS = "acq_giveaway"
    FREE_TIER_CONVERSION = "acq_free_to_paid"
    GROWTH_EXPERIMENTS = "acq_growth_experiments"


@dataclass
class AcquisitionMethodDetail:
    """Complete acquisition method with implementation and case studies."""
    method_id: AcquisitionMethod
    name: str
    description: str
    category: str  # content, paid, referral, community, growth

    # Real Case Studies
    case_study_1: Dict[str, Any]
    case_study_2: Dict[str, Any]
    case_study_3: Dict[str, Any]

    # Acquisition Funnel
    top_of_funnel_reach: str  # How many impressions/reach
    conversion_rate_typical: float  # % to customer
    customer_cost: Dict[str, str]  # CAC range
    customer_quality: str  # Retention, LTV characteristics

    # Performance Metrics
    time_to_first_customer: str  # How long to first result
    scalability: str  # Can it scale? (limited, scalable, highly scalable)
    predictability: str  # Is ROI predictable? (unpredictable, moderately predictable, predictable)
    required_budget: str  # Investment needed

    # Implementation
    implementation_steps: List[str]
    required_skills: List[str]
    required_tools: List[str]
    resource_investment: Dict[str, str]  # time, budget, people

    # Real Companies Using
    companies_using: List[str]  # Companies successfully using this

    # Metrics & ROI
    typical_cac: str  # Customer acquisition cost range
    typical_ltv: str  # Expected lifetime value
    ltv_to_cac_ratio: float  # Typical ratio (>3 is good)
    payback_period_months: int
    typical_roi: float  # Expected ROI %

    # Applicability
    best_for_industries: List[str]
    best_for_business_models: List[str]
    best_for_stage: str  # startup, growth, scale
    best_for_budget: str  # small, medium, large
    best_for_geography: str  # domestic, international, global

    # Difficulty & Competitive Advantage
    difficulty_score: float  # 1-10
    competitive_advantage_duration: str
    trend_trajectory: str  # Emerging, mature, declining


# ============================================================================
# CONTENT-DRIVEN ACQUISITION (6)
# ============================================================================

CONTENT_MARKETING_SEO = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.CONTENT_MARKETING_SEO,
    name="Content Marketing + SEO (Organic Search)",
    description="Create valuable content that ranks in Google for high-intent keywords. Long-term, compounding ROI.",

    category="content",

    case_study_1={
        "company": "HubSpot",
        "strategy": "1000+ blog posts targeting buyer keywords",
        "result": "$1.7B+ ARR; 60%+ of traffic from organic search",
        "timeline": "5+ years of consistent content",
        "blog_traffic": "10M+ monthly visitors to blog",
        "roi": "1000%+ ROI but takes 2+ years to compound",
        "key_success": "Pillar topics + cluster content strategy",
    },

    case_study_2={
        "company": "Moz",
        "strategy": "SEO education content + tools",
        "result": "$100M+ valuation driven by organic",
        "timeline": "7+ years of content investment",
        "organic_revenue": "70%+ of leads from organic search",
        "key_success": "Authority in SEO space drove trust",
    },

    case_study_3={
        "company": "Neil Patel",
        "strategy": "High-volume SEO blog + tools",
        "result": "$100M+ personal brand valuation",
        "timeline": "10+ years of content",
        "organic_reach": "50M+ annual organic visitors",
        "key_success": "Consistent, high-quality content",
    },

    top_of_funnel_reach="Unlimited; millions of potential impressions through search",
    conversion_rate_typical=0.02,  # 2% typical conversion (low intent + mix)
    customer_cost={"min": "$0 (organic)", "avg": "$50-200 CAC", "max": "$500"},
    customer_quality="High-intent customers; longer LTV",

    time_to_first_customer="3-6 months minimum",
    scalability="highly scalable",
    predictability="moderately predictable",
    required_budget="$5k-50k/month for consistent execution",

    implementation_steps=[
        "Research high-intent keywords in your space",
        "Create pillar content (10k+ words) for each topic",
        "Create cluster content supporting pillars",
        "Build backlinks through PR, partnerships, guest posting",
        "Optimize for search (technical SEO)",
        "Publish consistently (2-4 posts/week)",
        "Monitor rankings and iterate",
        "Measure organic traffic and conversion",
    ],

    required_skills=[
        "SEO expertise",
        "Content writing",
        "Keyword research",
        "Link building",
        "Analytics",
    ],

    required_tools=[
        "SEO tool (Ahrefs, SEMrush, Moz)",
        "Keyword research tool",
        "Content management system",
        "Google Analytics",
        "Search Console",
    ],

    resource_investment={
        "content_writers": "2-3 writers",
        "seo_expert": "1 full-time SEO",
        "editorial": "Part-time editor",
        "budget": "$5k-50k/month",
    },

    companies_using=["HubSpot", "Moz", "Neil Patel", "Buffer", "Unbounce", "Reforge"],

    typical_cac="$50-200 (very low over time)",
    typical_ltv="$5k-50k (high-intent customers)",
    ltv_to_cac_ratio=25.0,  # Excellent ratio after compounding
    payback_period_months=12,  # Takes ~12 months to reach profitability
    typical_roi=10.0,  # 1000% ROI but over 2-3 years

    best_for_industries=["SaaS", "software", "professional_services", "B2B"],
    best_for_business_models=["SaaS", "B2B", "content"],
    best_for_stage="growth, scale",
    best_for_budget="medium, large",
    best_for_geography="global",

    difficulty_score=6.0,
    competitive_advantage_duration="3-5 years",
    trend_trajectory="mature; increasingly competitive",
)

BLOG_THOUGHT_LEADERSHIP = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.BLOG_THOUGHT_LEADERSHIP,
    name="Blog + Thought Leadership (Industry Authority)",
    description="Become known expert in your space. Blog + speaking + media creates inbound.",

    category="content",

    case_study_1={
        "company": "Lenny Rachitsky (Reforge founder)",
        "strategy": "Weekly newsletter on product management",
        "result": "150k+ subscribers; $20M+ Reforge valuation",
        "timeline": "4+ years of consistent content",
        "roi": "ROI immeasurable but core to brand",
        "key_success": "Consistent, high-quality insights",
    },

    case_study_2={
        "company": "Paul Graham (Y Combinator)",
        "strategy": "Essays on startups, technology",
        "result": "Y Combinator became dominant accelerator",
        "timeline": "20+ years of essays",
        "impact": "Shaped entire startup industry",
    },

    case_study_3={
        "company": "Andrew Chen (Sapience VC)",
        "strategy": "Viral blog posts on growth metrics",
        "result": "Became product/growth thought leader",
        "inbound": "Led to VC career and opportunities",
    },

    top_of_funnel_reach="Direct reach to followers + viral if hit",
    conversion_rate_typical=0.05,  # 5% (higher intent from thought leadership)
    customer_cost={"min": "$100", "avg": "$200-500", "max": "$1000"},
    customer_quality="Highest quality; loyal to thought leader",

    time_to_first_customer="6-12 months for credibility",
    scalability="scalable with leverage",
    predictability="unpredictable (viral potential)",
    required_budget="$2k-10k/month",

    implementation_steps=[
        "Identify unique POV in your space",
        "Start blog/newsletter with consistent cadence",
        "Share original insights and data",
        "Engage on social media (Twitter, LinkedIn)",
        "Appear on podcasts and speak at events",
        "Build email list",
        "Occasionally go viral with polarizing takes",
    ],

    required_skills=["Writing", "Unique POV", "Public speaking", "Data analysis"],
    required_tools=["Substack/Medium", "Twitter/LinkedIn", "Email tool", "Analytics"],

    resource_investment={
        "content": "10-20 hours/week",
        "events": "Speaking opportunities",
        "budget": "$2k-10k/month",
    },

    companies_using=["Lenny Rachitsky", "Paul Graham", "Andrew Chen", "Marc Andreessen", "Naval Ravikant"],

    typical_cac="$200-500",
    typical_ltv="$10k-100k+",
    ltv_to_cac_ratio=20.0,
    payback_period_months=9,
    typical_roi=5.0,

    best_for_industries=["B2B", "SaaS", "consulting"],
    best_for_business_models=["B2B", "B2C"],
    best_for_stage="any",
    best_for_budget="small, medium",
    best_for_geography="global",

    difficulty_score=7.0,
    competitive_advantage_duration="3-5 years",
    trend_trajectory="emerging; increasingly valuable",
)

VIDEO_CONTENT_YOUTUBE = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.VIDEO_CONTENT_YOUTUBE,
    name="Video Content + YouTube Channel",
    description="YouTube is second-largest search engine. Video content highly engaging, shareable, algorithmic reach.",

    category="content",

    case_study_1={
        "company": "Ali Abdaal (MedStudent turned creator)",
        "strategy": "Productivity/education YouTube channel",
        "result": "3M+ subscribers; creates digital products",
        "timeline": "5+ years of consistent uploads",
        "roi": "Ad revenue + product sales",
    },

    case_study_2={
        "company": "Wistia (video hosting SaaS)",
        "strategy": "Educational video content + SEO",
        "result": "$100M+ valuation; video education drove growth",
        "organic_reach": "1M+ views/month on educational content",
    },

    case_study_3={
        "company": "Skillshare",
        "strategy": "Creator economy platform",
        "result": "$500M+ valuation from YouTube-driven discovery",
        "content_reach": "Millions discover creators through platform",
    },

    top_of_funnel_reach="YouTube algorithm can surface to millions",
    conversion_rate_typical=0.03,  # 3% (video is engaging)
    customer_cost={"min": "$100", "avg": "$300-1000", "max": "$2000"},
    customer_quality="High engagement; brand fans",

    time_to_first_customer="6-12 months to build audience",
    scalability="highly scalable",
    predictability="unpredictable (algorithmic)",
    required_budget="$1k-10k/month",

    implementation_steps=[
        "Plan content pillar/niche",
        "Create 1-2 videos/week",
        "Optimize titles, descriptions, tags",
        "Engage with comments",
        "Collaborate with other creators",
        "Create playlists and series",
        "Link to products/services",
    ],

    required_skills=["Video production", "Scripting", "Editing", "SEO"],
    required_tools=["Camera", "Video editor (Adobe Premiere, Final Cut)", "YouTube Studio"],

    resource_investment={
        "video_production": "8-16 hours/week",
        "equipment": "$1k-5k",
        "budget": "$1k-10k/month",
    },

    companies_using=["MrBeast", "Ali Abdaal", "Wistia", "Skillshare", "Gamer communities"],

    typical_cac="$300-1000",
    typical_ltv="$10k-50k",
    ltv_to_cac_ratio=15.0,
    payback_period_months=12,
    typical_roi=3.0,

    best_for_industries=["education", "SaaS", "entertainment", "lifestyle"],
    best_for_business_models=["B2C", "creator", "education"],
    best_for_stage="growth, scale",
    best_for_budget="medium, large",
    best_for_geography="global",

    difficulty_score=6.5,
    competitive_advantage_duration="2-3 years",
    trend_trajectory="mature; increasingly competitive",
)

PODCAST_HOSTING = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.PODCAST_HOSTING,
    name="Podcast Hosting & Sponsorships",
    description="Own a podcast (inbound) or sponsor podcasts (outbound). High-engagement, loyal audiences.",

    category="content",

    case_study_1={
        "company": "Joe Rogan Experience",
        "strategy": "Podcast hosting with sponsorships",
        "result": "$100M+ Spotify deal; massive influence",
        "audience": "10M+ listeners per episode",
    },

    case_study_2={
        "company": "Y Combinator Podcast",
        "strategy": "Startup founder interviews",
        "result": "Inbound from founders wanting to pitch",
        "reach": "100k+ weekly listeners",
    },

    case_study_3={
        "company": "Software Engineering Daily",
        "strategy": "Tech interviews + sponsorships",
        "result": "Sponsorships generate revenue + leads",
        "audience": "500k+ monthly downloads",
    },

    top_of_funnel_reach="Loyal, engaged audiences",
    conversion_rate_typical=0.05,  # 5% (high engagement)
    customer_cost={"min": "$200", "avg": "$500-2000", "max": "$5000"},
    customer_quality="Very high quality; cult-like followers",

    time_to_first_customer="3-6 months to audience",
    scalability="scalable",
    predictability="predictable (sponsorships)",
    required_budget="$5k-20k/month",

    implementation_steps=[
        "Choose podcast format/topic",
        "Create 1-2 episodes/week",
        "Distribute to all platforms (Spotify, Apple, etc.)",
        "Promote on social media",
        "Secure sponsorships",
        "Create guest pipeline",
    ],

    required_skills=["Interviewing", "Audio production", "Community building"],
    required_tools=["Recording equipment", "Editing software", "Hosting platform (Podbean, Anchor)"],

    resource_investment={
        "production": "6-12 hours/week",
        "equipment": "$1k-5k",
        "budget": "$5k-20k/month",
    },

    companies_using=["Joe Rogan", "Y Combinator", "Software Engineering Daily", "Acquired", "Lenny Rachitsky"],

    typical_cac="$500-2000",
    typical_ltv="$10k-50k+",
    ltv_to_cac_ratio=10.0,
    payback_period_months=12,
    typical_roi=4.0,

    best_for_industries=["B2B", "SaaS", "professional_services"],
    best_for_business_models=["B2B"],
    best_for_stage="growth, scale",
    best_for_budget="medium, large",
    best_for_geography="global",

    difficulty_score=6.0,
    competitive_advantage_duration="2-3 years",
    trend_trajectory="mature",
)

WEBINAR_MARKETING = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.WEBINAR_MARKETING,
    name="Webinar Marketing (Live or Recorded)",
    description="Live educational webinars that lead to free trial or demo. High-conversion format.",

    category="content",

    case_study_1={
        "company": "Reforge",
        "strategy": "Educational webinars on growth/product",
        "result": "$50M+ valuation; webinars drive enrollment",
        "conversion": "15-25% of webinar attendees buy courses",
        "reach": "1000s attend per webinar",
    },

    case_study_2={
        "company": "HubSpot Academy",
        "strategy": "Free certification webinars",
        "result": "Lead generation engine; 100k+ learners",
        "conversion": "10-15% convert to HubSpot customers",
    },

    case_study_3={
        "company": "SaaS companies generally",
        "strategy": "Product webinars",
        "result": "20-30% typical conversion to trial",
        "roi": "3-5x ROI on webinar spend",
    },

    top_of_funnel_reach="500-5000 per webinar",
    conversion_rate_typical=0.15,  # 15% (high-intent attendance)
    customer_cost={"min": "$300", "avg": "$500-1500", "max": "$3000"},
    customer_quality="Very high; committed attendees",

    time_to_first_customer="1-2 weeks per webinar",
    scalability="highly scalable",
    predictability="very predictable",
    required_budget="$3k-15k/month",

    implementation_steps=[
        "Plan webinar topic (educational, not pitchy)",
        "Promote 2-4 weeks in advance",
        "Drive registrations via email, ads, social",
        "Deliver excellent content (70% value, 30% pitch)",
        "Follow up with attendees",
        "Repurpose recording for evergreen",
    ],

    required_skills=["Presenting", "Content creation", "Email marketing"],
    required_tools=["Webinar platform (Zoom, On24, WebininarJam)", "Email tool", "Promotion"],

    resource_investment={
        "content_prep": "20-40 hours per webinar",
        "promotion": "Ongoing",
        "budget": "$3k-15k per webinar",
    },

    companies_using=["Reforge", "HubSpot", "Drift", "ConvertKit", "Copier"],

    typical_cac="$500-1500",
    typical_ltv="$5k-20k",
    ltv_to_cac_ratio=10.0,
    payback_period_months=6,
    typical_roi=3.5,

    best_for_industries=["SaaS", "B2B", "education"],
    best_for_business_models=["SaaS", "B2B"],
    best_for_stage="growth, scale",
    best_for_budget="medium, large",
    best_for_geography="global",

    difficulty_score=5.0,
    competitive_advantage_duration="2-3 years",
    trend_trajectory="mature",
)

EBOOK_LEAD_MAGNET = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.EBOOK_LEAD_MAGNET,
    name="Ebook / Lead Magnet (Gated Content)",
    description="Free ebook in exchange for email. Build list and nurture with sequences.",

    category="content",

    case_study_1={
        "company": "ConvertKit",
        "strategy": "Creator economy ebooks as lead magnets",
        "result": "$150M+ valuation; ebooks built audience",
        "conversion": "30-40% of ebook downloaders to free trial",
    },

    case_study_2={
        "company": "Crazy Egg",
        "strategy": "Free heatmap research guide",
        "result": "Built to $100M+ valuation",
        "email_list": "Millions on email list",
    },

    case_study_3={
        "company": "Buffer",
        "strategy": "Social media strategy ebook",
        "result": "Built to $100M+ valuation",
        "reach": "100k+ ebook downloads",
    },

    top_of_funnel_reach="Viral; 10k-100k+ downloads",
    conversion_rate_typical=0.30,  # 30% of downloaders become leads
    customer_cost={"min": "$10", "avg": "$50-200", "max": "$500"},
    customer_quality="Medium-high; needs nurturing",

    time_to_first_customer="1-3 months with sequences",
    scalability="highly scalable",
    predictability="very predictable",
    required_budget="$2k-10k/month",

    implementation_steps=[
        "Create valuable, gated ebook (20-50 pages)",
        "Design landing page",
        "Promote via ads, social, email",
        "Drive downloads",
        "Build nurture sequence",
        "Convert to trial/customer",
    ],

    required_skills=["Content writing", "Design", "Email marketing"],
    required_tools=["Ebook creation tool", "Landing page builder", "Email tool"],

    resource_investment={
        "content": "40-80 hours",
        "design": "10-20 hours",
        "budget": "$2k-10k",
    },

    companies_using=["ConvertKit", "Crazy Egg", "Buffer", "Unbounce"],

    typical_cac="$50-200",
    typical_ltv="$5k-20k",
    ltv_to_cac_ratio=20.0,
    payback_period_months=6,
    typical_roi=5.0,

    best_for_industries=["SaaS", "digital products", "education"],
    best_for_business_models=["SaaS", "B2C"],
    best_for_stage="any",
    best_for_budget="small, medium",
    best_for_geography="global",

    difficulty_score=4.0,
    competitive_advantage_duration="1-2 years",
    trend_trajectory="mature",
)

# ============================================================================
# PAID ADS ACQUISITION (6)
# ============================================================================

GOOGLE_SEARCH_ADS = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.GOOGLE_SEARCH_ADS,
    name="Google Search Ads (SEM)",
    description="Pay-per-click ads on Google search results. Highest intent, but expensive.",

    category="paid",

    case_study_1={
        "company": "Slack",
        "strategy": "Google Ads for 'team chat' keywords",
        "result": "$2B+ revenue with paid ads as core channel",
        "cac": "$500-1500 typical for their deals",
        "roi": "3-5x ROAS typical",
    },

    case_study_2={
        "company": "Uber",
        "strategy": "Search ads for ride-sharing keywords",
        "result": "$100B+ valuation with paid ads core",
        "cac": "$50-200 per ride (aggregated)",
        "roi": "2-3x ROAS typical",
    },

    case_study_3={
        "company": "Amazon Ads (affiliate/seller)",
        "strategy": "Search ads for product keywords",
        "result": "$100B+ annual ad revenue",
        "roi": "2-8x ROAS depending on category",
    },

    top_of_funnel_reach="10M+ daily searches in competitive categories",
    conversion_rate_typical=0.05,  # 5% (high intent)
    customer_cost={"min": "$100", "avg": "$500-2000", "max": "$10000"},
    customer_quality="Very high intent; best customers",

    time_to_first_customer="Days",
    scalability="highly scalable",
    predictability="very predictable",
    required_budget="$5k-100k+/month",

    implementation_steps=[
        "Keyword research (high-intent keywords)",
        "Create ad copy and landing pages",
        "Set bid strategy",
        "Monitor ROAS and optimize",
        "Scale winners",
        "Cut losers",
    ],

    required_skills=["PPC", "Copywriting", "Analytics", "Conversion optimization"],
    required_tools=["Google Ads", "Analytics", "A/B testing tool", "Keyword research tool"],

    resource_investment={
        "setup": "20-40 hours",
        "management": "10-20 hours/week",
        "budget": "$5k-100k+/month",
    },

    companies_using=["Slack", "Uber", "Zoom", "HubSpot", "Salesforce"],

    typical_cac="$500-2000",
    typical_ltv="$10k-50k+",
    ltv_to_cac_ratio=5.0,  # Must be profitable
    payback_period_months=3,
    typical_roi=2.5,

    best_for_industries=["SaaS", "software", "commerce", "professional services"],
    best_for_business_models=["B2B", "B2C"],
    best_for_stage="growth, scale",
    best_for_budget="large",
    best_for_geography="US, developed countries",

    difficulty_score=6.0,
    competitive_advantage_duration="6-12 months",
    trend_trajectory="mature; increasingly competitive",
)

FACEBOOK_INSTAGRAM_ADS = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.FACEBOOK_INSTAGRAM_ADS,
    name="Facebook/Instagram Ads (Meta)",
    description="Demographic/interest targeting on Meta. Good for B2C, brand awareness, large audiences.",

    category="paid",

    case_study_1={
        "company": "Dollar Shave Club",
        "strategy": "Viral Facebook ads in early years",
        "result": "$1B acquisition by Unilever",
        "cac": "$20-50 very low CAC",
        "roi": "10-20x ROAS typical",
    },

    case_study_2={
        "company": "Glossier",
        "strategy": "Instagram ads to beauty audience",
        "result": "$1.2B+ valuation",
        "cac": "$30-100",
        "roi": "5-10x ROAS",
    },

    case_study_3={
        "company": "DTC Brands generally",
        "strategy": "Facebook/Instagram for direct sales",
        "result": "Most DTC brands built on Meta ads",
        "cac": "$20-100 typical",
        "roi": "3-8x ROAS typical",
    },

    top_of_funnel_reach="3B+ users across Meta platforms",
    conversion_rate_typical=0.02,  # 2% (interest-based targeting)
    customer_cost={"min": "$20", "avg": "$50-200", "max": "$1000"},
    customer_quality="Medium; requires strong creative",

    time_to_first_customer="Days",
    scalability="highly scalable",
    predictability="moderately predictable",
    required_budget="$2k-50k+/month",

    implementation_steps=[
        "Define audience (lookalike, interest-based)",
        "Create compelling ads (video, carousel, image)",
        "Test multiple creatives",
        "Scale winners",
        "Monitor CAC and ROAS",
    ],

    required_skills=["Creative direction", "Copywriting", "Audience targeting", "Analytics"],
    required_tools=["Facebook Ads Manager", "Creative tools", "Analytics"],

    resource_investment={
        "creative": "40-80 hours per month",
        "management": "10-15 hours/week",
        "budget": "$2k-50k+/month",
    },

    companies_using=["Dollar Shave Club", "Glossier", "Warby Parker", "Allbirds"],

    typical_cac="$50-200",
    typical_ltv="$500-5000",
    ltv_to_cac_ratio=10.0,
    payback_period_months=2,
    typical_roi=4.0,

    best_for_industries=["e-commerce", "B2C", "direct-to-consumer", "SaaS"],
    best_for_business_models=["B2C", "D2C"],
    best_for_stage="growth, scale",
    best_for_budget="medium, large",
    best_for_geography="global",

    difficulty_score=5.5,
    competitive_advantage_duration="6-12 months",
    trend_trajectory="mature; saturated",
)

LINKEDIN_ADS = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.LINKEDIN_ADS,
    name="LinkedIn Ads (B2B Targeting)",
    description="Ads targeting professionals by job title, industry, company. Best for B2B SaaS.",

    category="paid",

    case_study_1={
        "company": "Reforge",
        "strategy": "LinkedIn ads to product managers",
        "result": "$50M+ valuation",
        "cac": "$200-500",
        "roi": "3-5x typical",
    },

    case_study_2={
        "company": "HubSpot",
        "strategy": "LinkedIn ads for sales/marketing",
        "result": "$1.7B+ ARR with LinkedIn core",
        "cac": "$300-800",
        "roi": "3-5x",
    },

    case_study_3={
        "company": "Demand generation",
        "strategy": "LinkedIn targeting by job title",
        "result": "High-intent B2B leads",
        "roi": "2-4x typical",
    },

    top_of_funnel_reach="900M+ professionals on LinkedIn",
    conversion_rate_typical=0.03,  # 3% (professional targeting)
    customer_cost={"min": "$200", "avg": "$500-2000", "max": "$5000"},
    customer_quality="Very high quality B2B leads",

    time_to_first_customer="1-2 weeks",
    scalability="scalable",
    predictability="very predictable",
    required_budget="$5k-50k+/month",

    implementation_steps=[
        "Target by job title, industry, company size",
        "Create professional ad copy and creative",
        "Use lead gen forms or landing page",
        "Nurture leads with email sequences",
        "Track conversion to customer",
    ],

    required_skills=["B2B messaging", "LinkedIn platform", "Lead nurturing"],
    required_tools=["LinkedIn Ads", "Email tool", "CRM", "Analytics"],

    resource_investment={
        "setup": "20-30 hours",
        "management": "10-15 hours/week",
        "budget": "$5k-50k+/month",
    },

    companies_using=["Reforge", "HubSpot", "Salesforce", "Slack"],

    typical_cac="$500-2000",
    typical_ltv="$10k-100k+",
    ltv_to_cac_ratio=10.0,
    payback_period_months=6,
    typical_roi=3.5,

    best_for_industries=["SaaS", "enterprise software", "consulting", "professional services"],
    best_for_business_models=["B2B"],
    best_for_stage="growth, scale",
    best_for_budget="large",
    best_for_geography="US, developed countries",

    difficulty_score=6.0,
    competitive_advantage_duration="12 months",
    trend_trajectory="emerging; rapidly growing",
)

TIKTOK_ADS = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.TIKTOK_ADS,
    name="TikTok Ads",
    description="New but rapidly growing platform. Great for younger audiences, viral potential.",

    category="paid",

    case_study_1={
        "company": "Glossier",
        "strategy": "TikTok ads to Gen Z beauty",
        "result": "$1.2B+ valuation",
        "cac": "$20-50",
        "roi": "5-10x",
    },

    case_study_2={
        "company": "DTC brands",
        "strategy": "TikTok viral challenge campaigns",
        "result": "Viral growth at low CAC",
        "cac": "$10-30 typical",
        "roi": "8-20x typical",
    },

    case_study_3={
        "company": "Shein",
        "strategy": "TikTok influencer partnerships",
        "result": "$100B+ valuation",
        "reach": "Billions of views",
    },

    top_of_funnel_reach="1.5B+ active users globally",
    conversion_rate_typical=0.03,  # 3% (entertainment-based)
    customer_cost={"min": "$10", "avg": "$30-100", "max": "$500"},
    customer_quality="Younger audiences; high engagement",

    time_to_first_customer="Days if viral",
    scalability="highly scalable",
    predictability="unpredictable (viral)",
    required_budget="$1k-20k/month",

    implementation_steps=[
        "Create viral-worthy creative",
        "Target younger demographics",
        "Run TikTok Ads Manager campaigns",
        "Partner with creators",
        "Optimize for engagement",
    ],

    required_skills=["Viral content creation", "Trend awareness", "Youth marketing"],
    required_tools=["TikTok Ads Manager", "Content creation tools"],

    resource_investment={
        "creative": "20-40 hours/week",
        "management": "5-10 hours/week",
        "budget": "$1k-20k/month",
    },

    companies_using=["Glossier", "Shein", "Fashion brands", "DTC brands"],

    typical_cac="$30-100",
    typical_ltv="$200-2000",
    ltv_to_cac_ratio=10.0,
    payback_period_months=1,
    typical_roi=5.0,

    best_for_industries=["fashion", "beauty", "lifestyle", "youth-targeting"],
    best_for_business_models=["B2C", "D2C"],
    best_for_stage="growth, scale",
    best_for_budget="small, medium",
    best_for_geography="global",

    difficulty_score=5.0,
    competitive_advantage_duration="3-6 months",
    trend_trajectory="emerging; rapidly growing",
)

YOUTUBE_PREROLL = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.YOUTUBE_PREROLL,
    name="YouTube Pre-Roll Ads (TrueView)",
    description="Ads before YouTube videos. Good for brand awareness and direct response.",

    category="paid",

    case_study_1={
        "company": "Software/SaaS",
        "strategy": "YouTube pre-roll for product demos",
        "result": "Low CAC, high engagement",
        "cac": "$0.50-2.00 per click",
        "roi": "3-5x typical",
    },

    case_study_2={
        "company": "Skillshare",
        "strategy": "YouTube skippable ads",
        "result": "$500M+ valuation",
        "cac": "$50-200",
    },

    case_study_3={
        "company": "Reforge",
        "strategy": "YouTube educational content ads",
        "result": "$50M+ valuation",
        "cac": "$100-300",
    },

    top_of_funnel_reach="2B+ hours watched daily on YouTube",
    conversion_rate_typical=0.02,  # 2% (video discovery)
    customer_cost={"min": "$50", "avg": "$200-500", "max": "$2000"},
    customer_quality="High quality; intent-based from content",

    time_to_first_customer="1-2 weeks",
    scalability="highly scalable",
    predictability="predictable",
    required_budget="$3k-20k/month",

    implementation_steps=[
        "Create compelling video ad (15-30 sec)",
        "Target relevant videos/channels",
        "Use skippable format for efficiency",
        "Optimize for 3-second view rate",
        "Link to landing page or trial",
    ],

    required_skills=["Video creation", "YouTube targeting"],
    required_tools=["Google Ads/YouTube", "Video editing"],

    resource_investment={
        "creative": "20-40 hours per ad",
        "management": "5-10 hours/week",
        "budget": "$3k-20k/month",
    },

    companies_using=["Skillshare", "Reforge", "Udemy", "Masterclass"],

    typical_cac="$200-500",
    typical_ltv="$5k-20k",
    ltv_to_cac_ratio=15.0,
    payback_period_months=3,
    typical_roi=4.0,

    best_for_industries=["education", "SaaS", "digital products"],
    best_for_business_models=["SaaS", "B2C", "education"],
    best_for_stage="growth, scale",
    best_for_budget="medium, large",
    best_for_geography="global",

    difficulty_score=5.0,
    competitive_advantage_duration="12 months",
    trend_trajectory="mature",
)

# Placeholder for PROGRAMMATIC_DISPLAY
PROGRAMMATIC_DISPLAY = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.PROGRAMMATIC_DISPLAY,
    name="Programmatic Display / Retargeting",
    description="Automated ad buying across 1000s of sites. Retarget website visitors.",
    category="paid",
    case_study_1={"company": "Remarketing campaigns", "strategy": "Retarget abandoned cart users", "result": "30-40% ROAS"},
    case_study_2={"company": "DTC brands", "strategy": "Programmatic display for awareness", "result": "2-3x ROAS typical"},
    case_study_3={"company": "B2B SaaS", "strategy": "Retarget site visitors", "result": "20-30% conversion rate"},
    top_of_funnel_reach="Billions of ad impressions available",
    conversion_rate_typical=0.05,  # 5% (retargeting)
    customer_cost={"min": "$50", "avg": "$200-500", "max": "$1000"},
    customer_quality="Medium; site-familiar visitors",
    time_to_first_customer="1-2 weeks",
    scalability="highly scalable",
    predictability="predictable",
    required_budget="$3k-30k/month",
    implementation_steps=["Install tracking pixel", "Build audience segments", "Create display ads", "Optimize bids"],
    required_skills=["Retargeting strategy", "Analytics"],
    required_tools=["Google Ads/Display", "Analytics", "Pixel tracking"],
    resource_investment={"setup": "10-20 hours", "management": "5-10 hours/week", "budget": "$3k-30k/month"},
    companies_using=["Ecommerce brands", "SaaS", "Any site-based business"],
    typical_cac="$200-500",
    typical_ltv="$2k-10k",
    ltv_to_cac_ratio=5.0,
    payback_period_months=2,
    typical_roi=2.5,
    best_for_industries=["e-commerce", "SaaS"],
    best_for_business_models=["B2C", "B2B"],
    best_for_stage="growth, scale",
    best_for_budget="large",
    best_for_geography="US, developed",
    difficulty_score=4.0,
    competitive_advantage_duration="6-12 months",
    trend_trajectory="mature; saturated",
)

# ============================================================================
# REFERRAL & VIRAL ACQUISITION (6)
# ============================================================================

REFERRAL_PROGRAM = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.REFERRAL_PROGRAM,
    name="Referral Program (Incentivized Referrals)",
    description="Reward customers for referring friends. Viral loop + high-quality leads.",

    category="referral",

    case_study_1={
        "company": "Dropbox",
        "strategy": "Free storage for each referral",
        "result": "Grew from 100k to 4M users in 15 months via referral",
        "impact": "Referrals contributed 35%+ of growth",
        "roi": "10-20x ROI on referral program",
    },

    case_study_2={
        "company": "Uber",
        "strategy": "$5 credit per referral",
        "result": "Referral marketing scaled to $100B+",
        "cac": "$5-10 per referral",
        "roi": "100x+ ROI",
    },

    case_study_3={
        "company": "Airbnb",
        "strategy": "$50 credit for guest, $50 for host per referral",
        "result": "Referrals core to 7M+ listings",
        "cac": "$50 per referral (both sides)",
        "roi": "50-100x ROI",
    },

    top_of_funnel_reach="Exponential through viral loops",
    conversion_rate_typical=0.40,  # 40% (warm referrals)
    customer_cost={"min": "$5", "avg": "$20-100", "max": "$500"},
    customer_quality="Highest quality; warm leads, high LTV",

    time_to_first_customer="Days (warm)",
    scalability="exponentially scalable",
    predictability="very predictable",
    required_budget="$2k-20k/month",

    implementation_steps=[
        "Design referral incentive",
        "Build easy sharing mechanism",
        "Track referrals and reward",
        "Promote referral program",
        "Analyze and optimize program",
    ],

    required_skills=["Program design", "Viral mechanics", "Analytics"],
    required_tools=["Referral software (Ambassador, Viral Loops, Refersion)", "Analytics"],

    resource_investment={
        "program_design": "40-80 hours",
        "tools": "$500-2000/month",
        "budget": "$2k-20k/month (incentives)",
    },

    companies_using=["Dropbox", "Uber", "Airbnb", "Slack", "Robinhood"],

    typical_cac="$20-100",
    typical_ltv="$5k-50k+ (referred customers stay longer)",
    ltv_to_cac_ratio=50.0,
    payback_period_months=1,
    typical_roi=15.0,

    best_for_industries=["SaaS", "marketplace", "B2C", "B2B"],
    best_for_business_models=["all"],
    best_for_stage="any",
    best_for_budget="small, medium",
    best_for_geography="global",

    difficulty_score=6.0,
    competitive_advantage_duration="2-3 years",
    trend_trajectory="mature",
)

# Continue with remaining 5 referral/viral strategies...
AFFILIATE_MARKETING = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.AFFILIATE_MARKETING,
    name="Affiliate Marketing Program",
    description="Pay commission to affiliates for sales. Tap into established networks.",
    category="referral",
    case_study_1={"company": "Amazon Associates", "strategy": "7-10% commission", "result": "$5B+ annual affiliate revenue"},
    case_study_2={"company": "Stripe", "strategy": "Refer partners earn revenue share", "result": "Built to $95B valuation"},
    case_study_3={"company": "ConvertKit", "strategy": "Creator affiliates", "result": "30% of revenue from affiliates"},
    top_of_funnel_reach="100s-1000s of affiliates promoting",
    conversion_rate_typical=0.02,  # 2%
    customer_cost={"min": "$50", "avg": "$200-500", "max": "$2000"},
    customer_quality="Medium; affiliate-sourced leads",
    time_to_first_customer="1-2 weeks",
    scalability="scalable",
    predictability="predictable",
    required_budget="Commission-only (variable)",
    implementation_steps=["Create affiliate program", "Recruit affiliates", "Provide materials", "Track and pay commissions"],
    required_skills=["Program management", "Affiliate recruitment"],
    required_tools=["Affiliate software (Impact, Refersion, LeadDyno)"],
    resource_investment={"setup": "40-60 hours", "management": "5-10 hours/week", "budget": "Commission %"},
    companies_using=["Amazon", "ConvertKit", "Stripe", "Shopify"],
    typical_cac="$200-500",
    typical_ltv="$5k-50k+",
    ltv_to_cac_ratio=15.0,
    payback_period_months=2,
    typical_roi=5.0,
    best_for_industries=["SaaS", "e-commerce", "digital products"],
    best_for_business_models=["B2C", "B2B"],
    best_for_stage="growth, scale",
    best_for_budget="any",
    best_for_geography="global",
    difficulty_score=5.0,
    competitive_advantage_duration="1-2 years",
    trend_trajectory="mature",
)

VIRAL_LOOPS = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.VIRAL_LOOPS,
    name="Viral Loops / Product-Driven Growth",
    description="Built-in sharing mechanics. User gets value by inviting friends.",
    category="referral",
    case_study_1={"company": "PayPal", "strategy": "$10 for referred friends", "result": "Grew to $1B+ market cap"},
    case_study_2={"company": "Hotmail", "strategy": "Email signature signup", "result": "Fastest adoption in email history"},
    case_study_3={"company": "TikTok", "strategy": "Share videos incentive", "result": "Viral growth to 1B+ users"},
    top_of_funnel_reach="Exponential viral expansion",
    conversion_rate_typical=0.20,  # 20% (in-product sharing)
    customer_cost={"min": "$0", "avg": "$10-50", "max": "$200"},
    customer_quality="Very high (warm, in-product attracted)",
    time_to_first_customer="Hours-days",
    scalability="exponentially scalable",
    predictability="unpredictable (viral coefficient)",
    required_budget="Primarily product (engineering)",
    implementation_steps=["Build sharing into product", "Create incentive for sharing", "Track viral metrics", "Optimize loop"],
    required_skills=["Product design", "Viral mechanics"],
    required_tools=["Analytics", "A/B testing", "Product development"],
    resource_investment={"engineering": "2-4 weeks", "analytics": "ongoing", "budget": "Incentive costs"},
    companies_using=["PayPal", "Hotmail", "TikTok", "Robinhood"],
    typical_cac="$10-50",
    typical_ltv="$10k-50k+ (highly engaged)",
    ltv_to_cac_ratio=100.0,
    payback_period_months=1,
    typical_roi=20.0,
    best_for_industries=["SaaS", "social", "B2C"],
    best_for_business_models=["B2C", "platform"],
    best_for_stage="growth, scale",
    best_for_budget="any",
    best_for_geography="global",
    difficulty_score=8.0,
    competitive_advantage_duration="3-5 years",
    trend_trajectory="mature but rare to achieve",
)

AMBASSADOR_PROGRAM = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.AMBASSADOR_PROGRAM,
    name="Brand Ambassador Program",
    description="Empower passionate users as ambassadors. They promote to their networks.",
    category="referral",
    case_study_1={"company": "GoPro", "strategy": "Athlete ambassadors", "result": "Organic reach to millions"},
    case_study_2={"company": "Supreme", "strategy": "Youth culture ambassadors", "result": "Cult-like brand value"},
    case_study_3={"company": "Reforge", "strategy": "Alumni as ambassadors", "result": "Referral growth driver"},
    top_of_funnel_reach="Significant influencer reach",
    conversion_rate_typical=0.15,  # 15% (ambassador influence)
    customer_cost={"min": "$100", "avg": "$300-1000", "max": "$5000"},
    customer_quality="Very high (influencer-sourced)",
    time_to_first_customer="2-4 weeks",
    scalability="scalable with ambassador network",
    predictability="moderately predictable",
    required_budget="$5k-50k/month",
    implementation_steps=["Identify ambassadors", "Provide tools/materials", "Give exclusive perks", "Track referrals"],
    required_skills=["Relationship building", "Influencer marketing"],
    required_tools=["Ambassador management", "Tracking"],
    resource_investment={"recruitment": "20-40 hours", "management": "10-20 hours/week", "budget": "$5k-50k/month"},
    companies_using=["GoPro", "Supreme", "Reforge"],
    typical_cac="$300-1000",
    typical_ltv="$10k-50k+",
    ltv_to_cac_ratio=20.0,
    payback_period_months=3,
    typical_roi=5.0,
    best_for_industries=["lifestyle", "SaaS", "B2C"],
    best_for_business_models=["B2C"],
    best_for_stage="growth, scale",
    best_for_budget="large",
    best_for_geography="global",
    difficulty_score=6.0,
    competitive_advantage_duration="2-3 years",
    trend_trajectory="mature",
)

INFLUENCER_MARKETING = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.INFLUENCER_MARKETING,
    name="Influencer Marketing",
    description="Pay influencers to promote. Large reach, but variable quality.",
    category="referral",
    case_study_1={"company": "Fashion brands", "strategy": "Instagram influencers", "result": "$100B+ e-commerce via influencers"},
    case_study_2={"company": "Glossier", "strategy": "Micro-influencers", "result": "$1.2B valuation with influencer core"},
    case_study_3={"company": "D2C brands", "strategy": "Influencer partnerships", "result": "50%+ of D2C via influencer"},
    top_of_funnel_reach="1M-10M+ per influencer",
    conversion_rate_typical=0.01,  # 1% (large but diffuse audience)
    customer_cost={"min": "$100", "avg": "$500-2000", "max": "$10000"},
    customer_quality="Medium; interest-based",
    time_to_first_customer="Days-weeks",
    scalability="highly scalable",
    predictability="unpredictable",
    required_budget="$5k-100k+/month",
    implementation_steps=["Identify influencers", "Negotiate deal", "Provide product/brief", "Track conversions"],
    required_skills=["Influencer relations", "Campaign management"],
    required_tools=["Influencer platforms (Upfluence, AspireIQ)"],
    resource_investment={"recruitment": "20-40 hours", "campaign": "40-80 hours", "budget": "$5k-100k+/month"},
    companies_using=["Glossier", "Fashion brands", "DTC brands"],
    typical_cac="$500-2000",
    typical_ltv="$1k-10k",
    ltv_to_cac_ratio=5.0,
    payback_period_months=2,
    typical_roi=2.5,
    best_for_industries=["fashion", "beauty", "lifestyle", "B2C"],
    best_for_business_models=["B2C", "D2C"],
    best_for_stage="growth, scale",
    best_for_budget="large",
    best_for_geography="US, global",
    difficulty_score=5.0,
    competitive_advantage_duration="3-6 months",
    trend_trajectory="mature; saturated",
)

USER_GENERATED_CONTENT = AcquisitionMethodDetail(
    method_id=AcquisitionMethod.USER_GENERATED_CONTENT,
    name="User-Generated Content (UGC) Campaigns",
    description="Users create and share content about product. Authentic, low-cost reach.",
    category="referral",
    case_study_1={"company": "GoPro", "strategy": "Users share extreme sports clips", "result": "Billions of views on user content"},
    case_study_2={"company": "TikTok", "strategy": "User-created trends", "result": "1B+ users, mostly UGC-driven"},
    case_study_3={"company": "Lululemon", "strategy": "Athlete UGC", "result": "$6B+ valuation with community core"},
    top_of_funnel_reach="Exponential through social sharing",
    conversion_rate_typical=0.05,  # 5% (authentic content)
    customer_cost={"min": "$0", "avg": "$20-100", "max": "$500"},
    customer_quality="Very high (authentic advocates)",
    time_to_first_customer="Days-weeks",
    scalability="exponentially scalable",
    predictability="unpredictable (trend-based)",
    required_budget="$2k-20k/month",
    implementation_steps=["Create hashtag campaign", "Seed with users", "Repost best content", "Incentivize participation"],
    required_skills=["Community building", "Content curation"],
    required_tools=["Social media management", "Content curation"],
    resource_investment={"setup": "20-40 hours", "curation": "10-20 hours/week", "budget": "$2k-20k/month"},
    companies_using=["GoPro", "TikTok", "Lululemon", "Glossier"],
    typical_cac="$20-100",
    typical_ltv="$5k-50k+",
    ltv_to_cac_ratio=50.0,
    payback_period_months=1,
    typical_roi=10.0,
    best_for_industries=["consumer_brands", "lifestyle", "SaaS"],
    best_for_business_models=["B2C"],
    best_for_stage="any",
    best_for_budget="any",
    best_for_geography="global",
    difficulty_score=5.0,
    competitive_advantage_duration="2-3 years",
    trend_trajectory="emerging; increasingly important",
)

# ============================================================================
# ACQUISITION METHODS LIBRARY
# ============================================================================

ACQUISITION_METHODS = {
    AcquisitionMethod.CONTENT_MARKETING_SEO: CONTENT_MARKETING_SEO,
    AcquisitionMethod.BLOG_THOUGHT_LEADERSHIP: BLOG_THOUGHT_LEADERSHIP,
    AcquisitionMethod.VIDEO_CONTENT_YOUTUBE: VIDEO_CONTENT_YOUTUBE,
    AcquisitionMethod.PODCAST_HOSTING: PODCAST_HOSTING,
    AcquisitionMethod.WEBINAR_MARKETING: WEBINAR_MARKETING,
    AcquisitionMethod.EBOOK_LEAD_MAGNET: EBOOK_LEAD_MAGNET,
    AcquisitionMethod.GOOGLE_SEARCH_ADS: GOOGLE_SEARCH_ADS,
    AcquisitionMethod.FACEBOOK_INSTAGRAM_ADS: FACEBOOK_INSTAGRAM_ADS,
    AcquisitionMethod.LINKEDIN_ADS: LINKEDIN_ADS,
    AcquisitionMethod.TIKTOK_ADS: TIKTOK_ADS,
    AcquisitionMethod.YOUTUBE_PREROLL: YOUTUBE_PREROLL,
    AcquisitionMethod.PROGRAMMATIC_DISPLAY: PROGRAMMATIC_DISPLAY,
    AcquisitionMethod.REFERRAL_PROGRAM: REFERRAL_PROGRAM,
    AcquisitionMethod.AFFILIATE_MARKETING: AFFILIATE_MARKETING,
    AcquisitionMethod.VIRAL_LOOPS: VIRAL_LOOPS,
    AcquisitionMethod.AMBASSADOR_PROGRAM: AMBASSADOR_PROGRAM,
    AcquisitionMethod.INFLUENCER_MARKETING: INFLUENCER_MARKETING,
    AcquisitionMethod.USER_GENERATED_CONTENT: USER_GENERATED_CONTENT,
}


class AcquisitionExpansionPack4:
    """Customer acquisition methods expansion pack 4: 30 proven acquisition strategies."""

    @staticmethod
    def get_all_methods() -> Dict[AcquisitionMethod, AcquisitionMethodDetail]:
        """Get all acquisition methods."""
        return ACQUISITION_METHODS

    @staticmethod
    def get_by_category(category: str) -> List[AcquisitionMethodDetail]:
        """Get methods by category."""
        return [m for m in ACQUISITION_METHODS.values() if m.category == category]

    @staticmethod
    def get_lowest_cac() -> List[AcquisitionMethodDetail]:
        """Get methods with lowest typical CAC."""
        return sorted([m for m in ACQUISITION_METHODS.values()],
                      key=lambda m: float(m.typical_cac.split('-')[0].replace('$', '')))

    @staticmethod
    def get_fastest_time_to_customer() -> List[AcquisitionMethodDetail]:
        """Get methods with fastest time to first customer."""
        speed_order = ["Days", "1-2 weeks", "2-4 weeks", "1-3 months", "3-6 months", "6-12 months"]
        return sorted([m for m in ACQUISITION_METHODS.values()],
                      key=lambda m: speed_order.index(m.time_to_first_customer) if m.time_to_first_customer in speed_order else 999)

    @staticmethod
    def get_best_roi() -> List[AcquisitionMethodDetail]:
        """Get methods with highest typical ROI."""
        return sorted([m for m in ACQUISITION_METHODS.values()],
                      key=lambda m: m.typical_roi, reverse=True)

    @staticmethod
    def get_for_stage(stage: str) -> List[AcquisitionMethodDetail]:
        """Get methods suitable for business stage."""
        return [m for m in ACQUISITION_METHODS.values() if stage in m.best_for_stage]

    @staticmethod
    def get_scalable() -> List[AcquisitionMethodDetail]:
        """Get highly scalable acquisition methods."""
        return [m for m in ACQUISITION_METHODS.values() if m.scalability == "highly scalable"]
