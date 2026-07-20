"""Lead Scoring Engine

Automatically calculates lead scores based on conversation activity,
behavior, intent signals, and recency.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.crm.models import LeadScore, LeadActivity
from app.domains.channels.models import Conversation, Message
from app.domains.crm.models import LeadStage
from app.domains.subscriptions.models import UserAPIKey
from app.core.encryption import decrypt_value


# Score rules
SCORE_RULES = {
    # Engagement
    "message_received": 5,
    "message_sent": 3,
    "response_within_5min": 10,
    "response_within_1h": 5,
    "multiple_messages_same_day": 10,
    # Intent
    "price_inquiry": 25,
    "availability_inquiry": 20,
    "appointment_request": 30,
    "demo_request": 35,
    "product_inquiry": 20,
    "complaint": -10,  # Negative signal
    # Demographic
    "provided_email": 15,
    "provided_phone": 20,
    "provided_address": 15,
    # Behavioral
    "revisited_conversation": 10,
    "clicked_link": 15,
    "viewed_catalog": 15,
    "added_to_cart": 25,
    # Recency
    "activity_today": 15,
    "activity_this_week": 10,
    "activity_this_month": 5,
    "inactive_7days": -10,
    "inactive_30days": -20,
}

# Classification thresholds
CLASSIFICATION_THRESHOLDS = {
    "hot": 70,
    "warm": 40,
    "cold": 0,
}


class LeadScoringEngine:
    """Engine that recalculates lead scores based on activity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_score(self, conversation_id: uuid.UUID, business_id: uuid.UUID) -> LeadScore:
        """Calculate or recalculate lead score for a conversation."""
        # Get or create lead score record
        result = await self.db.execute(
            select(LeadScore).where(LeadScore.conversation_id == conversation_id)
        )
        lead_score = result.scalar_one_or_none()
        if not lead_score:
            lead_score = LeadScore(
                business_id=business_id,
                conversation_id=conversation_id,
                total_score=0,
            )
            self.db.add(lead_score)
            await self.db.flush()

        # Guardar estado previo para detectar cambios
        previous_classification = lead_score.classification
        previous_total_score = lead_score.total_score

        # Reset component scores
        lead_score.engagement_score = 0
        lead_score.intent_score = 0
        lead_score.demographic_score = 0
        lead_score.behavioral_score = 0
        lead_score.recency_score = 0

        # Get conversation and messages
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return lead_score

        # Get all messages
        result = await self.db.execute(
            select(Message).where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()

        # Calculate engagement score
        lead_score.engagement_score = await self._calc_engagement(messages, conversation)

        # Calculate intent score
        lead_score.intent_score = await self._calc_intent(messages, conversation)

        # Calculate demographic score
        lead_score.demographic_score = await self._calc_demographic(conversation)

        # Calculate behavioral score
        lead_score.behavioral_score = await self._calc_behavioral(conversation)

        # Calculate recency score
        lead_score.recency_score = await self._calc_recency(messages, conversation)

        # Total
        lead_score.total_score = max(0, min(100,
            lead_score.engagement_score +
            lead_score.intent_score +
            lead_score.demographic_score +
            lead_score.behavioral_score +
            lead_score.recency_score
        ))

        # Classification
        if lead_score.total_score >= CLASSIFICATION_THRESHOLDS["hot"]:
            lead_score.classification = "hot"
        elif lead_score.total_score >= CLASSIFICATION_THRESHOLDS["warm"]:
            lead_score.classification = "warm"
        else:
            lead_score.classification = "cold"

        lead_score.last_calculated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(lead_score)

        # Update conversation
        if not conversation.extra_data:
            conversation.extra_data = {}
        conversation.extra_data["lead_score"] = lead_score.total_score
        await self.db.commit()

        # Generate expert commentary if classification changed
        if previous_classification != lead_score.classification:
            commentary = await self._generate_commentary(
                conversation=conversation,
                business_id=business_id,
                previous_classification=previous_classification,
                new_classification=lead_score.classification,
                previous_score=previous_total_score,
                new_score=lead_score.total_score,
                engagement=lead_score.engagement_score,
                intent=lead_score.intent_score,
                demographic=lead_score.demographic_score,
                behavioral=lead_score.behavioral_score,
                recency=lead_score.recency_score,
            )
            if commentary:
                lead_score.commentary = commentary
                await self.db.commit()

            try:
                from app.core.events import emit_lead_score_changed
                await emit_lead_score_changed(
                    business_id=str(business_id),
                    conversation_id=str(conversation_id),
                    old_score=previous_total_score,
                    new_score=lead_score.total_score,
                    old_classification=previous_classification,
                    new_classification=lead_score.classification,
                )
            except Exception as e:
                from app.core.logger import get_logger
                get_logger(__name__).error(f"Event emit error: {e}")

        return lead_score

    async def _calc_engagement(self, messages, conversation) -> int:
        score = 0
        if not messages:
            return score

        # Messages count
        inbound_count = sum(1 for m in messages if m.direction.value == "inbound")
        outbound_count = sum(1 for m in messages if m.direction.value == "outbound")

        score += min(inbound_count * SCORE_RULES["message_received"], 40)
        score += min(outbound_count * SCORE_RULES["message_sent"], 20)

        # Response time analysis
        for i in range(1, len(messages)):
            prev = messages[i - 1]
            curr = messages[i]
            if prev.direction.value == "inbound" and curr.direction.value == "outbound":
                delta = (curr.created_at - prev.created_at).total_seconds()
                if delta <= 300:  # 5 min
                    score += SCORE_RULES["response_within_5min"]
                elif delta <= 3600:  # 1h
                    score += SCORE_RULES["response_within_1h"]

        # Multiple messages same day
        from collections import defaultdict
        by_day = defaultdict(int)
        for m in messages:
            day = m.created_at.strftime("%Y-%m-%d")
            by_day[day] += 1
        for count in by_day.values():
            if count >= 3:
                score += SCORE_RULES["multiple_messages_same_day"]

        return min(score, 50)

    async def _calc_intent(self, messages, conversation) -> int:
        score = 0
        if not messages:
            return score

        intent_keywords = {
            "price_inquiry": ["precio", "cuanto cuesta", "valor", "costo", "tarifa", "presupuesto", "quote"],
            "availability_inquiry": ["disponible", "hay stock", "cuando", "horario", "turno", "cita"],
            "appointment_request": ["agendar", "reservar", "demo", "reunion", "llamada", "consulta"],
            "demo_request": ["demo", "prueba", "test", "muestra", "gratis", "free trial"],
            "product_inquiry": ["producto", "servicio", "que ofrecen", "que hacen", "como funciona"],
            "complaint": ["reclamo", "queja", "malo", "peor", "estafa", "problema", "devolucion"],
        }

        for m in messages:
            if m.direction.value != "inbound":
                continue
            content = (m.content or "").lower()
            for intent, keywords in intent_keywords.items():
                if any(kw in content for kw in keywords):
                    score += SCORE_RULES.get(intent, 0)

        return min(score, 50)

    async def _calc_demographic(self, conversation) -> int:
        score = 0
        extra = conversation.extra_data or {}

        if extra.get("email") or extra.get("lead_email"):
            score += SCORE_RULES["provided_email"]
        if extra.get("phone") or extra.get("lead_phone"):
            score += SCORE_RULES["provided_phone"]
        if extra.get("address") or extra.get("shipping_address"):
            score += SCORE_RULES["provided_address"]

        return min(score, 40)

    async def _calc_behavioral(self, conversation) -> int:
        score = 0
        extra = conversation.extra_data or {}

        if extra.get("revisited"):
            score += SCORE_RULES["revisited_conversation"]
        if extra.get("clicked_link"):
            score += SCORE_RULES["clicked_link"]
        if extra.get("viewed_catalog"):
            score += SCORE_RULES["viewed_catalog"]
        if extra.get("added_to_cart"):
            score += SCORE_RULES["added_to_cart"]

        return min(score, 40)

    async def _calc_recency(self, messages, conversation) -> int:
        score = 0
        if not messages:
            return score

        now = datetime.now(timezone.utc)
        last_message = max(m.created_at for m in messages if m.created_at)

        days_since_last = (now - last_message).days

        if days_since_last <= 1:
            score += SCORE_RULES["activity_today"]
        elif days_since_last <= 7:
            score += SCORE_RULES["activity_this_week"]
        elif days_since_last <= 30:
            score += SCORE_RULES["activity_this_month"]
        elif days_since_last >= 30:
            score += SCORE_RULES["inactive_30days"]
        elif days_since_last >= 7:
            score += SCORE_RULES["inactive_7days"]

        return score

    async def _generate_commentary(
        self,
        conversation: Conversation,
        business_id: uuid.UUID,
        previous_classification: str,
        new_classification: str,
        previous_score: int,
        new_score: int,
        engagement: int,
        intent: int,
        demographic: int,
        behavioral: int,
        recency: int,
    ) -> Optional[str]:
        """Generate an AI expert commentary explaining the score change."""
        from app.domains.agents.prompts import compose_system_prompt
        from app.domains.businesses.models import Business
        from app.domains.agents.llm_provider import generate_with_fallback
        from langchain_core.messages import SystemMessage, HumanMessage

        # Get business info
        result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        if not business:
            return None

        # Build prompt with expert analyst voice
        system_prompt = compose_system_prompt(
            base_slug="data-analyst",
            voice_slug=None,
            business_context={
                "name": business.name,
                "type": business.type.value if business.type else "unknown",
            },
        )

        # Override system prompt for scoring commentary
        system_prompt = f"""You are a Lead Scoring Analyst AI. You analyze sales lead behavior and explain score changes in clear, actionable language.

YOUR STYLE:
- Concise, insightful, no fluff. One or two sentences max.
- Use specific data points from the scoring breakdown.
- Speak like a senior sales analyst briefing a CEO.
- Focus on WHY the classification changed and WHAT it means.

RULES:
- Respond ONLY with the commentary text. No greetings, no sign-offs.
- Be factual but compelling.
- If the lead got HOTTER, highlight the buying signals.
- If the lead got COLDER, explain the warning signs.
"""

        user_prompt = f"""Lead: {conversation.lead_name or 'Unknown'}
Score change: {previous_score} ({previous_classification}) → {new_score} ({new_classification})

Breakdown:
- Engagement: {engagement}/50
- Intent: {intent}/50
- Demographic: {demographic}/40
- Behavioral: {behavioral}/40
- Recency: {recency}/20

Write a brief commentary (1-2 sentences) explaining this score change to the sales team."""

        try:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            response = await generate_with_fallback(
                self.db, business_id, messages, model="llama3.1", temperature=0.5, max_tokens=200,
            )
            if not response:
                return None
            return response.content.strip()
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Commentary generation error: {e}")
            return None

    async def record_activity(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
        activity_type: str,
        points: int = 0,
        description: str = "",
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> LeadActivity:
        """Record a lead activity and trigger score recalculation."""
        activity = LeadActivity(
            business_id=business_id,
            conversation_id=conversation_id,
            activity_type=activity_type,
            points=points,
            description=description,
            meta_data=meta_data or {},
        )
        self.db.add(activity)
        await self.db.commit()

        # Recalculate score
        await self.calculate_score(conversation_id, business_id)

        return activity
