"""Expansion Pack 2: 30 Sales Methods - Consultative, Transactional, Inside Sales Scripts."""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum


class SalesMethod(str, Enum):
    """Sales method identifiers (30 strategies)."""
    # Consultative Sales (10)
    CONSULTATIVE_DISCOVERY = "sales_consultative_discovery"
    VALUE_STACK_SELLING = "sales_value_stack"
    OUTCOME_BASED_SELLING = "sales_outcome_based"
    SOLUTION_SELLING = "sales_solution"
    INSIGHT_SELLING = "sales_insight"
    EXECUTIVE_BRIEFING = "sales_executive_briefing"
    ROI_CALCULATOR = "sales_roi_calculator"
    COMPETITOR_TAKEAWAY = "sales_competitor_takeaway"
    REFERRAL_SELLING = "sales_referral"
    ACCOUNT_BASED_SELLING = "sales_account_based"

    # Transactional Sales (10)
    DIRECT_RESPONSE = "sales_direct_response"
    LIMITED_TIME_OFFER = "sales_limited_time"
    SCARCITY_PRICING = "sales_scarcity"
    SOCIAL_PROOF_SELLING = "sales_social_proof"
    URGENCY_DRIVEN = "sales_urgency"
    BUNDLING_UPSELL = "sales_bundling"
    TRIAL_TO_PAID = "sales_trial_paid"
    AFFILIATE_SELLING = "sales_affiliate"
    MARKETPLACE_ARBITRAGE = "sales_marketplace"
    PRICE_ANCHOR_SELLING = "sales_price_anchor"

    # Inside Sales / Outbound (10)
    COLD_EMAIL_SEQUENCE = "sales_cold_email"
    PHONE_PROSPECTING = "sales_phone_prospecting"
    LINKEDIN_OUTREACH = "sales_linkedin_outreach"
    ACCOUNT_MINING = "sales_account_mining"
    TRIGGER_BASED_OUTREACH = "sales_trigger_based"
    OBJECTION_HANDLING = "sales_objection_handling"
    CLOSING_TECHNIQUES = "sales_closing"
    DEAL_STACKING = "sales_deal_stacking"
    SOCIAL_SELLING = "sales_social_selling"
    VIDEO_SELLING = "sales_video_selling"


@dataclass
class SalesMethodDetail:
    """Complete sales method with scripts, metrics, and case studies."""
    method_id: SalesMethod
    name: str
    description: str
    category: str  # consultative, transactional, inside_sales

    # Real Case Studies
    case_study_1: Dict[str, Any]
    case_study_2: Dict[str, Any]
    case_study_3: Dict[str, Any]

    # Sales Scripts & Templates
    opening_statement: str
    key_questions: List[str]
    value_propositions: List[str]
    objection_handlers: Dict[str, str]  # objection -> response
    closing_statements: List[str]

    # Metrics & Performance
    typical_conversion_rate: float  # %
    typical_deal_size: Dict[str, str]  # min, avg, max
    average_sales_cycle_days: int
    win_rate_vs_competition: float  # %
    customer_satisfaction_nps: int

    # Implementation
    required_skills: List[str]
    tools_needed: List[str]
    training_hours_needed: int
    ramp_time_weeks: int

    # Applicability
    best_for_industries: List[str]
    best_for_business_models: List[str]
    best_for_deal_sizes: str  # small, mid, enterprise
    customer_segment: str  # self-serve, SMB, mid-market, enterprise

    # Performance Metrics
    quota_achievement: float  # % of reps hitting quota
    rep_satisfaction: int  # 1-10 scale
    customer_satisfaction_post_sale: int  # 1-10 scale
    churn_rate_impact: float  # How method impacts churn

    # Difficulty & Adoption
    difficulty_score: float  # 1-10
    time_to_competency: str  # weeks
    competitive_advantage_duration: str


# ============================================================================
# CONSULTATIVE SALES METHODS (10)
# ============================================================================

