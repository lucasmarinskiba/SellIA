"""
Negotiation Agent — Negotiation frameworks and deal strategy.

Specialties:
- Negotiation frameworks (BATNA, anchoring, concessions)
- Supplier negotiation
- Customer negotiations
- Employment negotiations
- Deal structures and risk allocation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class NegotiationType(str, Enum):
    """Types of negotiations."""
    CUSTOMER_SALES = "customer_sales"  # Negotiating with customer to close deal
    SUPPLIER = "supplier"  # Negotiating with supplier for better terms
    EMPLOYMENT = "employment"  # Salary, benefits negotiations
    PARTNERSHIP = "partnership"  # Partner agreement terms
    INVESTMENT = "investment"  # Equity, funding terms
    VENDOR = "vendor"  # Service provider terms


class NegotiationPhase(str, Enum):
    """Phases of negotiation."""
    PREPARATION = "preparation"
    OPENING = "opening"
    INFORMATION_EXCHANGE = "information_exchange"
    BARGAINING = "bargaining"
    AGREEMENT = "agreement"
    CLOSING = "closing"


class NegotiationAgent:
    """Expert in negotiation strategy and tactics."""

    NEGOTIATION_FRAMEWORKS = {
        "batna": {
            "name": "BATNA (Best Alternative to Negotiated Agreement)",
            "description": "Your best option if negotiation fails",
            "importance": "Determines your walk-away point",
            "calculation": [
                "1. List alternatives if deal doesn't happen",
                "2. Evaluate pros/cons of each",
                "3. Choose best alternative",
                "4. Know your BATNA number",
            ],
            "strategic_use": [
                "Confidently set your minimum acceptable terms",
                "Know when to walk away",
                "Increase confidence in negotiation",
                "Don't accept worse than BATNA",
            ],
            "example": "If supplier won't reduce price: find alternative supplier",
        },

        "anchoring": {
            "name": "Anchoring",
            "description": "First number mentioned influences final price",
            "principle": "Whoever suggests price first has advantage",
            "tactics": [
                "Make first offer (suggest lower for buying, higher for selling)",
                "Research what they expect",
                "Use anchor from credible source",
                "Make anchor realistic to be taken seriously",
            ],
            "counter_tactic": [
                "Don't accept first anchor - counter immediately",
                "Suggest different anchor from credible source",
                "Explain why anchor is unrealistic",
                "Suggest midpoint if both anchors reasonable",
            ],
        },

        "zone_of_possible_agreement": {
            "name": "ZOPA (Zone of Possible Agreement)",
            "description": "Range where both parties can agree",
            "framework": {
                "your_ideal": "Your best case scenario",
                "your_acceptable_range": "Minimum to maximum",
                "their_ideal": "What they want",
                "their_acceptable_range": "Their minimum to maximum",
                "zopa": "Overlap between both ranges",
            },
            "strategy": "Expand ZOPA by finding shared interests",
        },

        "win_win": {
            "name": "Win-Win (Integrative) Negotiation",
            "description": "Create value for both parties",
            "principles": [
                "Separate people from problem",
                "Focus on interests, not positions",
                "Generate options for mutual gain",
                "Use objective criteria",
            ],
            "tactics": [
                "Ask 'why' questions to understand real interests",
                "Look for different value of items to each side",
                "Create package deals",
                "Explore non-monetary benefits",
            ],
            "example": "Buyer wants lower price, seller wants volume - offer volume discount",
        },

        "concessions": {
            "name": "Concessions Strategy",
            "description": "How to make and request concessions",
            "guidelines": [
                "Don't make one-sided concessions",
                "Every concession should have trade-off",
                "Concessions should decrease in size",
                "Ask for concession after giving one",
            ],
            "pattern": [
                "You concede $10K on price",
                "They concede on payment terms",
                "You concede on timeline",
                "They commit to multi-year contract",
            ],
            "avoid": [
                "Giving without asking for return",
                "Matching every concession 1:1",
                "Conceding on your must-haves",
            ],
        },
    }

    NEGOTIATION_TACTICS = {
        "information_gathering": {
            "description": "Understand other party's position",
            "questions": [
                "What are their business goals?",
                "What are their constraints?",
                "What do they value most?",
                "What's their timeline?",
                "What are they afraid of?",
                "What's their BATNA?",
            ],
            "methods": [
                "Direct questions",
                "Research (LinkedIn, company info)",
                "Industry knowledge",
                "References and past deals",
            ],
        },

        "active_listening": {
            "description": "Understand what's really important",
            "techniques": [
                "Don't interrupt",
                "Ask clarifying questions",
                "Paraphrase to confirm understanding",
                "Notice what they emphasize",
                "Read between the lines",
            ],
            "benefits": [
                "Identify real interests",
                "Find creative solutions",
                "Build rapport and trust",
                "Avoid misunderstandings",
            ],
        },

        "patience": {
            "description": "Don't rush or get emotional",
            "tactics": [
                "Let silence work for you",
                "Take breaks when frustrated",
                "Take time to think before responding",
                "Don't show eagerness",
                "Walk away if needed",
            ],
            "psychological_edge": "Rushed party accepts worse terms",
        },

        "bracketing": {
            "description": "Stay flexible within range",
            "approach": [
                "Set minimum acceptable (BATNA)",
                "Set ideal outcome (goal)",
                "Anchor above goal",
                "Move toward goal gradually",
            ],
            "example": "Buy price minimum $50K, goal $55K, anchor at $60K, move down gradually",
        },

        "flinching": {
            "description": "React with surprise to proposal",
            "when_to_use": "When other party makes unreasonable ask",
            "technique": [
                "Show emotional reaction (shock, dismay)",
                "Say 'That's much higher than expected'",
                "Go silent",
                "Let them fill silence with explanation/concession",
            ],
            "risk": "Overuse makes you lose credibility",
        },

        "nibbling": {
            "description": "Ask for small additional items",
            "when_to_use": "At end of negotiation when deal nearly done",
            "examples": [
                "Extended payment terms",
                "Free setup support",
                "Included training",
                "Extended warranty",
            ],
            "psychology": "Small asks seem reasonable when deal is near",
        },
    }

    NEGOTIATION_SCENARIOS = {
        NegotiationType.CUSTOMER_SALES: {
            "goal": "Close deal at best price/terms",
            "key_variables": [
                "Contract value",
                "Payment terms",
                "Delivery timeline",
                "Support level",
                "Exclusivity",
            ],
            "common_objections": [
                "Price is too high",
                "Need more time",
                "Need approval from above",
                "Want to compare with competitors",
            ],
            "closing_tactics": [
                "Trial close: 'Does this work for you?'",
                "Summary close: 'So we've agreed on...'",
                "Assumptive close: 'We'll start implementation on...'",
                "Alternative close: 'Monthly or annual billing?'",
            ],
        },

        NegotiationType.SUPPLIER: {
            "goal": "Get best price and terms from supplier",
            "leverage": [
                "Volume commitment",
                "Long-term contract",
                "Public case study",
                "Referrals",
                "Competition",
            ],
            "negotiation_points": [
                "Unit price",
                "Volume discounts",
                "Payment terms (30/60/90 days)",
                "Delivery timeline",
                "Quality guarantees",
                "Exclusivity",
            ],
            "preparation": [
                "Get competing quotes",
                "Know market prices",
                "Understand supplier's costs",
                "Know their other customers",
            ],
        },

        NegotiationType.EMPLOYMENT: {
            "goal": "Get best compensation package",
            "negotiable_items": [
                "Base salary",
                "Bonus structure",
                "Equity/stock options",
                "Benefits (health, 401k)",
                "Vacation days",
                "Remote work flexibility",
                "Professional development budget",
                "Start date",
            ],
            "research": [
                "Industry salary benchmarks",
                "Company financial health",
                "Cost of living adjustments",
                "Competitor offers",
            ],
            "strategy": [
                "Let them make offer first",
                "Know your minimum acceptable",
                "Focus on total package, not just salary",
                "Negotiate one item at a time",
                "Get offer in writing",
            ],
        },

        NegotiationType.PARTNERSHIP: {
            "goal": "Establish clear terms and mutual benefits",
            "key_terms": [
                "Roles and responsibilities",
                "Revenue sharing",
                "Decision-making authority",
                "Conflict resolution",
                "Exit clauses",
                "Intellectual property",
                "Non-compete",
            ],
            "preparation": [
                "Clear on your value contribution",
                "Understand partner's needs",
                "Document everything in writing",
                "Get legal review",
            ],
        },
    }

    DEAL_STRUCTURES = {
        "straight_transaction": {
            "description": "Simple buy/sell agreement",
            "terms": [
                "Price",
                "Delivery terms",
                "Payment terms",
                "Warranties",
            ],
        },
        "payment_plan": {
            "description": "Payment spread over time",
            "variations": [
                "Installments (equal payments)",
                "Milestone-based (pay for completion)",
                "Performance-based (pay for results)",
            ],
            "benefit_to_seller": "Higher total value",
            "benefit_to_buyer": "Lower upfront cost",
        },
        "volume_discount": {
            "description": "Price breaks for larger quantities",
            "structure": [
                "1-10 units: $100",
                "11-50 units: $85",
                "50+ units: $70",
            ],
        },
        "contingent_payment": {
            "description": "Payment contingent on results",
            "example": "Pay for consulting only if revenue increases by 20%",
            "benefit": "Aligns incentives",
        },
    }

    @staticmethod
    def prepare_negotiation(
        negotiation_type: NegotiationType,
        other_party: str,
        objective: str
    ) -> Dict[str, Any]:
        """Prepare for negotiation."""
        preparation = {
            "negotiation_type": negotiation_type.value,
            "other_party": other_party,
            "objective": objective,
            "must_haves": [],
            "nice_to_haves": [],
            "walk_away_points": [],
            "research": {
                "their_business": "",
                "their_constraints": "",
                "market_conditions": "",
                "competitive_landscape": "",
            },
            "batna": {
                "best_alternative": "",
                "BATNA_value": 0,
                "walk_away_point": "",
            },
            "anticipated_asks": [],
            "your_concessions": [],
            "their_likely_concessions": [],
            "opening_position": {},
            "target_outcome": {},
            "fallback_positions": [],
            "strategy": "",
        }

        return preparation

    @staticmethod
    def analyze_negotiation_position(
        current_offer: Dict[str, Any],
        must_haves: List[str],
        nice_to_haves: List[str],
        batna_value: float
    ) -> Dict[str, Any]:
        """Analyze your negotiation position."""
        analysis = {
            "current_offer": current_offer,
            "must_haves": must_haves,
            "nice_to_haves": nice_to_haves,
            "batna_value": batna_value,
            "position_strength": "Weak/Medium/Strong",
            "acceptable": True,
            "gaps_from_must_haves": [],
            "opportunities": [],
            "recommendations": [],
        }

        return analysis

    @staticmethod
    def create_offer(
        base_value: float,
        margin: float,
        anchor_strategy: str = "high"
    ) -> Dict[str, Any]:
        """Create opening offer."""
        if anchor_strategy == "high":
            # For selling, anchor high
            offer = base_value * (1 + margin)
        else:
            # For buying, anchor low
            offer = base_value * (1 - margin)

        return {
            "opening_offer": round(offer, 2),
            "base_value": base_value,
            "margin": f"{margin*100:.1f}%",
            "anchor_strategy": anchor_strategy,
            "rationale": "First number influences negotiation",
            "expected_counterproposal": round(base_value, 2),
            "likely_settlement": round((offer + base_value) / 2, 2),
        }

    @staticmethod
    def handle_objection(
        objection: str,
        your_position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle objection in negotiation."""
        strategies = {
            "price_objection": {
                "reframe": "Not about cost, it's about value",
                "response": "Here's the ROI/value you'll get",
                "tactic": "Translate price to value per unit or per year",
            },
            "timeline_objection": {
                "reframe": "Understand their real constraint",
                "response": "Can we phase implementation?",
                "tactic": "Break into milestone payments",
            },
            "authority_objection": {
                "reframe": "They need to get approval",
                "response": "Let's prepare documentation to help them get buy-in",
                "tactic": "Create proposal/business case for their decision-maker",
            },
            "comparison_objection": {
                "reframe": "They're comparing you to alternative",
                "response": "Here's how we differ: ...",
                "tactic": "Highlight unique value only you offer",
            },
        }

        return {
            "objection": objection,
            "strategy": strategies.get(objection, {}),
            "your_response": "",
            "follow_up_questions": [],
            "concession_if_needed": None,
        }

    @staticmethod
    def build_deal_structure(
        base_transaction_value: float,
        timeline_months: int,
        key_terms: List[str]
    ) -> Dict[str, Any]:
        """Build optimized deal structure."""
        return {
            "base_value": base_transaction_value,
            "timeline": f"{timeline_months} months",
            "structure_options": [
                {
                    "name": "Upfront payment",
                    "total": base_transaction_value,
                    "pro": "Immediate cash",
                    "con": "Higher risk for buyer",
                },
                {
                    "name": "Monthly installments",
                    "monthly": base_transaction_value / timeline_months,
                    "total": base_transaction_value,
                    "pro": "Lower buyer risk",
                    "con": "Ongoing administration",
                },
                {
                    "name": "Milestone-based",
                    "milestones": [f"Milestone {i+1}" for i in range(timeline_months // 3)],
                    "pro": "Aligns incentives",
                    "con": "Tied to performance",
                },
            ],
            "recommendation": "",
            "key_terms": key_terms,
            "contingencies": [],
        }

    @staticmethod
    def get_negotiation_framework(negotiation_type: NegotiationType) -> Dict[str, Any]:
        """Get framework for negotiation type."""
        return NegotiationAgent.NEGOTIATION_SCENARIOS.get(negotiation_type, {})

    @staticmethod
    def negotiation_checklist(
        negotiation_type: NegotiationType
    ) -> Dict[str, List[str]]:
        """Get pre-negotiation checklist."""
        return {
            "research": [
                "Know other party's business model",
                "Understand their constraints",
                "Research market rates/benchmarks",
                "Know their key decision-makers",
            ],
            "preparation": [
                "Define your BATNA clearly",
                "List must-haves vs nice-to-haves",
                "Set opening position",
                "Anticipate their objections",
                "Plan your concessions",
            ],
            "logistics": [
                "Schedule negotiation (not rushed)",
                "Prepare materials/documentation",
                "Decide team members",
                "Plan meeting location (neutral?)",
                "Set agenda",
            ],
            "mindset": [
                "Go in with positive attitude",
                "View as problem-solving, not battle",
                "Be willing to walk away",
                "Don't get emotional",
                "Listen more than talk",
            ],
        }

    @staticmethod
    def closing_strategies() -> Dict[str, Dict[str, Any]]:
        """Get deal closing strategies."""
        return {
            "summary_close": {
                "technique": "Recap everything agreed upon",
                "wording": "So to confirm, we've agreed on: price $X, delivery Y, terms Z. Is that correct?",
                "psychology": "Gets confirmation and moves toward closure",
            },
            "assumptive_close": {
                "technique": "Assume the deal is done",
                "wording": "Great! Let's get this scheduled. When can we start implementation?",
                "psychology": "Moves past closing to next steps",
            },
            "alternative_close": {
                "technique": "Give binary choice",
                "wording": "Would you prefer monthly or annual billing?",
                "psychology": "Both options assume purchase",
            },
            "urgency_close": {
                "technique": "Create time pressure",
                "wording": "This pricing is only good through end of month",
                "psychology": "Fear of missing out drives decision",
                "caution": "Use only if genuine; trust erosion if perceived as manipulation",
            },
        }
