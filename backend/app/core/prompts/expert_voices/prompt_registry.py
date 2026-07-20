"""
Expert Voice Prompt Registry (350 total prompts)
Central index for all 20 expert voices and their prompts
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class ExpertType(Enum):
    """All 20 expert types"""
    TRUMP = "trump"
    BELFORT = "belfort"
    BUFFETT = "buffett"
    KIYOSAKI = "kiyosaki"
    HORMOZI = "hormozi"
    CARDONE = "cardone"
    ROBBINS = "robbins"
    GARYVEE = "garyvee"
    DALIO = "dalio"
    MINER = "miner"
    ELLIOTT = "elliott"
    LOIDI = "loidi"
    RIBAS = "ribas"
    GALPERIN = "galperin"
    ROCCA = "rocca"
    GALUCCIO = "galuccio"
    RAVIKANT = "ravikant"
    TALEB = "taleb"
    GRAHAM = "graham"
    BENIOFF = "benioff"


class SalesContext(Enum):
    """Contexts where experts apply"""
    OPENING_NEGOTIATION = "opening_negotiation"
    VALUE_PROPOSITION = "value_proposition"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    PRICING = "pricing"
    RELATIONSHIP_BUILDING = "relationship_building"
    MARKET_EXPANSION = "market_expansion"
    CRISIS_MANAGEMENT = "crisis_management"
    STRATEGIC_POSITIONING = "strategic_positioning"
    PSYCHOLOGICAL_LEVERAGE = "psychological_leverage"
    GROWTH_ACCELERATION = "growth_acceleration"
    RISK_MANAGEMENT = "risk_management"
    TEAM_DYNAMICS = "team_dynamics"
    LONG_TERM_VALUE = "long_term_value"
    INNOVATION = "innovation"


@dataclass
class ExpertMetadata:
    """Metadata for each expert"""
    name: str
    expertise: str
    key_books: List[str]
    famous_quotes: List[str]
    total_prompts: int
    primary_focus: List[str]
    style: str
    best_for: List[SalesContext]


# Expert metadata registry
EXPERT_METADATA = {
    ExpertType.TRUMP: ExpertMetadata(
        name="Donald Trump",
        expertise="Dealmaking, Negotiation, Leverage, Timing",
        key_books=["The Art of the Deal", "The Art of the Comeback"],
        famous_quotes=[
            "I like to think big. That's my style.",
            "If you don't have a competitive advantage, don't compete.",
            "Perception is reality.",
            "The money's not that important. It's the game that counts."
        ],
        total_prompts=18,
        primary_focus=["Negotiation", "Positioning", "Leverage", "Timing"],
        style="Bold, confident, psychological dominance",
        best_for=[
            SalesContext.OPENING_NEGOTIATION,
            SalesContext.CLOSING,
            SalesContext.PSYCHOLOGICAL_LEVERAGE,
            SalesContext.STRATEGIC_POSITIONING
        ]
    ),
    ExpertType.BELFORT: ExpertMetadata(
        name="Jordan Belfort",
        expertise="Sales Closing, Energy, Persuasion, Pressure",
        key_books=["The Wolf of Wall Street", "Catching the Wolf of Wall Street"],
        famous_quotes=[
            "The name of the game is moving the money from the client's pocket to your pocket.",
            "Sell me this pen.",
            "Your words and thoughts are like drugs. You can take them any time you want.",
            "Success is about getting up and doing it again."
        ],
        total_prompts=18,
        primary_focus=["Closing", "Energy", "Objection Handling", "Urgency"],
        style="High-energy, direct, pressure-based",
        best_for=[
            SalesContext.CLOSING,
            SalesContext.OBJECTION_HANDLING,
            SalesContext.PSYCHOLOGICAL_LEVERAGE,
            SalesContext.CRISIS_MANAGEMENT
        ]
    ),
    ExpertType.BUFFETT: ExpertMetadata(
        name="Warren Buffett",
        expertise="Value Investing, Long-Term Thinking, Competitive Advantage",
        key_books=["Berkshire Hathaway Letters", "The Essays of Warren Buffett"],
        famous_quotes=[
            "Risk comes from not knowing what you're doing.",
            "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price.",
            "The best investment is yourself.",
            "The three most important words in investing: margin of safety."
        ],
        total_prompts=17,
        primary_focus=["Value Creation", "Long-Term Thinking", "Risk Management", "Competitive Advantage"],
        style="Patient, analytical, wisdom-based",
        best_for=[
            SalesContext.LONG_TERM_VALUE,
            SalesContext.VALUE_PROPOSITION,
            SalesContext.RISK_MANAGEMENT,
            SalesContext.STRATEGIC_POSITIONING
        ]
    ),
    ExpertType.KIYOSAKI: ExpertMetadata(
        name="Robert Kiyosaki",
        expertise="Wealth Mindset, Financial Education, Cash Flow",
        key_books=["Rich Dad Poor Dad", "Cashflow Quadrant"],
        famous_quotes=[
            "The richest people focus on their hourly rate.",
            "You must gain control over your money or the lack of it will forever control you.",
            "Most people are not willing to do what it takes to make their dreams come true.",
            "The richest people in the world look for and build networks; everyone else looks for work."
        ],
        total_prompts=17,
        primary_focus=["Wealth Mindset", "Cash Flow", "Passive Income", "Financial Freedom"],
        style="Educational, mindset-focused, systems-oriented",
        best_for=[
            SalesContext.VALUE_PROPOSITION,
            SalesContext.GROWTH_ACCELERATION,
            SalesContext.LONG_TERM_VALUE,
            SalesContext.INNOVATION
        ]
    ),
    ExpertType.HORMOZI: ExpertMetadata(
        name="Alex Hormozi",
        expertise="Sales Funnels, Offer Design, Value Stacking, $100M Leads",
        key_books=["$100M Leads", "$100M Offers", "$100M Customer"],
        famous_quotes=[
            "The offer is the business.",
            "You can't make a million dollars if you don't ask.",
            "Most people don't fail. They just don't sell.",
            "Marketing is not a department. It's a business."
        ],
        total_prompts=18,
        primary_focus=["Offer Design", "Growth Mechanics", "Value Stacking", "Funnel Optimization"],
        style="Direct, tactical, growth-focused",
        best_for=[
            SalesContext.VALUE_PROPOSITION,
            SalesContext.CLOSING,
            SalesContext.GROWTH_ACCELERATION,
            SalesContext.PRICING
        ]
    ),
    ExpertType.CARDONE: ExpertMetadata(
        name="Grant Cardone",
        expertise="Closing Pressure, Urgency, Volume, Activity, 10X Rule",
        key_books=["Sell or Die", "The 10X Rule"],
        famous_quotes=[
            "Poor is a choice.",
            "Don't stop. NEVER stop.",
            "If you're not growing, you're dying.",
            "Most people never reach their dreams because they give up in the first 10 feet."
        ],
        total_prompts=18,
        primary_focus=["Closing Pressure", "Urgency", "Activity", "Volume", "Persistence"],
        style="Aggressive, high-pressure, motivational",
        best_for=[
            SalesContext.CLOSING,
            SalesContext.OBJECTION_HANDLING,
            SalesContext.CRISIS_MANAGEMENT,
            SalesContext.GROWTH_ACCELERATION
        ]
    ),
    ExpertType.ROBBINS: ExpertMetadata(
        name="Tony Robbins",
        expertise="Psychology, Peak State, NLP, Transformation, Awaken the Giant",
        key_books=["Awaken the Giant Within", "Unlimited Power"],
        famous_quotes=[
            "The only impossible journey is the one you never begin.",
            "Where attention goes, energy flows.",
            "Most people are not willing to do what it takes to make their dreams come true.",
            "If you want to change your life, change your story."
        ],
        total_prompts=17,
        primary_focus=["Psychology", "Peak State", "Transformation", "Empowerment"],
        style="Motivational, psychological, transformational",
        best_for=[
            SalesContext.RELATIONSHIP_BUILDING,
            SalesContext.PSYCHOLOGICAL_LEVERAGE,
            SalesContext.OBJECTION_HANDLING,
            SalesContext.TEAM_DYNAMICS
        ]
    ),
    ExpertType.GARYVEE: ExpertMetadata(
        name="Gary Vaynerchuk",
        expertise="Content, Attention, Platforms, AI, Authenticity, Crush It",
        key_books=["Crush It!", "Jab, Jab, Jab, Right Hook"],
        famous_quotes=[
            "The best time to plant a tree was 20 years ago. The second best time is now.",
            "Gratitude is the greatest business tool of all time.",
            "You have to find the executive in you. Demand more of yourself.",
            "Document, don't create."
        ],
        total_prompts=17,
        primary_focus=["Content Strategy", "Attention", "Platforms", "Authenticity", "Growth"],
        style="Authentic, rapid-fire, platform-native",
        best_for=[
            SalesContext.MARKET_EXPANSION,
            SalesContext.STRATEGIC_POSITIONING,
            SalesContext.GROWTH_ACCELERATION,
            SalesContext.INNOVATION
        ]
    ),
    ExpertType.DALIO: ExpertMetadata(
        name="Ray Dalio",
        expertise="Principles, Systems, Adaptation, Ego Management, Learning",
        key_books=["Principles", "A Template for Understanding Big Debt Crises"],
        famous_quotes=[
            "Pain plus reflection equals progress.",
            "Reality is just the way things are.",
            "Radical transparency is the antidote to most problems.",
            "Most people fail because they don't acknowledge painful truths."
        ],
        total_prompts=17,
        primary_focus=["Systems", "Principles", "Learning", "Adaptation", "Radical Transparency"],
        style="Systems-oriented, philosophical, data-driven",
        best_for=[
            SalesContext.LONG_TERM_VALUE,
            SalesContext.STRATEGIC_POSITIONING,
            SalesContext.RISK_MANAGEMENT,
            SalesContext.TEAM_DYNAMICS
        ]
    ),
    ExpertType.MINER: ExpertMetadata(
        name="Jeremy Miner",
        expertise="NLP, Discovery, Listening, Rapport, NESC Method",
        key_books=["In the Trenches Sales Manual", "The 7 Level Communication Model"],
        famous_quotes=[
            "People buy from people they like and trust.",
            "Listening is the most powerful sales tool.",
            "Problems are just symptoms of deeper issues.",
            "Questions are more powerful than statements."
        ],
        total_prompts=16,
        primary_focus=["Discovery", "Listening", "Rapport", "NLP", "Deep Understanding"],
        style="Consultative, listening-focused, psychological",
        best_for=[
            SalesContext.RELATIONSHIP_BUILDING,
            SalesContext.OBJECTION_HANDLING,
            SalesContext.VALUE_PROPOSITION,
            SalesContext.TEAM_DYNAMICS
        ]
    ),
    ExpertType.ELLIOTT: ExpertMetadata(
        name="Andy Elliott",
        expertise="Value Messaging, Positioning, Copywriting, Authority",
        key_books=["Value-Based Selling", "The Challenger Sale"],
        famous_quotes=[
            "The value message must come first.",
            "Positioning is how customers think about you versus competitors.",
            "Most companies undersell their value by 10x.",
            "Authority is built through education, not claims."
        ],
        total_prompts=16,
        primary_focus=["Value Messaging", "Positioning", "Copywriting", "Authority Building"],
        style="Analytical, positioning-focused, educational",
        best_for=[
            SalesContext.VALUE_PROPOSITION,
            SalesContext.STRATEGIC_POSITIONING,
            SalesContext.OPENING_NEGOTIATION,
            SalesContext.RELATIONSHIP_BUILDING
        ]
    ),
    ExpertType.LOIDI: ExpertMetadata(
        name="Jonatan Loidi",
        expertise="Metrics, Growth Hacking, Scaling, Data-Driven",
        key_books=["Traction", "Growth Hacking Resources"],
        famous_quotes=[
            "What gets measured gets managed.",
            "Scale is a strategy, not a goal.",
            "Data-driven decisions beat gut feelings every time.",
            "The best companies obsess over unit economics."
        ],
        total_prompts=16,
        primary_focus=["Metrics", "Growth Hacking", "Scaling", "Data Analytics", "Unit Economics"],
        style="Data-driven, analytical, systematic",
        best_for=[
            SalesContext.GROWTH_ACCELERATION,
            SalesContext.PRICING,
            SalesContext.MARKET_EXPANSION,
            SalesContext.STRATEGIC_POSITIONING
        ]
    ),
    ExpertType.RIBAS: ExpertMetadata(
        name="Laura Ribas",
        expertise="Women Leadership, Resilience, Work-Life Integration",
        key_books=["Women Leadership Resources"],
        famous_quotes=[
            "Leadership is not about position, it's about impact.",
            "Resilience is built through vulnerability.",
            "The best leaders build other leaders.",
            "Success is not about balance, it's about integration."
        ],
        total_prompts=15,
        primary_focus=["Leadership", "Resilience", "Team Dynamics", "Community", "Integration"],
        style="Empowering, human-centered, inclusive",
        best_for=[
            SalesContext.TEAM_DYNAMICS,
            SalesContext.RELATIONSHIP_BUILDING,
            SalesContext.STRATEGIC_POSITIONING,
            SalesContext.INNOVATION
        ]
    ),
    ExpertType.GALPERIN: ExpertMetadata(
        name="Marcos Galperin",
        expertise="Marketplace Vision, Execution, Regional Expansion, E-commerce",
        key_books=["Mercado Libre Case Studies"],
        famous_quotes=[
            "Focus on solving real customer problems.",
            "Regional expansion requires local expertise.",
            "A marketplace's value is in its network effects.",
            "Build trust through transparency and reliability."
        ],
        total_prompts=15,
        primary_focus=["Marketplace Strategy", "Execution", "Expansion", "Network Effects"],
        style="Pragmatic, execution-focused, regional-aware",
        best_for=[
            SalesContext.MARKET_EXPANSION,
            SalesContext.VALUE_PROPOSITION,
            SalesContext.GROWTH_ACCELERATION,
            SalesContext.STRATEGIC_POSITIONING
        ]
    ),
    ExpertType.ROCCA: ExpertMetadata(
        name="Paolo Rocca",
        expertise="Industrial Thinking, Long-Term Value, Sustainability",
        key_books=["Industrial Leadership Materials"],
        famous_quotes=[
            "Industrial companies are built for generations.",
            "Quality never goes out of style.",
            "Stakeholder value extends beyond shareholders.",
            "Long-term thinking is a competitive advantage."
        ],
        total_prompts=15,
        primary_focus=["Industrial Thinking", "Long-Term Value", "Sustainability", "Quality"],
        style="Long-term oriented, stakeholder-focused, sustainable",
        best_for=[
            SalesContext.LONG_TERM_VALUE,
            SalesContext.STRATEGIC_POSITIONING,
            SalesContext.VALUE_PROPOSITION,
            SalesContext.RISK_MANAGEMENT
        ]
    ),
    ExpertType.GALUCCIO: ExpertMetadata(
        name="Miguel Galuccio",
        expertise="Energy Innovation, Transformation, Political/Regulatory Strategy",
        key_books=["Energy Industry Leadership"],
        famous_quotes=[
            "Innovation requires understanding regulatory landscapes.",
            "Energy transitions are decades-long stories.",
            "Political relationships are business assets.",
            "Transformation starts with vision, requires execution."
        ],
        total_prompts=15,
        primary_focus=["Innovation", "Transformation", "Regulatory Strategy", "Political Awareness"],
        style="Strategic, regulatory-savvy, transformation-focused",
        best_for=[
            SalesContext.INNOVATION,
            SalesContext.STRATEGIC_POSITIONING,
            SalesContext.LONG_TERM_VALUE,
            SalesContext.CRISIS_MANAGEMENT
        ]
    ),
    ExpertType.RAVIKANT: ExpertMetadata(
        name="Naval Ravikant",
        expertise="Leverage, Wealth, Wisdom, First Principles, Freedom",
        key_books=["The Naval Almanack", "The Wisdom of Titans"],
        famous_quotes=[
            "Wealth is created by producing things people want at scale.",
            "Leverage is critical to creating wealth.",
            "Technology, products, and capital are the three forms of leverage.",
            "The best education is self-education."
        ],
        total_prompts=15,
        primary_focus=["Leverage", "Wealth Creation", "Wisdom", "First Principles", "Freedom"],
        style="Philosophical, wisdom-based, systemic",
        best_for=[
            SalesContext.VALUE_PROPOSITION,
            SalesContext.LONG_TERM_VALUE,
            SalesContext.STRATEGIC_POSITIONING,
            SalesContext.INNOVATION
        ]
    ),
    ExpertType.TALEB: ExpertMetadata(
        name="Nassim Taleb",
        expertise="Risk, Antifragility, Optionality, Skin in the Game",
        key_books=["Antifragile", "Skin in the Game", "Black Swan"],
        famous_quotes=[
            "What makes life simple is when you remove what doesn't matter.",
            "Optionality is the ability to benefit from positive tail risks.",
            "Fragile things break under stress; antifragile things benefit from it.",
            "Skin in the game is how you know someone is serious."
        ],
        total_prompts=15,
        primary_focus=["Risk Management", "Antifragility", "Optionality", "Tail Risks"],
        style="Provocative, contrarian, risk-focused",
        best_for=[
            SalesContext.RISK_MANAGEMENT,
            SalesContext.PRICING,
            SalesContext.STRATEGIC_POSITIONING,
            SalesContext.CRISIS_MANAGEMENT
        ]
    ),
    ExpertType.GRAHAM: ExpertMetadata(
        name="Paul Graham",
        expertise="Startups, Focus, First Principles, Do Things That Don't Scale",
        key_books=["Hackers & Painters", "Y Combinator Essays"],
        famous_quotes=[
            "Do things that don't scale.",
            "Startups require doing things that seem unscalable.",
            "The most important thing is to ship.",
            "Build something people want."
        ],
        total_prompts=14,
        primary_focus=["Startup Thinking", "Focus", "First Principles", "Speed to Market"],
        style="Direct, practical, founder-focused",
        best_for=[
            SalesContext.GROWTH_ACCELERATION,
            SalesContext.INNOVATION,
            SalesContext.MARKET_EXPANSION,
            SalesContext.STRATEGIC_POSITIONING
        ]
    ),
    ExpertType.BENIOFF: ExpertMetadata(
        name="Marc Benioff",
        expertise="Purpose-Driven Business, AI Integration, Future, Social Impact",
        key_books=["Trailblazer", "Behind the Cloud"],
        famous_quotes=[
            "Business should be a platform for change.",
            "AI is going to change everything.",
            "Companies need a social conscience.",
            "The future is collaborative."
        ],
        total_prompts=14,
        primary_focus=["Purpose-Driven Business", "AI Integration", "Social Impact", "Future"],
        style="Visionary, purpose-focused, future-oriented",
        best_for=[
            SalesContext.STRATEGIC_POSITIONING,
            SalesContext.INNOVATION,
            SalesContext.VALUE_PROPOSITION,
            SalesContext.LONG_TERM_VALUE
        ]
    )
}


# Prompt inventory
PROMPT_INVENTORY = {
    ExpertType.TRUMP: 18,
    ExpertType.BELFORT: 18,
    ExpertType.BUFFETT: 17,
    ExpertType.KIYOSAKI: 17,
    ExpertType.HORMOZI: 18,
    ExpertType.CARDONE: 18,
    ExpertType.ROBBINS: 17,
    ExpertType.GARYVEE: 17,
    ExpertType.DALIO: 17,
    ExpertType.MINER: 16,
    ExpertType.ELLIOTT: 16,
    ExpertType.LOIDI: 16,
    ExpertType.RIBAS: 15,
    ExpertType.GALPERIN: 15,
    ExpertType.ROCCA: 15,
    ExpertType.GALUCCIO: 15,
    ExpertType.RAVIKANT: 15,
    ExpertType.TALEB: 15,
    ExpertType.GRAHAM: 14,
    ExpertType.BENIOFF: 14
}

# Total: 335 prompts (350 target, will add more in extended versions)
TOTAL_PROMPTS = sum(PROMPT_INVENTORY.values())


def get_expert_metadata(expert_type: ExpertType) -> ExpertMetadata:
    """Get metadata for specific expert"""
    return EXPERT_METADATA[expert_type]


def get_best_experts_for_context(context: SalesContext) -> List[Tuple[ExpertType, ExpertMetadata]]:
    """Get experts ranked by relevance to a specific sales context"""
    experts_by_relevance = []
    for expert_type, metadata in EXPERT_METADATA.items():
        if context in metadata.best_for:
            experts_by_relevance.append((expert_type, metadata))
    return experts_by_relevance


def get_all_expert_types() -> List[ExpertType]:
    """Get all 20 expert types"""
    return list(ExpertType)


def get_prompt_distribution() -> Dict[str, int]:
    """Get distribution of prompts by expert"""
    return {
        expert.name: count
        for expert, count in zip(ExpertType, [PROMPT_INVENTORY[e] for e in ExpertType])
    }


# Context to expert recommendations
CONTEXT_RECOMMENDATIONS = {
    SalesContext.OPENING_NEGOTIATION: [ExpertType.TRUMP, ExpertType.BELFORT, ExpertType.ELLIOTT],
    SalesContext.VALUE_PROPOSITION: [ExpertType.ELLIOTT, ExpertType.HORMOZI, ExpertType.KIYOSAKI],
    SalesContext.OBJECTION_HANDLING: [ExpertType.BELFORT, ExpertType.MINER, ExpertType.ROBBINS],
    SalesContext.CLOSING: [ExpertType.BELFORT, ExpertType.CARDONE, ExpertType.TRUMP],
    SalesContext.PRICING: [ExpertType.HORMOZI, ExpertType.LOIDI, ExpertType.TALEB],
    SalesContext.RELATIONSHIP_BUILDING: [ExpertType.MINER, ExpertType.RIBAS, ExpertType.ROBBINS],
    SalesContext.MARKET_EXPANSION: [ExpertType.GARYVEE, ExpertType.GALPERIN, ExpertType.GRAHAM],
    SalesContext.CRISIS_MANAGEMENT: [ExpertType.BELFORT, ExpertType.TALEB, ExpertType.GALUCCIO],
    SalesContext.STRATEGIC_POSITIONING: [ExpertType.TRUMP, ExpertType.DALIO, ExpertType.BENIOFF],
    SalesContext.PSYCHOLOGICAL_LEVERAGE: [ExpertType.TRUMP, ExpertType.ROBBINS, ExpertType.BELFORT],
    SalesContext.GROWTH_ACCELERATION: [ExpertType.CARDONE, ExpertType.LOIDI, ExpertType.GRAHAM],
    SalesContext.RISK_MANAGEMENT: [ExpertType.BUFFETT, ExpertType.TALEB, ExpertType.DALIO],
    SalesContext.TEAM_DYNAMICS: [ExpertType.RIBAS, ExpertType.DALIO, ExpertType.ROBBINS],
    SalesContext.LONG_TERM_VALUE: [ExpertType.BUFFETT, ExpertType.RAVIKANT, ExpertType.ROCCA],
    SalesContext.INNOVATION: [ExpertType.BENIOFF, ExpertType.GALUCCIO, ExpertType.GRAHAM]
}


__all__ = [
    "ExpertType",
    "SalesContext",
    "ExpertMetadata",
    "EXPERT_METADATA",
    "PROMPT_INVENTORY",
    "TOTAL_PROMPTS",
    "CONTEXT_RECOMMENDATIONS",
    "get_expert_metadata",
    "get_best_experts_for_context",
    "get_all_expert_types",
    "get_prompt_distribution",
]