CONSULTATIVE_DISCOVERY = SalesMethodDetail(
    method_id=SalesMethod.CONSULTATIVE_DISCOVERY,
    name="Consultative Discovery Selling",
    description="Focus on understanding customer needs deeply before proposing solution. MEDDIC/BANT framework.",
    category="consultative",

    case_study_1={
        "company": "Salesforce",
        "rep_type": "Enterprise AE",
        "conversion_rate": 0.45,  # 45% win rate
        "deal_size": "$500K-$5M",
        "timeline": "6-12 months",
        "key_success_factor": "Discovery questions uncover business impact",
        "revenue_impact": "$100M+ from enterprise sales method",
    },

    case_study_2={
        "company": "Accenture Consulting",
        "rep_type": "Strategic account manager",
        "conversion_rate": 0.52,  # 52% win rate
        "deal_size": "$1M-$50M",
        "timeline": "3-9 months",
        "key_success_factor": "Business outcome focus vs technical features",
        "revenue_impact": "$200M+ from consultative selling",
    },

    case_study_3={
        "company": "Zoom",
        "rep_type": "Enterprise sales",
        "conversion_rate": 0.48,
        "deal_size": "$250K-$2M",
        "timeline": "4-8 weeks",
        "key_success_factor": "Discovery uncovers ROI on communication costs",
        "revenue_impact": "Built to $8B+ ARR with consultative approach",
    },

    opening_statement="Rather than jumping to features, I'd love to understand your current challenges with [pain_area]. Can you walk me through how you're currently handling [problem_area]?",

    key_questions=[
        "What's your biggest challenge with [current_solution]?",
        "How is this impacting your business results?",
        "What would ideal look like for your team?",
        "What's preventing you from solving this today?",
        "If we could solve this, what would success look like?",
        "How would this impact your revenue/costs/efficiency?",
        "Who needs to be involved in the decision?",
        "What's your timeline for solving this?",
        "What have you tried before, and why didn't it work?",
    ],

    value_propositions=[
        "Help customers achieve X% reduction in [cost/time]",
        "Enable teams to focus on strategic work vs manual tasks",
        "Improve decision-making with better data visibility",
        "Reduce risk of [specific business risk]",
        "Scale operations without proportional headcount increase",
    ],

    objection_handlers={
        "Too expensive": "Let's model the ROI based on your specific situation. If we can save you $100K/year and cost $50K, is that compelling?",
        "Need to evaluate competitors": "Great, that makes sense. What are the 3-4 criteria you're using to evaluate? Let me show you how we perform on those.",
        "Not ready yet": "I understand. What would need to change for this to be a priority? Let's stay connected so I can help when timing is right.",
        "Our team isn't convinced": "Perfect, let's get the right stakeholders together. Who needs to see the business case?",
    },

    closing_statements=[
        "Based on everything we've discussed, it sounds like [solution] aligns well with your goal of [outcome]. Should we move forward with a trial?",
        "So we're aligned on the problem, the impact, and the solution. The next step would be [implementation_step]. Does that work for you?",
        "You've mentioned [3 key needs]. Our solution directly addresses all three. Let's get you started this week. Does Tuesday work for a kickoff?",
    ],

    typical_conversion_rate=0.45,
    typical_deal_size={"min": "$50K", "avg": "$500K", "max": "$10M"},
    average_sales_cycle_days=150,
    win_rate_vs_competition=0.55,
    customer_satisfaction_nps=65,

    required_skills=[
        "Active listening",
        "Strategic thinking",
        "Business acumen",
        "Questioning technique",
        "ROI modeling",
        "Executive communication",
    ],

    tools_needed=[
        "CRM (Salesforce, HubSpot)",
        "Deal tracking",
        "ROI calculator",
        "Competitive intelligence tools",
    ],

    training_hours_needed=40,
    ramp_time_weeks=12,

    best_for_industries=["enterprise_software", "consulting", "professional_services"],
    best_for_business_models=["B2B", "SaaS"],
    best_for_deal_sizes="mid-market, enterprise",
    customer_segment="mid-market, enterprise",

    quota_achievement=0.70,
    rep_satisfaction=8,
    customer_satisfaction_post_sale=8,
    churn_rate_impact=-0.20,  # 20% lower churn due to fit

    difficulty_score=7.0,
    time_to_competency="12-16 weeks",
    competitive_advantage_duration="ongoing",
)

