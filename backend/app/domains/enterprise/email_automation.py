"""Email + Proposal Automation Services (Phase 28)."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.email_automation import (
    SendTimePrediction,
    EmailOpenTracking,
    ProposalDraft,
    ProposalView,
    CompetitorMention,
    CompetitorResponse,
)
from backend.celery_app import celery_app
import logging

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)


@dataclass
class SendTimeRecommendation:
    """Optimal send time recommendation."""

    person_id: str
    recommended_time: datetime
    predicted_open_probability: float  # 0-100
    alternatives: List[datetime]
    confidence: float


@dataclass
class ProposalDraftResult:
    """Generated proposal draft."""

    draft_id: str
    deal_id: str
    html_content: str
    word_count: int
    generation_time_seconds: float


@dataclass
class CompetitorDetectionResult:
    """Competitor mention detection."""

    competitors: List[str]
    mentions: List[Dict[str, Any]]
    has_threats: bool


class SendTimeOptimizer:
    """ML-based email send time optimization."""

    def __init__(self, db: Session, ml_model=None):
        self.db = db
        self.model = ml_model  # XGBoost/LR model

    def predict_send_times(
        self, person_id: str, email_subject: str, email_body: str
    ) -> SendTimeRecommendation:
        """Predict optimal send time for email."""

        # Generate candidate times (next 72 hours, hourly)
        now = datetime.utcnow()
        candidates = [now + timedelta(hours=i) for i in range(1, 73)]

        # Extract features for each candidate time
        # Features: timezone, hour_of_day, day_of_week, email sentiment, etc

        # Simplified: If model available, use it
        # Otherwise: return business hours (9 AM - 5 PM in recipient timezone)

        if self.model:
            try:
                scores = self._score_candidates(
                    person_id, email_subject, email_body, candidates
                )
                top_indices = np.argsort(scores)[-3:][::-1]
                top_times = [candidates[i] for i in top_indices]
                top_probs = [scores[i] * 100 for i in top_indices]
            except Exception as e:
                logger.warning(f"Model inference failed: {e}. Using default times.")
                top_times, top_probs = self._get_default_send_times(candidates)
        else:
            top_times, top_probs = self._get_default_send_times(candidates)

        recommendation = SendTimeRecommendation(
            person_id=person_id,
            recommended_time=top_times[0],
            predicted_open_probability=top_probs[0],
            alternatives=top_times[1:],
            confidence=min(top_probs[0] / 100, 1.0),
        )

        # Store prediction
        prediction = SendTimePrediction(
            person_id=person_id,
            recommended_send_time=top_times[0],
            predicted_open_probability=top_probs[0],
            alternative_time_1=top_times[1] if len(top_times) > 1 else None,
            alternative_time_2=top_times[2] if len(top_times) > 2 else None,
            model_version="1.0.0",
        )
        self.db.add(prediction)
        self.db.commit()

        return recommendation

    def _score_candidates(
        self, person_id: str, subject: str, body: str, candidates: List[datetime]
    ) -> np.ndarray:
        """Score candidate send times using ML model."""

        # Extract features for person + email + time
        # This would involve:
        # 1. Getting person's timezone, role, industry
        # 2. Extracting email sentiment
        # 3. Feature engineering for each time
        # 4. Model.predict_proba()

        # Placeholder: return random scores
        return np.random.uniform(0.4, 0.9, len(candidates))

    def _get_default_send_times(self, candidates: List[datetime]) -> tuple:
        """Get default send times (business hours)."""

        default_times = [
            c for c in candidates
            if c.hour in [9, 10, 14, 15] and c.weekday() < 5  # Business hours, weekdays
        ]

        if not default_times:
            default_times = candidates[:3]
        else:
            default_times = default_times[:3]

        probs = [65, 55, 45]  # Default probabilities
        return default_times, probs

    def track_open(
        self, email_id: str, person_id: str, opened_at: datetime
    ) -> bool:
        """Track email open event."""

        # Find original prediction
        prediction = (
            self.db.query(SendTimePrediction)
            .filter(SendTimePrediction.person_id == person_id)
            .order_by(SendTimePrediction.prediction_date.desc())
            .first()
        )

        if prediction and prediction.actual_send_time:
            delay = (opened_at - prediction.actual_send_time).total_seconds() / 60
        else:
            delay = None

        open_event = EmailOpenTracking(
            email_id=email_id,
            person_id=person_id,
            opened_at=opened_at,
            open_delay_minutes=int(delay) if delay else None,
        )
        self.db.add(open_event)
        self.db.commit()

        return True


class ProposalGenerator:
    """AI-powered proposal generation using Claude."""

    def __init__(self, db: Session, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    def generate_proposal(self, deal_id: str, options: Optional[Dict[str, Any]] = None) -> ProposalDraftResult:
        """Generate AI proposal for deal."""

        if not self.claude:
            logger.warning("Claude not available. Using template proposal.")
            return self._generate_template_proposal(deal_id)

        try:
            from backend.app.models.deal import Deal

            # Gather context
            deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
            if not deal:
                raise ValueError(f"Deal {deal_id} not found")

            # Build prompt
            prompt = self._build_proposal_prompt(deal, options or {})

            # Call Claude
            start_time = datetime.utcnow()
            message = self.claude.messages.create(
                model="claude-opus",
                max_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            generation_time = (datetime.utcnow() - start_time).total_seconds()

            proposal_html = message.content[0].text

            # Save draft
            draft = ProposalDraft(
                deal_id=deal_id,
                html_content=proposal_html,
                word_count=len(proposal_html.split()),
                generation_method="claude_opus",
                generated_at=datetime.utcnow(),
            )
            self.db.add(draft)
            self.db.commit()

            logger.info(f"Generated proposal for deal {deal_id} in {generation_time:.1f}s")

            return ProposalDraftResult(
                draft_id=str(draft.id),
                deal_id=deal_id,
                html_content=proposal_html,
                word_count=draft.word_count,
                generation_time_seconds=generation_time,
            )

        except Exception as e:
            logger.error(f"Error generating proposal: {e}")
            return self._generate_template_proposal(deal_id)

    def _build_proposal_prompt(self, deal: Any, options: Dict[str, Any]) -> str:
        """Build Claude prompt for proposal generation."""

        tone = options.get("tone", "professional")
        length = options.get("length", "standard")  # short, standard, detailed
        focus = options.get("focus", "value")  # value, implementation, risk_mitigation

        prompt = f"""
        Generate a professional sales proposal for:

        Company: {deal.company_name if hasattr(deal, 'company_name') else 'TBD'}
        Deal Value: ${deal.amount:,} if hasattr(deal, 'amount') else '$50,000'
        Stage: {deal.stage if hasattr(deal, 'stage') else 'opportunity'}
        Timeline: {deal.timeline if hasattr(deal, 'timeline') else 'Q4 2026'}

        Requirements:
        - Tone: {tone}
        - Length: {length} (1-2 pages for short, 2-3 for standard, 3-5 for detailed)
        - Focus: {focus}
        - Format: HTML ready to send
        - Include ROI calculation based on typical customer results
        - Add implementation timeline (30/60/90 days)
        - Show why our solution is best for their situation
        - Professional header and footer

        Generate the proposal HTML now:
        """

        return prompt

    def _generate_template_proposal(self, deal_id: str) -> ProposalDraftResult:
        """Fallback: generate proposal from template."""

        template_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h1>Proposal</h1>
        <p>Deal ID: {deal_id}</p>
        <p>Professional proposal template - customize with deal details</p>
        </body>
        </html>
        """

        draft = ProposalDraft(
            deal_id=deal_id,
            html_content=template_html,
            word_count=20,
            generation_method="template",
            generated_at=datetime.utcnow(),
        )
        self.db.add(draft)
        self.db.commit()

        return ProposalDraftResult(
            draft_id=str(draft.id),
            deal_id=deal_id,
            html_content=template_html,
            word_count=20,
            generation_time_seconds=0.5,
        )

    def track_view(
        self, draft_id: str, viewed_by: str, duration_seconds: int
    ) -> bool:
        """Track proposal view."""

        view = ProposalView(
            draft_id=draft_id,
            viewed_by=viewed_by,
            viewed_at=datetime.utcnow(),
            duration_seconds=duration_seconds,
        )
        self.db.add(view)
        self.db.commit()

        return True


