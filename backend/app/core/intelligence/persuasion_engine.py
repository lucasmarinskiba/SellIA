"""
Persuasion Engine — Cialdini + Kahneman + neuromarketing + language patterns.

Técnicas:
- Cialdini: reciprocity, scarcity, authority, social proof, liking, commitment
- Kahneman: loss aversion, sunk cost, anchoring, availability, framing
- Neuromarketing: emotional triggers, color psychology, social proof levels
- Language patterns: Milton model, presuppositions, embedded commands, metaphor
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PersuasionEngine:
    """Persuade automático usando psicología demostrada."""

    # Cialdini: 6 principios + tactical implementations
    CIALDINI_FRAMEWORKS = {
        "reciprocity": {
            "principle": "Give first → buyer feels obligated to give back",
            "tactics": [
                "Free mini-audit / analysis (shows value)",
                "Free trial (test drive, no risk)",
                "Free masterclass / education (builds trust)",
                "Free consultation (personalized attention)",
            ],
            "psychology": "Indebtedness creates obligation",
            "power": "high",
        },
        "scarcity": {
            "principle": "Limit creates urgency (loss aversion > gain seeking)",
            "tactics": [
                "Limited inventory (real: 5 units left)",
                "Limited time offer (48h, 72h window)",
                "Exclusive access (only 10 spots/month)",
                "Deadline (early bird discount, enrollment closes Friday)",
            ],
            "psychology": "Fear of missing out > value consideration",
            "power": "very_high",
        },
        "authority": {
            "principle": "Trust experts → follow their lead",
            "tactics": [
                "Credentials displayed (MBA, 20 years experience)",
                "Media mentions (Featured in Forbes, TechCrunch)",
                "Awards (Industry award, customer choice award)",
                "Certifications (ISO, industry-specific cert)",
            ],
            "psychology": "Expertise = trustworthy",
            "power": "high",
        },
        "social_proof": {
            "principle": "Others did it → it's safe to do",
            "tactics": [
                "Customer count (5000+ companies using)",
                "Testimonials (specific results, named person + photo)",
                "Case studies (detailed before/after, numbers)",
                "Ratings & reviews (4.8/5 stars, 2000+ reviews)",
                "User-generated content (customer photos/videos)",
            ],
            "psychology": "Crowds = safety signal",
            "power": "very_high",
        },
        "liking": {
            "principle": "Like person → buy from person",
            "tactics": [
                "Similarity (same background, values, goals)",
                "Compliments (genuine, specific)",
                "Cooperation (work together toward goal)",
                "Attractiveness (professional, polished appearance)",
            ],
            "psychology": "Likable = persuasive",
            "power": "medium",
        },
        "commitment": {
            "principle": "Public promise → follow through",
            "tactics": [
                "Small yes first (commitment escalation)",
                "Written commitment (sign, even small)",
                "Public commitment (tell friends, post social)",
                "Identity commitment (become X type of person)",
            ],
            "psychology": "Consistency bias drives behavior",
            "power": "high",
        },
    }

    # Kahneman: Behavioral economics + decision making
    KAHNEMAN_FRAMEWORKS = {
        "loss_aversion": {
            "principle": "Fear of loss > pleasure of gain (2:1 ratio)",
            "tactics": [
                "Frame as prevention (avoid loss) not gain",
                "Money-back guarantee (removes risk)",
                "Highlight cost of NOT doing (opportunity loss)",
                "Emphasize what they'll lose (scarcity messaging)",
            ],
            "example": "NOT 'Gain 50% productivity' BUT 'Avoid losing $100k/year'",
            "power": "very_high",
        },
        "anchoring": {
            "principle": "First number sticks (reference point)",
            "tactics": [
                "High anchor first ($10k solution, now $5k discount)",
                "Compare to alternative ($500/mo competing solution)",
                "Price comparison ($10/mo = $120/year)",
                "Original price shown (was $999, now $499)",
            ],
            "example": "Original $999, Today $499 = mind anchors to $999",
            "power": "very_high",
        },
        "availability_bias": {
            "principle": "Recent/top-of-mind = true",
            "tactics": [
                "Testimonials first (memorable stories)",
                "Case studies top (specific examples stick)",
                "Recent wins highlighted (just yesterday...)",
                "Social proof current (trending, popular now)",
            ],
            "psychology": "Easy to recall = feels true",
            "power": "high",
        },
        "framing_effect": {
            "principle": "Same thing, different frame = different decision",
            "tactics": [
                "Positive frame: 95% success rate (vs 5% failure)",
                "Loss frame: Don't miss out on X benefit",
                "Gain frame: Achieve X result in X time",
                "Prospect frame: What you could gain",
            ],
            "example": "NOT 'Low risk' BUT 'Protected by 60-day guarantee'",
            "power": "very_high",
        },
        "sunk_cost_fallacy": {
            "principle": "Invested time/money → continue path",
            "tactics": [
                "Build momentum (small commitment first)",
                "Track progress (show invested value)",
                "Highlight effort sunk (time, attention, energy)",
                "Future payoff clear (justify continued investment)",
            ],
            "psychology": "Don't want to waste what invested",
            "power": "medium_high",
        },
    }

    # Language patterns: Milton model + embedded commands
    LANGUAGE_PATTERNS = {
        "presuppositions": {
            "pattern": "Assume outcome, question becomes 'how' not 'if'",
            "examples": [
                "When you achieve X, how will you celebrate?",
                "As you implement this, you'll notice...",
                "After you sign up, you'll gain access to...",
            ],
        },
        "embedded_commands": {
            "pattern": "Hide instruction in sentence",
            "examples": [
                "You might want to IMAGINE what success looks like",
                "I'd like you to CONSIDER how this could help",
                "You could DECIDE right now to move forward",
            ],
        },
        "metaphor": {
            "pattern": "Story/metaphor sticks more than facts",
            "examples": [
                "Building a business is like planting a garden...",
                "Your sales funnel is a river...",
                "Customer journey is like a movie...",
            ],
        },
        "power_words": {
            "high_impact": [
                "Proven", "Guaranteed", "Exclusive", "Limited",
                "Breakthrough", "Revolutionary", "Effortless", "Instantly",
            ],
            "examples": [
                "Proven 3-step system (not just system)",
                "Guaranteed results or money back (not maybe)",
                "Exclusive access (limited availability signal)",
            ],
        },
    }

    # Persuasion stack: layer multiple principles
    @staticmethod
    def build_persuasion_stack(buyer: Dict[str, Any], product: Dict[str, Any]) -> Dict[str, Any]:
        """Construye stack persuasión personalizado."""

        stack = {
            "buyer_profile": buyer,
            "primary_principle": None,
            "secondary_principles": [],
            "language_patterns": [],
            "emotional_triggers": [],
            "objection_reframes": [],
        }

        # Identify primary principle based on buyer type
        buyer_type = buyer.get("type", "rational")

        if buyer_type == "risk_averse":
            stack["primary_principle"] = "loss_aversion"
            stack["secondary_principles"] = ["social_proof", "authority"]
        elif buyer_type == "impulser":
            stack["primary_principle"] = "scarcity"
            stack["secondary_principles"] = ["urgency", "fomo"]
        elif buyer_type == "analytical":
            stack["primary_principle"] = "authority"
            stack["secondary_principles"] = ["data", "proof"]
        else:
            stack["primary_principle"] = "social_proof"
            stack["secondary_principles"] = ["liking", "reciprocity"]

        # Add emotional triggers
        if product.get("price", 0) > 5000:
            stack["emotional_triggers"].append("exclusivity")
        if buyer.get("urgency_level") == "high":
            stack["emotional_triggers"].append("scarcity_time")

        return stack

    @staticmethod
    def generate_persuasive_copy(
        hook: str,
        pain_point: str,
        solution: str,
        social_proof: str,
        cta: str,
    ) -> str:
        """Genera copy persuasivo (5-part structure)."""

        copy = f"""
{hook}

Pain: {pain_point}

Solution: {solution}

Proof: {social_proof}

CTA: {cta}
        """.strip()

        return copy

    @staticmethod
    def objection_reframe(objection: str, principle: str) -> Dict[str, str]:
        """Reframe objeción usando principio persuasión."""

        reframes = {
            "price_too_high": {
                "loss_aversion": "Cost of NOT doing this is higher (opportunity loss)",
                "reciprocity": "You get 10x value back vs investment",
                "authority": "Industry experts pay 2x, we give discount",
            },
            "need_to_think": {
                "scarcity": "Only 2 spots left, decision needed by Friday",
                "commitment": "Just small commitment first, no pressure full commitment",
                "social_proof": "3 similar clients signed up yesterday, don't miss wave",
            },
            "not_sure_it_works": {
                "authority": "Proven by 5000+ companies, 4.8/5 rating",
                "social_proof": "See case study X (identical situation, +300% result)",
                "loss_aversion": "Risk is ours: 90-day money-back guarantee",
            },
        }

        return reframes.get(objection, {}).get(principle, "Reframe not found")