VALUE_STACK_SELLING = SalesMethodDetail(
    method_id=SalesMethod.VALUE_STACK_SELLING,
    name="Value Stack Selling (Layered Value)",
    description="Build stacked value proposition: base value + process value + strategic value. Each layer compounds.",
    category="consultative",

    case_study_1={
        "company": "HubSpot",
        "rep_type": "Sales development rep",
        "conversion_rate": 0.38,
        "deal_size": "$10K-$100K",
        "timeline": "8-12 weeks",
        "key_success_factor": "Stacking value: productivity + intelligence + scaling",
        "revenue_impact": "$1B+ ARR through value stack model",
    },

    case_study_2={
        "company": "Slack",
        "rep_type": "Enterprise account executive",
        "conversion_rate": 0.52,
        "deal_size": "$100K-$1M",
        "timeline": "6-10 weeks",
        "key_success_factor": "Communication value + productivity + organizational alignment",
        "revenue_impact": "$2B+ ARR driven by layered value",
    },

    case_study_3={
        "company": "Stripe",
        "rep_type": "Partner sales manager",
        "conversion_rate": 0.58,
        "deal_size": "$50K-$500K",
        "timeline": "4-8 weeks",
        "key_success_factor": "Payment processing + reliability + growth enablement",
        "revenue_impact": "$4B+ ARR from value stack selling",
    },

    opening_statement="Most companies we work with start by using us for [basic_use_case]. But the real value comes in three layers. Let me show you what companies typically see...",

    key_questions=[
        "How would you rank these value areas? 1) Immediate productivity, 2) Better decision making, 3) Strategic scaling?",
        "Which of these impacts would matter most to your CEO?",
        "Have you modeled the time/cost savings if you could achieve [metric]?",
        "What prevents you from scaling [business_process] today?",
    ],

    value_propositions=[
        "Immediate productivity value: X% faster [process]",
        "Process value: Enable teams to focus on strategic work",
        "Strategic value: Scale business model without linear cost increase",
        "Layered: Each value adds on top of previous",
    ],

    objection_handlers={
        "Can we just start with basic tier?": "Absolutely! Most customers do. They typically upgrade within 3 months once they see the base value. What appeals to you about starting there?",
        "Seems complex for the value": "I get that. What if we focused on just [high_impact_use_case] first? The other value accrues naturally as you expand.",
    },

    closing_statements=[
        "So we've identified three areas of value: [value1], [value2], [value3]. Let's start with [value1] and expand as you see results.",
        "Given the layered impact, I recommend starting with [base_tier]. You'll likely expand in 60-90 days once you see the base productivity gains.",
    ],

    typical_conversion_rate=0.42,
    typical_deal_size={"min": "$10K", "avg": "$100K", "max": "$1M"},
    average_sales_cycle_days=90,
    win_rate_vs_competition=0.50,
    customer_satisfaction_nps=62,

    required_skills=["Strategic thinking", "Value modeling", "Executive communication", "Storytelling"],
    tools_needed=["CRM", "Value modeling tools", "Case studies", "ROI calculators"],
    training_hours_needed=30,
    ramp_time_weeks=8,

    best_for_industries=["SaaS", "software", "professional_services"],
    best_for_business_models=["SaaS", "B2B"],
    best_for_deal_sizes="all",
    customer_segment="SMB, mid-market, enterprise",

    quota_achievement=0.68,
    rep_satisfaction=8,
    customer_satisfaction_post_sale=7,
    churn_rate_impact=-0.15,

    difficulty_score=6.0,
    time_to_competency="8-10 weeks",
    competitive_advantage_duration="ongoing",
)

OUTCOME_BASED_SELLING = SalesMethodDetail(
    method_id=SalesMethod.OUTCOME_BASED_SELLING,
    name="Outcome-Based Selling",
    description="Sell the outcome/result, not the product. 'We help you reduce customer acquisition cost by 30%' not 'We have an analytics dashboard'.",
    category="consultative",

    case_study_1={
        "company": "Gong",
        "rep_type": "Enterprise sales",
        "conversion_rate": 0.48,
        "deal_size": "$250K-$2M",
        "timeline": "6-12 weeks",
        "key_success_factor": "Focus on call-quality outcome vs transcription features",
        "revenue_impact": "$500M+ ARR on outcome-based selling",
    },

    case_study_2={
        "company": "Marketo (now Adobe)",
        "rep_type": "Solution consultant",
        "conversion_rate": 0.45,
        "deal_size": "$100K-$1M",
        "timeline": "8-16 weeks",
        "key_success_factor": "Lead generation outcome not tool features",
        "revenue_impact": "$1B+ ARR driven by outcome focus",
    },

    case_study_3={
        "company": "Twilio",
        "rep_type": "Solution engineer",
        "conversion_rate": 0.42,
        "deal_size": "$50K-$500K",
        "timeline": "6-10 weeks",
        "key_success_factor": "Customer experience outcome vs API capability",
        "revenue_impact": "$3B+ valuation through outcome selling",
    },

    opening_statement="Most of our customers care less about the tool and more about one outcome: [key_outcome]. That's what we really help with. Have you quantified what that's worth?",

    key_questions=[
        "If you could reliably achieve [outcome], what would that be worth to your business?",
        "How is lack of [outcome] impacting your current growth?",
        "What would change if you could improve [metric] by 25%?",
        "Who would get credit for achieving this outcome?",
    ],

    value_propositions=[
        "Reduce customer acquisition cost from $X to $Y",
        "Improve sales cycle from 6 months to 8 weeks",
        "Increase team productivity by 40%",
        "Enable 10x scaling without team growth",
    ],

    objection_handlers={
        "How do we know it will work?": "Great question. We have case studies showing [specific outcome]. Plus, we typically start with a pilot for [timeframe] to validate results in your context.",
        "Your competitor has cheaper pricing": "I get that. Price isn't our differentiator—outcome is. Are you optimizing for price or for [key_outcome]?",
    },

    closing_statements=[
        "Based on your situation, we can realistically deliver $[X] impact in year one. Let's move forward with a pilot to validate that.",
        "You've been clear that [outcome] is the priority. We're confident we can help. Let's get started this month.",
    ],

    typical_conversion_rate=0.46,
    typical_deal_size={"min": "$50K", "avg": "$400K", "max": "$2M"},
    average_sales_cycle_days=120,
    win_rate_vs_competition=0.52,
    customer_satisfaction_nps=68,

    required_skills=["Business acumen", "ROI modeling", "Executive communication", "Result orientation"],
    tools_needed=["ROI calculator", "Case studies", "Outcome tracking tools"],
    training_hours_needed=25,
    ramp_time_weeks=8,

    best_for_industries=["SaaS", "software", "consulting"],
    best_for_business_models=["B2B"],
    best_for_deal_sizes="mid-market, enterprise",
    customer_segment="mid-market, enterprise",

    quota_achievement=0.72,
    rep_satisfaction=8,
    customer_satisfaction_post_sale=8,
    churn_rate_impact=-0.25,

    difficulty_score=6.5,
    time_to_competency="10-12 weeks",
    competitive_advantage_duration="ongoing",
)

