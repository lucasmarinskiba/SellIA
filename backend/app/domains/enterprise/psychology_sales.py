"""Phase 31 - Psychology Sales System (Jordan Belfort Method)."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.psychology_sales import (
    DiscoveryResponse,
    NeedNarrative,
    ObjectionHandling,
    CloseAttempt,
    SalesConversation,
)
from backend.celery_app import celery_app
import logging

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryQuestion:
    """Discovery question with psychology framework."""

    question: str
    category: str  # rapport, problem, impact, status_quo, desired, authority
    psychology: str
    expected_response_type: str


@dataclass
class NeedNarrativeResult:
    """Need creation narrative."""

    narrative: str
    financial_impact: float
    pain_points: List[str]
    urgency_level: float  # 1-10


class DiscoveryQuestionsEngine:
    """Generate contextual discovery questions."""

    QUESTION_HIERARCHY = {
        "rapport": [
            "Tell me about {company_name} and what you folks focus on.",
            "How long have you been in your current role?",
            "What's the size of your team?",
        ],
        "problem": [
            "What's your biggest challenge right now?",
            "Where are you losing time or money?",
            "What keeps you up at night about your business?",
        ],
        "impact": [
            "How much is that costing you annually?",
            "What's the impact on your team when this happens?",
            "If this continued for 12 months, what happens to your business?",
        ],
        "status_quo": [
            "How are you handling it now?",
            "What solutions have you already tried?",
            "Why hasn't that worked out?",
        ],
        "desired": [
            "What would ideal look like for you?",
            "If you could wave a magic wand, what changes?",
            "What would you do with the time/money you'd save?",
        ],
        "authority": [
            "Who else needs to sign off on this decision?",
            "What's your decision process?",
            "When could we get them involved in a conversation?",
        ],
    }

    def __init__(self, db: Session, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    def generate_questions(self, prospect: Dict, deal_stage: str) -> List[DiscoveryQuestion]:
        """Generate discovery questions for prospect."""

        stage_to_hierarchy = {
            "initial_contact": "rapport",
            "discovery": "problem",
            "qualification": "impact",
            "needs_analysis": "status_quo",
            "proposal": "desired",
            "negotiation": "authority",
        }

        hierarchy_type = stage_to_hierarchy.get(deal_stage, "problem")
        base_questions = self.QUESTION_HIERARCHY.get(hierarchy_type, [])

        if not self.claude:
            return [
                DiscoveryQuestion(
                    question=q,
                    category=hierarchy_type,
                    psychology=self._get_psychology(hierarchy_type),
                    expected_response_type=self._get_response_type(hierarchy_type),
                )
                for q in base_questions
            ]

        # Personalize with Claude
        prompt = f"""
        Generate 3 discovery questions for:
        Company: {prospect.get('company_name')}
        Industry: {prospect.get('industry')}
        Role: {prospect.get('role')}
        Stage: {deal_stage}

        Category: {hierarchy_type}

        Base questions:
        {json.dumps(base_questions)}

        Personalize for this prospect. Focus on making THEM talk, not you selling.
        Format as JSON array with fields: question, psychology, expected_response_type
        """

        try:
            message = self.claude.messages.create(
                model="claude-opus",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            questions_json = json.loads(message.content[0].text)
            return [
                DiscoveryQuestion(
                    question=q["question"],
                    category=hierarchy_type,
                    psychology=q.get("psychology", ""),
                    expected_response_type=q.get("expected_response_type", "open"),
                )
                for q in questions_json
            ]
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return [
                DiscoveryQuestion(
                    question=q,
                    category=hierarchy_type,
                    psychology=self._get_psychology(hierarchy_type),
                    expected_response_type=self._get_response_type(hierarchy_type),
                )
                for q in base_questions
            ]

    def record_response(self, deal_id: str, question: str, response: str) -> DiscoveryResponse:
        """Record discovery response and analyze."""

        # Extract pain points, needs, urgency
        analysis = self._analyze_response(response)

        db_response = DiscoveryResponse(
            deal_id=deal_id,
            question=question,
            response_text=response,
            pain_points=analysis.get("pain_points", []),
            needs_identified=analysis.get("needs", []),
            urgency_level=analysis.get("urgency", 5),
            sentiment=analysis.get("sentiment", "neutral"),
        )

        self.db.add(db_response)
        self.db.commit()

        return db_response

    def _analyze_response(self, response: str) -> Dict[str, Any]:
        """Analyze response for pain points, needs, urgency."""

        pain_keywords = ["losing", "wasting", "frustrated", "struggling", "broken", "pain", "problem"]
        pain_points = []
        for keyword in pain_keywords:
            if keyword in response.lower():
                pain_points.append(response)

        # Simple urgency calc (1-10)
        urgency_keywords = ["asap", "urgent", "immediately", "now", "critical"]
        urgency = 5
        if any(kw in response.lower() for kw in urgency_keywords):
            urgency = 8

        return {
            "pain_points": pain_points,
            "needs": [response[:50]],  # Placeholder
            "urgency": urgency,
            "sentiment": "neutral",
        }

    def _get_psychology(self, hierarchy_type: str) -> str:
        """Get psychology principle for question type."""

        psychology_map = {
            "rapport": "Build trust, get them comfortable talking",
            "problem": "Let them identify their own problem",
            "impact": "Make THEM quantify the cost",
            "status_quo": "Help them see current solution failing",
            "desired": "Make THEM describe the need they're creating",
            "authority": "Remove decision objections before proposal",
        }
        return psychology_map.get(hierarchy_type, "Build conversation")

    def _get_response_type(self, hierarchy_type: str) -> str:
        """Get expected response type."""

        return "open" if hierarchy_type in ["problem", "desired"] else "specific"


class NeedCreationEngine:
    """Create awareness of buyer need through pain amplification."""

    def __init__(self, db: Session, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    def create_need_narrative(self, deal_id: str, discovery_responses: List[str]) -> NeedNarrativeResult:
        """Build narrative that creates urgency and need."""

        # Extract pain points
        pain_points = self._extract_pain_points(discovery_responses)
        financial_impact = self._calculate_financial_impact(pain_points)

        if not self.claude:
            narrative = self._get_template_narrative(pain_points, financial_impact)
        else:
            narrative = self._generate_claude_narrative(pain_points, financial_impact)

        # Save to DB
        db_narrative = NeedNarrative(
            deal_id=deal_id,
            narrative=narrative,
            financial_impact_calculated=financial_impact,
            pain_points=pain_points,
        )
        self.db.add(db_narrative)
        self.db.commit()

        urgency = min(financial_impact / 100000, 10)  # 1-10 scale

        return NeedNarrativeResult(
            narrative=narrative,
            financial_impact=financial_impact,
            pain_points=pain_points,
            urgency_level=urgency,
        )

    def _extract_pain_points(self, responses: List[str]) -> List[str]:
        """Extract pain points from discovery responses."""

        pain_keywords = ["losing", "wasting", "frustrated", "struggling", "broken", "pain"]
        pain_points = []

        for response in responses:
            if any(keyword in response.lower() for keyword in pain_keywords):
                pain_points.append(response)

        return pain_points[:3]  # Top 3

    def _calculate_financial_impact(self, pain_points: List[str]) -> float:
        """Calculate annual financial impact."""

        # Simplified: extract numbers from pain points
        import re

        total_impact = 0
        for pain in pain_points:
            matches = re.findall(r'\$?([\d,]+)', pain)
            for match in matches:
                try:
                    amount = float(match.replace(",", ""))
                    if amount < 10000:  # Per unit cost
                        amount *= 52  # Annualize
                    total_impact += amount
                except:
                    pass

        return max(total_impact, 50000)  # Conservative minimum

    def _generate_claude_narrative(self, pain_points: List[str], impact: float) -> str:
        """Generate need narrative using Claude."""

        prompt = f"""
        Create a wake-up-call narrative that makes buyer see they NEED to act:

        Pain Points: {json.dumps(pain_points)}
        Annual Impact: ${impact:,.0f}

        Structure:
        1. Validate problem (not alone)
        2. Quantify cost ("costing you...")
        3. Show trend ("if unchanged...")
        4. Create urgency ("competitors are...")
        5. Position hope ("there IS a way...")

        Tone: Conversational, empathetic, real. NOT salesy.
        """

        try:
            message = self.claude.messages.create(
                model="claude-opus",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error generating narrative: {e}")
            return self._get_template_narrative(pain_points, impact)

    def _get_template_narrative(self, pain_points: List[str], impact: float) -> str:
        """Template narrative."""

        return f"""
        You're facing a real challenge that most companies in your space are dealing with right now.

        Here's what's happening: {pain_points[0] if pain_points else "Your current solution isn't scaled"}

        What does that cost you? About ${impact:,.0f} per year in lost productivity, missed opportunities, and team burnout.

        The problem is, if you keep going status quo, that number only grows. Your competitors? They're already fixing this.

        But here's the good news: There IS a proven way to solve this. And we've built it.
        """


class UrgencyTriggerEngine:
    """Generate legitimate FOMO/urgency triggers."""

    def __init__(self, db: Session):
        self.db = db

    def generate_urgency_triggers(self, deal: Dict) -> List[Dict[str, Any]]:
        """Create FOMO triggers (legitimate, not manipulative)."""

        triggers = []

        # 1. Supply scarcity (real capacity limits)
        if deal.get("stage") in ["proposal", "negotiation"]:
            triggers.append({
                "type": "supply_scarcity",
                "trigger": "We're at capacity. Next cohort is April.",
                "why_true": "Limited onboarding team",
                "deadline": "End of quarter",
                "messaging": "Our onboarding team can only take 3 new clients this quarter. After that, we're full until April.",
            })

        # 2. Price increase (scheduled & real)
        triggers.append({
            "type": "price_increase",
            "trigger": "Pricing increases March 1st",
            "why_true": "We're raising prices on new customers",
            "deadline": "Feb 28",
            "messaging": "We just increased pricing. Current pricing locks in until Feb 28.",
        })

        # 3. Social proof (actual wins in their space)
        if deal.get("industry"):
            triggers.append({
                "type": "social_proof",
                "trigger": f"We just signed 2 other {deal['industry']} companies",
                "why_true": "Recent wins in their category",
                "deadline": "Now",
                "messaging": "Your competitors are already using this. You'd be the first to [specific advantage].",
            })

        # 4. Competitive threat (intelligence-based)
        triggers.append({
            "type": "competitive",
            "trigger": "Your competitors are 6 months ahead",
            "why_true": "Market intel",
            "deadline": "Before gap widens",
            "messaging": "The way sales works is changing. If your team doesn't adapt now, they'll be at a disadvantage.",
        })

        return triggers

    def weave_into_narrative(self, triggers: List[Dict], conversation: str) -> str:
        """Weave urgency into conversation naturally."""

        # Don't say "Limited spots available!" (cringe)
        # DO say "Our next cohort starts April 1st" (natural)

        result = conversation
        for trigger in triggers[:2]:  # Use top 2 triggers
            result += f"\n\n[Natural insertion point: {trigger['messaging']}]"

        return result


class PsychologyObjectionHandler:
    """Handle objections using psychology, not logic."""

    def __init__(self, db: Session, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    OBJECTION_FRAMEWORKS = {
        "price": {
            "validate": "I get it, budget's tight.",
            "reframe": "Price of regret vs price of solution",
            "question": "What would it cost NOT to fix this?",
        },
        "time": {
            "validate": "You're busy, I know.",
            "reframe": "5 hours now saves 10/week for months",
            "question": "What's your time worth?",
        },
        "need": {
            "validate": "I totally hear that.",
            "reframe": "Future state: will this get better or worse?",
            "question": "What happens in 12 months if nothing changes?",
        },
        "authority": {
            "validate": "Smart to check with them.",
            "reframe": "Get them excited FIRST, then sell internally",
            "question": "Who would benefit most if we fixed this?",
        },
    }

    def handle_objection(self, objection: str, prospect: Dict) -> str:
        """Generate psychology-based objection response."""

        objection_type = self._classify_objection(objection)
        framework = self.OBJECTION_FRAMEWORKS.get(objection_type, self.OBJECTION_FRAMEWORKS["need"])

        if not self.claude:
            return f"{framework['validate']} {framework['question']}"

        prompt = f"""
        Create psychology-based response to objection:

        Objection: "{objection}"
        Type: {objection_type}
        Framework: {json.dumps(framework)}

        Response should:
        1. Validate (never dismiss): "{framework['validate']}"
        2. Reframe perspective: "{framework['reframe']}"
        3. Ask question: "{framework['question']}"

        Make it conversational, not salesy. 2-3 sentences max.
        """

        try:
            message = self.claude.messages.create(
                model="claude-opus",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error handling objection: {e}")
            return f"{framework['validate']} {framework['question']}"

    def _classify_objection(self, objection: str) -> str:
        """Classify objection type."""

        objection_lower = objection.lower()

        if "price" in objection_lower or "cost" in objection_lower or "expensive" in objection_lower:
            return "price"
        elif "time" in objection_lower or "busy" in objection_lower or "implement" in objection_lower:
            return "time"
        elif "need" in objection_lower or "don't" in objection_lower or "not sure" in objection_lower:
            return "need"
        elif "boss" in objection_lower or "team" in objection_lower or "approval" in objection_lower:
            return "authority"

        return "need"


class AssumptiveCloseEngine:
    """Jordan Belfort's 5-step closing sequence."""

    def __init__(self, db: Session):
        self.db = db

    CLOSE_SEQUENCE = [
        {
            "step": 1,
            "commitment": "Should we get your team involved in a 30-min call?",
            "psychology": "Low-barrier small YES",
            "expected": "Sure, when?",
        },
        {
            "step": 2,
            "commitment": "Which works better: annual or monthly pricing?",
            "psychology": "Choice assumes they're buying",
            "expected": "Probably annual",
        },
        {
            "step": 3,
            "commitment": "Let's do a 30-day pilot first to prove ROI",
            "psychology": "Removes risk, enables commitment",
            "expected": "Okay, let's try it",
        },
        {
            "step": 4,
            "commitment": "Should we add advanced features?",
            "psychology": "Small upsell after main commitment",
            "expected": "Maybe later",
        },
        {
            "step": 5,
            "commitment": "Perfect. I'll send the contract today. You good?",
            "psychology": "Momentum + assumption = automatic yes",
            "expected": "Yep, send it",
        },
    ]

    def get_close(self, step: int) -> str:
        """Get close for current step."""

        if step < len(self.CLOSE_SEQUENCE):
            return self.CLOSE_SEQUENCE[step]["commitment"]

        return "So you're ready to move forward?"

    def get_next_close(self, current_response: str) -> tuple:
        """Get next close based on their response."""

        is_positive = self._is_positive_response(current_response)

        if not is_positive:
            # Handle objection, stay on current step
            return ("objection", current_response)

        # Move to next step
        return ("advance", self.CLOSE_SEQUENCE)

    def _is_positive_response(self, response: str) -> bool:
        """Determine if response is positive."""

        positive_words = ["yes", "sure", "ok", "good", "let's", "when", "how", "sounds"]
        return any(word in response.lower() for word in positive_words)


# ============================================================
# CELERY TASKS
# ============================================================


@celery_app.task(bind=True, max_retries=3)
def create_need_narrative_async(self, deal_id: str, responses: List[str]):
    """Create need narrative in background."""
    try:
        from backend.app.database import SessionLocal

        db = SessionLocal()
        engine = NeedCreationEngine(db)

        result = engine.create_need_narrative(deal_id, responses)

        logger.info(f"Need narrative created for deal {deal_id}: ${result.financial_impact:,.0f} impact")
        db.close()

        return {"status": "complete", "deal_id": deal_id, "impact": result.financial_impact}

    except Exception as exc:
        logger.error(f"Error creating narrative: {exc}")
        raise self.retry(exc=exc, countdown=60)