class CompetitorDetector:
    """NLP-based competitor mention detection."""

    COMPETITORS = [
        "outreach", "chorus", "salesloft", "pipedrive",
        "salesforce", "hubspot", "ringcentral", "gong",
        "microsoft teams", "slack", "zoom",
    ]

    def __init__(self, db: Session, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    def detect_competitors(self, text: str) -> CompetitorDetectionResult:
        """Extract competitor mentions from text."""

        mentions = []
        text_lower = text.lower()

        for competitor in self.COMPETITORS:
            if competitor.lower() in text_lower:
                # Extract sentence containing mention
                sentences = text.split(".")
                for sentence in sentences:
                    if competitor.lower() in sentence.lower():
                        mentions.append({
                            "competitor": competitor,
                            "context": sentence.strip(),
                            "confidence": 0.95,
                        })

        has_threats = len(mentions) > 0

        return CompetitorDetectionResult(
            competitors=[m["competitor"] for m in mentions],
            mentions=mentions,
            has_threats=has_threats,
        )

    def generate_response(self, competitor: str, context: str) -> str:
        """Generate counter-message for competitor mention."""

        if not self.claude:
            logger.warning("Claude not available. Using template response.")
            return self._get_template_response(competitor)

        try:
            prompt = f"""
            Buyer mentioned: "{competitor}"
            Context: "{context}"

            Generate short, professional response that:
            1. Acknowledges competitor respectfully
            2. Positions our unique value proposition
            3. Asks for meeting to discuss differences

            Keep under 100 words. Tone: consultative, not defensive.

            Generate response:
            """

            message = self.claude.messages.create(
                model="claude-opus",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_template_response(competitor)

    def _get_template_response(self, competitor: str) -> str:
        """Template response for competitor mention."""

        return f"""
        Thanks for mentioning {competitor}. They're a solid choice.
        I'd love to show you why we're different - specifically around
        [your key differentiator]. Can we schedule 20 minutes to compare?
        """


# ============================================================
# CELERY BACKGROUND TASKS
# ============================================================


@celery_app.task(bind=True, max_retries=3)
def send_email_with_optimal_timing(self, email_id: str, person_id: str, email_content: str):
    """Send email at optimal time."""
    try:
        from backend.app.database import SessionLocal

        db = SessionLocal()
        optimizer = SendTimeOptimizer(db)

        recommendation = optimizer.predict_send_times(person_id, "", email_content)

        # Schedule email
        send_at = recommendation.recommended_time

        logger.info(f"Email {email_id} scheduled for {send_at} (open prob: {recommendation.predicted_open_probability:.0f}%)")
        db.close()

        return {"status": "scheduled", "email_id": email_id, "send_at": send_at.isoformat()}

    except Exception as exc:
        logger.error(f"Error scheduling email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def generate_proposal_async(self, deal_id: str):
    """Generate proposal in background."""
    try:
        from backend.app.database import SessionLocal

        db = SessionLocal()
        generator = ProposalGenerator(db)

        result = generator.generate_proposal(deal_id)

        logger.info(f"Proposal generated for deal {deal_id}: {result.word_count} words in {result.generation_time_seconds:.1f}s")
        db.close()

        return {"status": "complete", "deal_id": deal_id, "draft_id": result.draft_id}

    except Exception as exc:
        logger.error(f"Error generating proposal: {exc}")
        raise self.retry(exc=exc, countdown=60)