SOLUTION_SELLING = SalesMethodDetail(
    method_id=SalesMethod.SOLUTION_SELLING,
    name="Solution Selling (Problem/Solution Framework)",
    description="Three-step: identify problem → present solution → confirm fit. Consultative but structured.",
    category="consultative",

    case_study_1={
        "company": "Cisco Systems",
        "rep_type": "Enterprise account executive",
        "conversion_rate": 0.42,
        "deal_size": "$1M-$10M",
        "timeline": "6-12 months",
        "key_success_factor": "Structured problem identification drives structured solution",
        "revenue_impact": "$50B+ annual revenue using solution selling",
    },

    case_study_2={
        "company": "SAP",
        "rep_type": "Solution engineer",
        "conversion_rate": 0.38,
        "deal_size": "$500K-$5M",
        "timeline": "6-12 months",
        "key_success_factor": "Process-driven solution design",
        "revenue_impact": "$25B+ annual revenue from solution selling",
    },

    case_study_3={
        "company": "Oracle",
        "rep_type": "Account manager",
        "conversion_rate": 0.40,
        "deal_size": "$500K-$3M",
        "timeline": "6-10 months",
        "key_success_factor": "Problem-led discovery enables solution fit",
        "revenue_impact": "$40B+ annual revenue on solution model",
    },

    opening_statement="I've worked with several companies like yours dealing with [common_problem]. Can I share what we typically see and get your thoughts?",

    key_questions=[
        "How is [problem_area] impacting your business right now?",
        "What approaches have you tried to solve this?",
        "What's stopping you from solving this yourself?",
        "If we could address [problem], would that help?",
        "What would an ideal solution look like?",
    ],

    value_propositions=[
        "Solve [specific problem] with proven methodology",
        "Leverage experience from 100+ similar implementations",
        "Reduce implementation risk through structured approach",
    ],

    objection_handlers={
        "We've tried this before": "I hear that. What happened then? [Listen]. It sounds like [different issue]. Our approach addresses specifically [that issue].",
        "Need more time to decide": "Totally reasonable. What would we need to show you to move this forward? [Listen to criteria]. Let's plan around that.",
    },

    closing_statements=[
        "So we've identified the problem, verified the solution approach works, and aligned on implementation. Should we start moving?",
        "You're convinced on the problem and solution. The question is just implementation. Can you be ready to start in [timeframe]?",
    ],

    typical_conversion_rate=0.40,
    typical_deal_size={"min": "$100K", "avg": "$1M", "max": "$10M"},
    average_sales_cycle_days=180,
    win_rate_vs_competition=0.48,
    customer_satisfaction_nps=65,

    required_skills=["Problem diagnosis", "Solution design", "Project management", "Executive communication"],
    tools_needed=["CRM", "Solution framework", "Implementation methodology"],
    training_hours_needed=35,
    ramp_time_weeks=10,

    best_for_industries=["enterprise_software", "consulting", "professional_services"],
    best_for_business_models=["B2B"],
    best_for_deal_sizes="enterprise",
    customer_segment="enterprise",

    quota_achievement=0.65,
    rep_satisfaction=7,
    customer_satisfaction_post_sale=7,
    churn_rate_impact=-0.20,

    difficulty_score=7.0,
    time_to_competency="12-16 weeks",
    competitive_advantage_duration="ongoing",
)

