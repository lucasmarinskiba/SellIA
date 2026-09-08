"""Conversation Pattern Analyzer -- real pattern analysis over conversations/deals.

Replaces the previous "knowledge base" mock (KnowledgeBase/KnowledgeEntry
dataclasses, in-memory, confidence_score=random.uniform(60, 95),
estimated_impact=f"+{random.randint(5, 25)}%") with simple, real counts over
actual data: what did conversations that ended in a won deal look like,
compared to ones that were lost? No ML/embeddings -- word frequency, message
counts, and averages over app.domains.enterprise.forecasting_models.DealOutcome
(real win/loss records, wired in enterprise_deal_intelligence.py) joined to
their Deal's Conversation and Messages.
"""

import re
import uuid
from collections import Counter
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.crm.models import Deal
from app.domains.enterprise.forecasting_models import DealOutcome
from app.domains.channels.models import Conversation, Message, MessageDirection

# Small, pragmatic ES+EN stopword list for word-frequency counting -- not a
# linguistics library, just enough to keep "que", "the", "de" etc. from
# drowning out actually distinctive words in the counts.
_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "que", "y", "o", "a", "en", "es", "por", "para", "con", "su", "sus", "se",
    "lo", "le", "les", "te", "me", "mi", "tu", "nos", "si", "no", "ya", "muy",
    "mas", "más", "pero", "como", "cuando", "donde", "qué", "esta", "este",
    "esa", "ese", "eso", "esto", "hay", "ha", "he", "vas", "voy", "es", "son",
    "the", "a", "an", "to", "of", "for", "and", "or", "is", "are", "in", "on",
    "it", "you", "your", "we", "our", "i", "this", "that", "with", "be", "at",
    "hola", "gracias", "buenas", "buenos", "dias", "días", "tardes", "noches",
}
_WORD_RE = re.compile(r"[a-zA-Záéíóúñü]{3,}", re.IGNORECASE)


def _tokenize(text: str) -> list[str]:
    words = _WORD_RE.findall(text.lower())
    return [w for w in words if w not in _STOPWORDS]


class ConversationPatternAnalyzer:
    """Real pattern analysis over a business's won/lost deal conversations."""

    @staticmethod
    async def get_win_loss_patterns(db: AsyncSession, business_id: uuid.UUID) -> dict:
        """Compare conversations that led to a won deal vs a lost one:
        message volume, time to close, and win rate broken down by which
        sales-agent personality/voice was used (from the A/B testing
        assignment stashed on Conversation.extra_data, when present)."""
        result = await db.execute(
            select(DealOutcome, Deal)
            .join(Deal, Deal.id == DealOutcome.deal_id)
            .where(DealOutcome.business_id == business_id)
        )
        rows = result.all()

        won = [(o, d) for o, d in rows if o.outcome == "won"]
        lost = [(o, d) for o, d in rows if o.outcome == "lost"]

        async def _avg_message_count(pairs: list) -> Optional[float]:
            conv_ids = [d.conversation_id for _, d in pairs if d.conversation_id]
            if not conv_ids:
                return None
            count_result = await db.execute(
                select(func.count(Message.id)).where(Message.conversation_id.in_(conv_ids))
            )
            total_messages = count_result.scalar() or 0
            return round(total_messages / len(conv_ids), 1)

        async def _win_rate_by_personality() -> dict:
            conv_ids = [d.conversation_id for _, d in rows if d.conversation_id]
            if not conv_ids:
                return {}
            conv_result = await db.execute(
                select(Conversation.id, Conversation.extra_data).where(Conversation.id.in_(conv_ids))
            )
            personality_by_conv = {}
            for conv_id, extra_data in conv_result.all():
                tracking = (extra_data or {}).get("personality_ab") or (extra_data or {}).get("funnel_ab")
                slug = tracking.get("agent_type") or tracking.get("stage") if tracking else None
                if slug:
                    personality_by_conv[conv_id] = slug

            tally: dict = {}
            for outcome_row, deal in rows:
                slug = personality_by_conv.get(deal.conversation_id)
                if not slug:
                    continue
                bucket = tally.setdefault(slug, {"won": 0, "lost": 0})
                bucket[outcome_row.outcome] = bucket.get(outcome_row.outcome, 0) + 1

            return {
                slug: {
                    **counts,
                    "win_rate": f"{(counts['won'] / max(counts['won'] + counts['lost'], 1)) * 100:.1f}%",
                }
                for slug, counts in tally.items()
            }

        avg_days_won = round(sum(o.days_to_close for o, _ in won if o.days_to_close is not None) / max(len([o for o, _ in won if o.days_to_close is not None]), 1), 1) if won else None
        avg_days_lost = round(sum(o.days_to_close for o, _ in lost if o.days_to_close is not None) / max(len([o for o, _ in lost if o.days_to_close is not None]), 1), 1) if lost else None

        return {
            "sample_size": {"won": len(won), "lost": len(lost)},
            "avg_messages_before_won": await _avg_message_count(won),
            "avg_messages_before_lost": await _avg_message_count(lost),
            "avg_days_to_close_won": avg_days_won,
            "avg_days_to_close_lost": avg_days_lost,
            "win_rate_by_agent": await _win_rate_by_personality(),
        }

    @staticmethod
    async def get_winning_phrases(
        db: AsyncSession, business_id: uuid.UUID, limit: int = 20
    ) -> dict:
        """Simple word-frequency count over the sales agent's own (outbound)
        messages in won vs lost conversations -- what words show up more in
        conversations that closed, vs ones that didn't. Real counts, not a
        language model."""
        result = await db.execute(
            select(DealOutcome.outcome, Deal.conversation_id)
            .join(Deal, Deal.id == DealOutcome.deal_id)
            .where(DealOutcome.business_id == business_id, Deal.conversation_id.isnot(None))
        )
        rows = result.all()
        won_conv_ids = [c for outcome, c in rows if outcome == "won"]
        lost_conv_ids = [c for outcome, c in rows if outcome == "lost"]

        async def _word_counts(conv_ids: list) -> Counter:
            counter: Counter = Counter()
            if not conv_ids:
                return counter
            msg_result = await db.execute(
                select(Message.content).where(
                    Message.conversation_id.in_(conv_ids),
                    Message.direction == MessageDirection.OUTBOUND,
                )
            )
            for (content,) in msg_result.all():
                counter.update(_tokenize(content or ""))
            return counter

        won_counts = await _word_counts(won_conv_ids)
        lost_counts = await _word_counts(lost_conv_ids)

        return {
            "sample_size": {"won_conversations": len(won_conv_ids), "lost_conversations": len(lost_conv_ids)},
            "top_words_in_won": [{"word": w, "count": c} for w, c in won_counts.most_common(limit)],
            "top_words_in_lost": [{"word": w, "count": c} for w, c in lost_counts.most_common(limit)],
        }
