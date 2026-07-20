"""Feedback Loop / Prompt Improvement

Tracks conversation outcomes, analyzes prompt effectiveness,
and uses LLM to suggest prompt improvements.
"""

import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Numeric, Float, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.core.logger import get_logger

logger = get_logger(__name__)


class ConversationOutcome(Base):
    """Stores the outcome of a conversation for prompt optimization analysis."""

    __tablename__ = "conversation_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_type = Column(String(50), nullable=False)
    outcome = Column(
        String(50),
        nullable=False,
    )  # 'lead_generated', 'sale_closed', 'objection_overcome', 'lost', 'no_progress'
    revenue = Column(Numeric(12, 2), nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    feedback = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class PromptOptimizer:
    """Service for recording outcomes and suggesting prompt improvements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_outcome(
        self,
        conversation_id: uuid.UUID,
        agent_type: str,
        outcome: str,
        revenue: Optional[float] = None,
        confidence: float = 0.0,
        feedback: Optional[str] = None,
    ) -> ConversationOutcome:
        """Record the outcome of a conversation."""
        record = ConversationOutcome(
            conversation_id=conversation_id,
            agent_type=agent_type,
            outcome=outcome,
            revenue=revenue,
            confidence=confidence,
            feedback=feedback,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        logger.info(f"Recorded outcome {outcome} for conversation {conversation_id}")
        return record

    async def analyze_prompt_effectiveness(
        self,
        agent_type: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Correlate prompt usage with outcomes and return success rate by variant."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(ConversationOutcome)
            .where(
                ConversationOutcome.agent_type == agent_type,
                ConversationOutcome.created_at >= cutoff,
            )
        )
        records = result.scalars().all()

        total = len(records)
        if total == 0:
            return {"total": 0, "success_rate": 0.0, "by_outcome": {}}

        by_outcome: Dict[str, int] = {}
        successes = 0
        total_revenue = 0.0
        revenue_count = 0

        for r in records:
            by_outcome[r.outcome] = by_outcome.get(r.outcome, 0) + 1
            if r.outcome in ("lead_generated", "sale_closed", "objection_overcome"):
                successes += 1
            if r.revenue is not None:
                total_revenue += float(r.revenue)
                revenue_count += 1

        return {
            "total": total,
            "success_rate": successes / total,
            "by_outcome": by_outcome,
            "avg_revenue": total_revenue / revenue_count if revenue_count > 0 else None,
        }

    async def suggest_prompt_improvements(
        self,
        agent_type: str,
        days: int = 30,
    ) -> List[Dict[str, str]]:
        """
        Analyze failed conversations and use LLM to suggest prompt improvements.
        Returns list of suggested changes with rationale.
        """
        from app.domains.agents.ai_reply import generate_raw_ai_response
        from app.domains.channels.models import Conversation
        from app.domains.memory.models import ConversationMemoryChunk

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(ConversationOutcome)
            .where(
                ConversationOutcome.agent_type == agent_type,
                ConversationOutcome.outcome.in_(["lost", "no_progress"]),
                ConversationOutcome.created_at >= cutoff,
            )
            .limit(20)
        )
        failed = result.scalars().all()

        if not failed:
            return []

        contexts = []
        business_id = None

        for outcome in failed:
            chunk_result = await self.db.execute(
                select(ConversationMemoryChunk)
                .where(ConversationMemoryChunk.conversation_id == outcome.conversation_id)
                .order_by(ConversationMemoryChunk.chunk_index.asc())
                .limit(10)
            )
            chunks = chunk_result.scalars().all()
            if not chunks:
                continue

            if business_id is None:
                business_id = chunks[0].business_id

            transcript = "\n".join(f"{c.role}: {c.content}" for c in chunks)
            contexts.append(
                f"Outcome: {outcome.outcome}\n"
                f"Feedback: {outcome.feedback or 'N/A'}\n"
                f"Transcript:\n{transcript}\n---"
            )

        if not contexts or not business_id:
            return []

        prompt = (
            "Analiza las siguientes conversaciones fallidas de ventas y sugiere mejoras "
            "al prompt del agente. Devuelve una lista de cambios sugeridos con su "
            "justificación en formato JSON:\n"
            '{"suggestions": [{"change": "...", "rationale": "..."}]}\n\n'
            + "\n\n".join(contexts)
        )

        response = await generate_raw_ai_response(
            db=self.db,
            business_id=business_id,
            system_prompt=(
                "Eres un experto en optimización de prompts para agentes de ventas AI. "
                "Analiza conversaciones fallidas y sugiere cambios concretos y accionables."
            ),
            user_prompt=prompt,
            max_tokens=1500,
            temperature=0.5,
        )

        if not response:
            return []

        try:
            data = json.loads(response)
            return data.get("suggestions", [])
        except json.JSONDecodeError:
            return [
                {
                    "change": response,
                    "rationale": "Respuesta del modelo (no pudo parsear JSON)",
                }
            ]