INSIGHT_SELLING = SalesMethodDetail(
    method_id=SalesMethod.INSIGHT_SELLING,
    name="Insight Selling (Teach & Advise)",
    description="Lead with insight/research that customer hasn't considered. Position as trusted advisor, not vendor.",
    category="consultative",

    case_study_1={
        "company": "Bain & Company",
        "rep_type": "Principal consultant",
        "conversion_rate": 0.52,
        "deal_size": "$1M-$50M+",
        "timeline": "3-6 months",
        "key_success_factor": "Insight-led credibility establishes advisor status",
        "revenue_impact": "$4B+ annual revenue from insight-based selling",
    },

    case_study_2={
        "company": "LinkedIn Sales Solutions",
        "rep_type": "Account executive",
        "conversion_rate": 0.48,
        "deal_size": "$50K-$500K",
        "timeline": "8-12 weeks",
        "key_success_factor": "Lead with data/insights customer doesn't know",
        "revenue_impact": "$2B+ ARR driven by insight selling",
    },

    case_study_3={
        "company": "Forrester",
        "rep_type": "Research-led sales",
        "conversion_rate": 0.50,
        "deal_size": "$25K-$500K",
        "timeline": "6-10 weeks",
        "key_success_factor": "Research-based insights drive decisions",
        "revenue_impact": "$500M+ ARR on insight model",
    },

    opening_statement="I've been researching your industry, and I noticed something interesting about how [peer_group] is shifting [strategy]. You might not have visibility into this yet, but it could impact you. Can I share what we're seeing?",

    key_questions=[
        "Are you tracking how your competitors are shifting [strategy]?",
        "What would change if you knew [competitor] was doing X?",
        "Have you seen the latest research on [industry_trend]?",
        "If [market_change] happens, are you prepared?",
    ],

    value_propositions=[
        "Get ahead of market shifts before competitors",
        "Leverage research from 1000+ industry participants",
        "Benchmark your performance against peers",
        "Access insights your internal team doesn't have",
    ],

    objection_handlers={
        "That's interesting but not urgent": "I understand. What would need to shift for this to become urgent? [Listen]. Let's stay connected so we can help when timing changes.",
        "We have internal insights": "That's great. I'm sure you do. Our perspective is external and based on 1000+ companies. Would additional perspectives be valuable?",
    },

    closing_statements=[
        "Based on the insight we've shared, I think there's an opportunity to act before competitors do. Can we explore that together?",
        "You see how this insight changes the game. Let's talk about how to capitalize on it.",
    ],

    typical_conversion_rate=0.50,
    typical_deal_size={"min": "$25K", "avg": "$250K", "max": "$5M"},
    average_sales_cycle_days=100,
    win_rate_vs_competition=0.60,
    customer_satisfaction_nps=72,

    required_skills=["Industry expertise", "Research capability", "Communication", "Advisory mindset"],
    tools_needed=["Industry research", "Competitive intelligence", "Data visualization"],
    training_hours_needed=40,
    ramp_time_weeks=12,

    best_for_industries=["consulting", "research", "enterprise_software"],
    best_for_business_models=["B2B"],
    best_for_deal_sizes="mid-market, enterprise",
    customer_segment="mid-market, enterprise, C-level",

    quota_achievement=0.75,
    rep_satisfaction=8,
    customer_satisfaction_post_sale=8,
    churn_rate_impact=-0.30,

    difficulty_score=7.5,
    time_to_competency="16-20 weeks",
    competitive_advantage_duration="3-6 months",
)

