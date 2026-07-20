"""
Phase 10: Humanization — Personalization (400L)

Personalizes messages with:
- Buyer name usage (natural, not excessive)
- Purchase history context
- Preferences and behavior patterns
- Urgency level detection
- Company/industry context
- Timing personalization
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class PersonalizationLevel(str, Enum):
    """Level of personalization"""
    MINIMAL = "minimal"  # No personalization
    LIGHT = "light"  # Name only
    MODERATE = "moderate"  # Name + one reference
    DEEP = "deep"  # Name + history + preferences


@dataclass
class BuyerProfile:
    """Buyer information for personalization"""
    buyer_id: str
    name: str
    first_name: str
    company: Optional[str] = None
    industry: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None

    # Behavior data
    past_purchases: List[Dict[str, Any]] = field(default_factory=list)
    engagement_history: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)

    # Interaction timing
    last_contact: Optional[datetime] = None
    best_contact_time: Optional[str] = None  # "morning", "afternoon", "evening"
    timezone: Optional[str] = None

    # Urgency signals
    urgency_level: int = 5  # 1-10, detected from behavior
    is_vip: bool = False
    churn_risk: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PersonalizationContext:
    """Context for personalizing a message"""
    buyer_profile: BuyerProfile
    message_type: str  # "initial", "follow_up", "objection_response", "closing"
    previous_messages: List[str] = field(default_factory=list)
    industry_context: Optional[str] = None
    campaign_name: Optional[str] = None
    personalization_level: PersonalizationLevel = PersonalizationLevel.MODERATE


class PersonalizationEngine:
    """Personalizes messages based on buyer data"""

    # Name usage guidelines (don't overuse)
    NAME_USAGE_RULES = {
        "initial": 1,  # Use name 1x in opening
        "follow_up": 0,  # Don't overuse in follow-ups
        "objection_response": 0,  # Focus on response
        "closing": 1,  # Use name in closing
    }

    # Industry-specific language
    INDUSTRY_VOCABULARY = {
        "real_estate": {
            "keywords": ["property", "investment", "location", "market value", "inspection"],
            "pain_points": ["neighborhood quality", "resale value", "financing"],
            "benefits": ["appreciation", "investment return", "lifestyle"],
        },
        "saas": {
            "keywords": ["scalable", "integration", "analytics", "automation", "api"],
            "pain_points": ["adoption", "onboarding", "vendor lock-in"],
            "benefits": ["efficiency", "insight", "growth"],
        },
        "ecommerce": {
            "keywords": ["conversion", "cart", "checkout", "retention", "ltv"],
            "pain_points": ["abandonment rate", "shipping costs", "competition"],
            "benefits": ["sales velocity", "customer lifetime value"],
        },
        "services": {
            "keywords": ["expertise", "consultation", "ROI", "results", "benchmark"],
            "pain_points": ["quality inconsistency", "scaling", "talent"],
            "benefits": ["reliability", "growth", "peace of mind"],
        },
    }

    # Timing-based personalization
    TIMING_TEMPLATES = {
        "morning": {
            "en": "Hope your day is off to a great start!",
            "es": "¡Espero que tu día comience muy bien!",
        },
        "afternoon": {
            "en": "Quick thought for your afternoon...",
            "es": "Un pensamiento rápido para tu tarde...",
        },
        "evening": {
            "en": "When you get a chance this evening...",
            "es": "Cuando tengas un momento esta noche...",
        },
    }

    def __init__(self):
        """Initialize personalization engine"""
        logger.info("PersonalizationEngine initialized")

    def create_buyer_profile(
        self,
        buyer_id: str,
        name: str,
        **kwargs
    ) -> BuyerProfile:
        """
        Create or update buyer profile.

        Args:
            buyer_id: Unique buyer identifier
            name: Full name
            **kwargs: Additional profile data (company, role, etc.)

        Returns:
            BuyerProfile
        """
        first_name = name.split()[0] if name else "there"

        profile = BuyerProfile(
            buyer_id=buyer_id,
            name=name,
            first_name=first_name,
            company=kwargs.get("company"),
            industry=kwargs.get("industry"),
            role=kwargs.get("role"),
            location=kwargs.get("location"),
            timezone=kwargs.get("timezone", "UTC"),
            best_contact_time=kwargs.get("best_contact_time", "afternoon"),
            is_vip=kwargs.get("is_vip", False),
        )

        return profile

    def infer_industry(
        self,
        company_name: Optional[str] = None,
        context_clues: Optional[str] = None,
    ) -> Optional[str]:
        """
        Infer buyer industry from company name or context.

        Returns:
            Detected industry or None
        """
        if not company_name and not context_clues:
            return None

        text = f"{company_name or ''} {context_clues or ''}".lower()

        # Real estate indicators
        if any(word in text for word in ["realty", "property", "real estate", "inmobiliario", "propiedad"]):
            return "real_estate"

        # SaaS indicators
        if any(word in text for word in ["software", "saas", "platform", "solution", "app"]):
            return "saas"

        # E-commerce indicators
        if any(word in text for word in ["shop", "store", "ecommerce", "tienda", "ecommerce"]):
            return "ecommerce"

        # Services indicators
        if any(word in text for word in ["consulting", "agency", "services", "consultoría", "asesoría"]):
            return "services"

        return None

    def personalize_message(
        self,
        message: str,
        buyer_profile: BuyerProfile,
        context: PersonalizationContext,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Personalize message for buyer.

        Args:
            message: Base message template
            buyer_profile: Buyer information
            context: Personalization context
            language: Language code

        Returns:
            {
                "personalized_message": str,
                "personalization_elements": [list],
                "confidence": float,
            }
        """
        personalized = message
        elements_added = []

        # Determine personalization level
        level = context.personalization_level

        if level in [PersonalizationLevel.LIGHT, PersonalizationLevel.MODERATE, PersonalizationLevel.DEEP]:
            # Add name greeting (respects usage rules)
            name_uses = self.NAME_USAGE_RULES.get(context.message_type, 0)
            if name_uses > 0 and buyer_profile.first_name:
                # Insert name naturally at start if not already there
                if not personalized.startswith(buyer_profile.first_name):
                    if language == "es":
                        personalized = f"{buyer_profile.first_name}, {personalized}"
                    else:
                        personalized = f"{buyer_profile.first_name}, {personalized}"
                    elements_added.append(f"name_greeting:{buyer_profile.first_name}")

        if level in [PersonalizationLevel.MODERATE, PersonalizationLevel.DEEP]:
            # Add industry-specific language
            if buyer_profile.industry:
                industry_vocab = self.INDUSTRY_VOCABULARY.get(buyer_profile.industry, {})
                if industry_vocab:
                    # Try to weave in 1-2 industry keywords
                    for keyword in industry_vocab.get("keywords", [])[:2]:
                        if keyword not in personalized.lower():
                            # Find good place to add it
                            if "your" in personalized:
                                personalized = personalized.replace(
                                    "your",
                                    f"your {keyword}",
                                    1
                                )
                                elements_added.append(f"industry_keyword:{keyword}")
                                break

            # Add company reference
            if buyer_profile.company and "your company" in personalized:
                personalized = personalized.replace(
                    "your company",
                    buyer_profile.company
                )
                elements_added.append(f"company:{buyer_profile.company}")

            # Add role reference
            if buyer_profile.role and buyer_profile.role.lower() not in personalized.lower():
                if "your role" in personalized or "your position" in personalized:
                    personalized = personalized.replace(
                        "your role",
                        f"your {buyer_profile.role.lower()} role"
                    )
                    elements_added.append(f"role:{buyer_profile.role}")

            # Add purchase history reference
            if buyer_profile.past_purchases:
                last_purchase = buyer_profile.past_purchases[-1]
                if "previously" not in personalized and language == "en":
                    insert_text = f" I saw you {last_purchase.get('product', 'something great')} previously — "
                    personalized = insert_text + personalized
                    elements_added.append(f"purchase_history:{last_purchase.get('product', 'item')}")

        if level == PersonalizationLevel.DEEP:
            # Add timing personalization
            if buyer_profile.best_contact_time:
                timing_msg = self.TIMING_TEMPLATES.get(
                    buyer_profile.best_contact_time,
                    {}
                ).get(language, "")
                if timing_msg:
                    personalized = f"{timing_msg} {personalized}"
                    elements_added.append(f"timing:{buyer_profile.best_contact_time}")

            # Add urgency signal
            if buyer_profile.urgency_level >= 7:
                if language == "es":
                    urgency_indicator = "por tu situación particular, esto puede ser relevante ahora: "
                else:
                    urgency_indicator = "given your situation, this might be particularly relevant right now: "
                personalized = f"{urgency_indicator}{personalized}"
                elements_added.append("urgency_signal:high")

        return {
            "personalized_message": personalized,
            "personalization_elements": elements_added,
            "personalization_level": level.value,
            "confidence": self._calculate_personalization_confidence(elements_added),
        }

    def detect_urgency_from_profile(
        self,
        buyer_profile: BuyerProfile,
    ) -> int:
        """
        Detect buyer urgency level (1-10) from profile data.

        Factors:
        - Recent website activity
        - Engagement frequency
        - Churn risk
        - VIP status

        Returns:
            Urgency level 1-10
        """
        urgency = 5  # Default

        # High urgency if churn risk
        if buyer_profile.churn_risk:
            urgency = 8

        # High urgency if VIP
        if buyer_profile.is_vip:
            urgency = 7

        # Check recency of last contact
        if buyer_profile.last_contact:
            days_since = (datetime.utcnow() - buyer_profile.last_contact).days
            if days_since > 14:
                urgency += 2
            elif days_since < 7:
                urgency -= 1

        # Check engagement history
        if buyer_profile.engagement_history:
            recent_engagement = len([
                e for e in buyer_profile.engagement_history
                if "week" in str(e).lower()
            ])
            if recent_engagement > 3:
                urgency += 1

        return min(max(urgency, 1), 10)

    def generate_follow_up_context(
        self,
        buyer_profile: BuyerProfile,
        days_since_contact: int,
    ) -> Dict[str, Any]:
        """
        Generate appropriate follow-up context based on timing.

        Args:
            buyer_profile: Buyer info
            days_since_contact: Days since last contact

        Returns:
            Follow-up guidance
        """
        if days_since_contact < 2:
            followup_type = "quick_nudge"
            description = "Quick follow-up to keep momentum"
        elif days_since_contact < 7:
            followup_type = "check_in"
            description = "Casual check-in, add new value"
        elif days_since_contact < 14:
            followup_type = "reengagement"
            description = "Re-engage with fresh perspective"
        else:
            followup_type = "win_back"
            description = "Win-back attempt, add strong incentive"

        return {
            "followup_type": followup_type,
            "description": description,
            "days_since": days_since_contact,
            "emphasis_urgency": days_since_contact > 7,
            "recommend_incentive": days_since_contact > 14,
        }

    def extract_buyer_preferences(
        self,
        buyer_profile: BuyerProfile,
    ) -> Dict[str, Any]:
        """
        Extract buyer preferences for personalization.

        From: past interactions, email opens, link clicks, etc.

        Returns:
            {
                "content_type": "short/medium/long",
                "format": "email/message/call",
                "tone": "formal/casual",
                "length": int,
            }
        """
        preferences = {}

        # Infer content preferences from engagement
        if buyer_profile.engagement_history:
            short_engagement = len([e for e in buyer_profile.engagement_history if "short" in str(e).lower()])
            long_engagement = len([e for e in buyer_profile.engagement_history if "long" in str(e).lower()])

            if short_engagement > long_engagement:
                preferences["content_type"] = "short"
                preferences["max_length"] = 50  # words
            elif long_engagement > short_engagement:
                preferences["content_type"] = "long"
                preferences["max_length"] = 200
            else:
                preferences["content_type"] = "medium"
                preferences["max_length"] = 100

        # Role-based tone preference
        if buyer_profile.role:
            if "executive" in buyer_profile.role.lower() or "director" in buyer_profile.role.lower():
                preferences["tone"] = "professional"
            elif "manager" in buyer_profile.role.lower():
                preferences["tone"] = "balanced"
            else:
                preferences["tone"] = "friendly"

        # Industry-based format
        if buyer_profile.industry == "saas":
            preferences["format"] = "email"  # Saas buyers prefer email
        elif buyer_profile.industry == "ecommerce":
            preferences["format"] = "message"  # Ecommerce prefers messaging

        return preferences

    def _calculate_personalization_confidence(
        self,
        elements: List[str],
    ) -> float:
        """Calculate confidence in personalization quality"""
        if not elements:
            return 0.5

        # More elements = higher confidence
        base = min(len(elements) * 0.1, 0.9)

        # Boost for certain element types
        high_value_elements = [
            e for e in elements
            if any(x in e for x in ["name_greeting", "company", "purchase_history"])
        ]
        if high_value_elements:
            base += 0.1

        return min(base, 1.0)

    def should_personalize(
        self,
        buyer_profile: BuyerProfile,
        message_type: str,
    ) -> bool:
        """
        Determine if message should be personalized.

        Always personalize for:
        - VIP buyers
        - Returning customers
        - Objection responses
        - Closing messages
        """
        if buyer_profile.is_vip:
            return True

        if buyer_profile.past_purchases:
            return True

        if message_type in ["objection_response", "closing"]:
            return True

        return False

    def create_dynamic_reference(
        self,
        buyer_profile: BuyerProfile,
        reference_type: str,  # "product", "company", "role", "industry"
    ) -> Optional[str]:
        """
        Create dynamic reference to buyer's specific context.

        Examples:
        - "I know you're in real estate..."
        - "Given your role as Director..."
        - "Since you're at [Company]..."
        """
        if reference_type == "industry" and buyer_profile.industry:
            return f"in the {buyer_profile.industry.replace('_', ' ')} space"

        elif reference_type == "role" and buyer_profile.role:
            return f"as a {buyer_profile.role}"

        elif reference_type == "company" and buyer_profile.company:
            return f"at {buyer_profile.company}"

        elif reference_type == "purchase" and buyer_profile.past_purchases:
            recent_product = buyer_profile.past_purchases[-1].get("product", "our product")
            return f"after your recent purchase of {recent_product}"

        return None