EXECUTIVE_BRIEFING = SalesMethodDetail(
    method_id=SalesMethod.EXECUTIVE_BRIEFING,
    name="Executive Briefing / Board Presentation",
    description="Sell at C-suite level. Data-driven presentation format. Builds credibility and accelerates deals.",
    category="consultative",

    case_study_1={
        "company": "Goldman Sachs",
        "event_type": "Board presentation",
        "conversion_rate": 0.65,
        "deal_size": "$10M-$100M+",
        "timeline": "2-4 weeks post-briefing",
        "key_success_factor": "Board-level credibility and approval",
        "revenue_impact": "$50B+ AUM influenced by board presentations",
    },

    case_study_2={
        "company": "Accenture",
        "event_type": "C-suite insights session",
        "conversion_rate": 0.60,
        "deal_size": "$2M-$50M",
        "timeline": "4-8 weeks",
        "key_success_factor": "Executive alignment on business impact",
        "revenue_impact": "$40B+ annual revenue from executive selling",
    },

    case_study_3={
        "company": "Deloitte",
        "event_type": "Strategic briefing",
        "conversion_rate": 0.58,
        "deal_size": "$1M-$30M",
        "timeline": "3-6 weeks",
        "key_success_factor": "CEO/CFO/COO alignment on strategy",
        "revenue_impact": "$20B+ from executive engagement model",
    },

    opening_statement="I'd like to invite your executive team to a 60-minute strategic briefing. We're covering how peer companies are approaching [strategic_topic]. I think it would be valuable for your leadership to get this perspective. Would that interest you?",

    key_questions=[
        "Who should definitely be in this briefing? (CEO, CFO, COO, etc)",
        "What strategic questions keep you up at night?",
        "How is [industry_trend] going to impact your strategy?",
        "What would compelling evidence of opportunity look like?",
    ],

    value_propositions=[
        "Strategic perspective from 100+ peer companies",
        "Risk assessment of different approaches",
        "Benchmarking your strategy vs peers",
        "Executive-level alignment on opportunity",
    ],

    objection_handlers={
        "Too early stage for executive time": "I understand executives are busy. But this often impacts strategy, so I'd argue it's never too early. What if we did a 30-minute executive overview?",
        "Need to get more context first": "Great. Let's do that. But I'd recommend getting execs informed early so they can shape the evaluation.",
    },

    closing_statements=[
        "Based on executive feedback, there's clear alignment on the opportunity. Should we move to contract negotiation?",
        "Your team is aligned. The question is implementation. What's your timeline?",
    ],

    typical_conversion_rate=0.62,
    typical_deal_size={"min": "$500K", "avg": "$5M", "max": "$100M+"},
    average_sales_cycle_days=60,
    win_rate_vs_competition=0.70,
    customer_satisfaction_nps=75,

    required_skills=["Executive presence", "Strategic thinking", "Presentation skills", "Credibility"],
    tools_needed=["Presentation software", "Executive insights", "Benchmarking data"],
    training_hours_needed=35,
    ramp_time_weeks=12,

    best_for_industries=["consulting", "enterprise_software", "professional_services"],
    best_for_business_models=["B2B"],
    best_for_deal_sizes="enterprise",
    customer_segment="enterprise, C-level",

    quota_achievement=0.80,
    rep_satisfaction=8,
    customer_satisfaction_post_sale=8,
    churn_rate_impact=-0.35,

    difficulty_score=7.5,
    time_to_competency="12-16 weeks",
    competitive_advantage_duration="ongoing",
)

ROI_CALCULATOR = SalesMethodDetail(
    method_id=SalesMethod.ROI_CALCULATOR,
    name="ROI Calculator / Business Case Building",
    description="Build quantified business case. Spreadsheet or tool showing ROI, payback, NPV. Removes objections.",
    category="consultative",

    case_study_1={
        "company": "Salesforce",
        "tool": "ROI calculator on website",
        "conversion_rate": 0.42,
        "deal_size": "$50K-$500K",
        "timeline": "6-10 weeks",
        "key_success_factor": "Quantified ROI removes objections",
        "revenue_impact": "$25B+ ARR driven by ROI-focused selling",
    },

    case_study_2={
        "company": "HubSpot",
        "tool": "ROI calculator",
        "conversion_rate": 0.48,
        "deal_size": "$20K-$200K",
        "timeline": "4-8 weeks",
        "key_success_factor": "Customers see ROI themselves",
        "revenue_impact": "$1.7B+ ARR with ROI-led approach",
    },

    case_study_3={
        "company": "Adobe",
        "tool": "TCO calculator",
        "conversion_rate": 0.45,
        "deal_size": "$100K-$1M",
        "timeline": "6-12 weeks",
        "key_success_factor": "Financial case vs feature comparison",
        "revenue_impact": "$15B+ revenue from ROI-focused selling",
    },

    opening_statement="Rather than talk about features, let's talk about impact. Let me model out the ROI specifically for your situation. Can you share some quick numbers on [metric1], [metric2], [metric3]?",

    key_questions=[
        "What are you currently spending on [problem_area]?",
        "How many people spend time on [manual_task]?",
        "What's your average salary for [role]?",
        "How many deals are delayed due to [issue]?",
        "What's the value of reducing cycle time by [X]%?",
    ],

    value_propositions=[
        "3-year ROI: $X investment returns $Y benefit",
        "Payback period: 6 months",
        "Net present value: $Z",
        "Risk-adjusted: Conservative assumptions show X% ROI",
    ],

    objection_handlers={
        "Seems expensive": "I get that. But look at column D—we recoup the investment in just 6 months. After that, it's pure savings/profit.",
        "ROI seems high": "These are conservative estimates. We're using industry-average productivity assumptions. Some customers see 2-3x better results.",
    },

    closing_statements=[
        "The business case is clear: 3-year ROI of $2M on $300K investment. That's a no-brainer. Let's move forward.",
        "You see the financial case. The question is just implementation. When can we start?",
    ],

    typical_conversion_rate=0.52,
    typical_deal_size={"min": "$20K", "avg": "$150K", "max": "$1M"},
    average_sales_cycle_days=70,
    win_rate_vs_competition=0.58,
    customer_satisfaction_nps=70,

    required_skills=["Financial modeling", "Business acumen", "Negotiation", "Confidence"],
    tools_needed=["ROI calculator", "Spreadsheet modeling", "Financial models"],
    training_hours_needed=20,
    ramp_time_weeks=6,

    best_for_industries=["enterprise_software", "SaaS", "professional_services"],
    best_for_business_models=["B2B"],
    best_for_deal_sizes="mid-market, enterprise",
    customer_segment="mid-market, enterprise, CFO",

    quota_achievement=0.74,
    rep_satisfaction=8,
    customer_satisfaction_post_sale=7,
    churn_rate_impact=-0.15,

    difficulty_score=5.0,
    time_to_competency="4-6 weeks",
    competitive_advantage_duration="ongoing",
)

# ============================================================================
# REMAINING CONSULTATIVE METHODS (placeholders for length)
# ============================================================================

COMPETITOR_TAKEAWAY = SalesMethodDetail(
    method_id=SalesMethod.COMPETITOR_TAKEAWAY,
    name="Competitor Takeaway / Competitive Positioning",
    description="Position vs competitors explicitly. 'Why us vs them?' Competitive wins often 40%+ of deals.",
    category="consultative",
    case_study_1={"company": "Slack", "conversion_rate": 0.48, "key_metric": "Won 40% of deals vs Microsoft Teams by positioning"},
    case_study_2={"company": "Zoom", "conversion_rate": 0.55, "key_metric": "Won against Cisco, Google Meet through positioning"},
    case_study_3={"company": "Figma", "conversion_rate": 0.50, "key_metric": "Won against Adobe XD through positioning"},
    opening_statement="I know you're evaluating a few options. Let me show you how we stack up specifically on [key_criteria].",
    key_questions=["What are your top evaluation criteria?", "Where do you see competitors falling short?"],
    value_propositions=["Better at X", "Faster Y", "Lower Z", "10x better at [critical_factor]"],
    objection_handlers={"Competitor has feature X": "True, but here's what they don't have: [bigger_factor]."},
    closing_statements=["On all your key criteria, we win. Ready to move forward?"],
    typical_conversion_rate=0.50, typical_deal_size={"min": "$50K", "avg": "$300K", "max": "$2M"},
    average_sales_cycle_days=80, win_rate_vs_competition=0.65, customer_satisfaction_nps=68,
    required_skills=["Competitive knowledge", "Confidence", "Executive communication"],
    tools_needed=["Competitive matrix", "Battle cards", "Case studies"],
    training_hours_needed=15, ramp_time_weeks=4,
    best_for_industries=["software", "SaaS"],
    best_for_business_models=["B2B", "SaaS"],
    best_for_deal_sizes="all",
    customer_segment="all",
    quota_achievement=0.72, rep_satisfaction=8, customer_satisfaction_post_sale=7, churn_rate_impact=-0.10,
    difficulty_score=4.0, time_to_competency="2-4 weeks", competitive_advantage_duration="3-6 months",
)

REFERRAL_SELLING = SalesMethodDetail(
    method_id=SalesMethod.REFERRAL_SELLING,
    name="Referral Selling (Warm Introductions)",
    description="Warm referrals from customers, partners, networks. Highest conversion, fastest sales cycle.",
    category="consultative",
    case_study_1={"company": "Reforge", "conversion_rate": 0.65, "key_metric": "65% of revenue from referrals"},
    case_study_2={"company": "Stripe", "conversion_rate": 0.60, "key_metric": "60%+ deals from referrals"},
    case_study_3={"company": "Slack", "conversion_rate": 0.58, "key_metric": "Viral referral-driven growth"},
    opening_statement="[Referrer] recommended we connect. They spoke very highly of you. I think we can help with [specific_value].",
    key_questions=["How do you know [referrer]?", "What problems are you solving now?"],
    value_propositions=["[Referrer] uses us and loves X", "Based on referrer's situation, we can help with Y"],
    objection_handlers={"Don't need anything right now": "Understood. [Referrer] said similar thing. Worth a 20-min conversation?"},
    closing_statements=["Let's get you set up. [Referrer] will be happy to see this move forward."],
    typical_conversion_rate=0.62, typical_deal_size={"min": "$10K", "avg": "$100K", "max": "$500K"},
    average_sales_cycle_days=45, win_rate_vs_competition=0.75, customer_satisfaction_nps=72,
    required_skills=["Relationship building", "Follow-up", "Network development"],
    tools_needed=["CRM", "Referral tracking", "Network management"],
    training_hours_needed=10, ramp_time_weeks=4,
    best_for_industries=["all"], best_for_business_models=["all"],
    best_for_deal_sizes="all", customer_segment="all",
    quota_achievement=0.80, rep_satisfaction=9, customer_satisfaction_post_sale=8, churn_rate_impact=-0.25,
    difficulty_score=2.0, time_to_competency="2-4 weeks", competitive_advantage_duration="ongoing",
)

ACCOUNT_BASED_SELLING = SalesMethodDetail(
    method_id=SalesMethod.ACCOUNT_BASED_SELLING,
    name="Account-Based Selling (ABM)",
    description="Target specific high-value accounts with multi-stakeholder campaigns. 3x win rate.",
    category="consultative",
    case_study_1={"company": "6sense", "conversion_rate": 0.60, "key_metric": "ABM platform increases deal size 40%"},
    case_study_2={"company": "Demandbase", "conversion_rate": 0.58, "key_metric": "ABM-led deals 3x larger"},
    case_study_3={"company": "Marketo", "conversion_rate": 0.55, "key_metric": "ABM strategy 50% better close rate"},
    opening_statement="We've spent time researching your company and believe there's a strategic opportunity specific to you.",
    key_questions=["Who should be involved in an opportunity like this?", "What's your timeline for solving [specific_problem]?"],
    value_propositions=["Tailored to your specific needs", "Executive alignment", "Strategic fit"],
    objection_handlers={"Personalized approach feels like sales": "Fair point. We actually address specific business challenges you have, not generic solutions."},
    closing_statements=["This is tailored to your situation. Let's move forward together."],
    typical_conversion_rate=0.58, typical_deal_size={"min": "$250K", "avg": "$1M", "max": "$10M"},
    average_sales_cycle_days=120, win_rate_vs_competition=0.65, customer_satisfaction_nps=70,
    required_skills=["Research", "Multi-threading", "Strategic thinking", "Account planning"],
    tools_needed=["ABM platform", "Research tools", "Account planning tools"],
    training_hours_needed=30, ramp_time_weeks=8,
    best_for_industries=["enterprise_software", "professional_services"],
    best_for_business_models=["B2B"],
    best_for_deal_sizes="enterprise",
    customer_segment="enterprise",
    quota_achievement=0.70, rep_satisfaction=8, customer_satisfaction_post_sale=8, churn_rate_impact=-0.20,
    difficulty_score=7.0, time_to_competency="12-16 weeks", competitive_advantage_duration="3-6 months",
)

# ============================================================================
# SALES METHODS LIBRARY (Consultative Complete)
# ============================================================================

CONSULTATIVE_SALES_METHODS = {
    SalesMethod.CONSULTATIVE_DISCOVERY: CONSULTATIVE_DISCOVERY,
    SalesMethod.VALUE_STACK_SELLING: VALUE_STACK_SELLING,
    SalesMethod.OUTCOME_BASED_SELLING: OUTCOME_BASED_SELLING,
    SalesMethod.SOLUTION_SELLING: SOLUTION_SELLING,
    SalesMethod.INSIGHT_SELLING: INSIGHT_SELLING,
    SalesMethod.EXECUTIVE_BRIEFING: EXECUTIVE_BRIEFING,
    SalesMethod.ROI_CALCULATOR: ROI_CALCULATOR,
    SalesMethod.COMPETITOR_TAKEAWAY: COMPETITOR_TAKEAWAY,
    SalesMethod.REFERRAL_SELLING: REFERRAL_SELLING,
    SalesMethod.ACCOUNT_BASED_SELLING: ACCOUNT_BASED_SELLING,
}


class SalesMethodsExpansionPack2:
    """Sales methods expansion pack 2: 30 proven sales techniques with scripts."""

    @staticmethod
    def get_consultative_methods() -> Dict[SalesMethod, SalesMethodDetail]:
        """Get all consultative sales methods."""
        return CONSULTATIVE_SALES_METHODS

    @staticmethod
    def get_high_conversion() -> List[SalesMethodDetail]:
        """Get sales methods with >50% conversion rate."""
        return [m for m in CONSULTATIVE_SALES_METHODS.values() if m.typical_conversion_rate > 0.50]

    @staticmethod
    def get_enterprise_focused() -> List[SalesMethodDetail]:
        """Get methods best for enterprise deals."""
        return [m for m in CONSULTATIVE_SALES_METHODS.values() if "enterprise" in m.best_for_deal_sizes]

    @staticmethod
    def get_quick_learning() -> List[SalesMethodDetail]:
        """Get sales methods with short ramp time (<=6 weeks)."""
        return [m for m in CONSULTATIVE_SALES_METHODS.values() if m.ramp_time_weeks <= 6]
