"""Memory Engine Celery Tasks"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.async_bridge import run_async
from app.core.logger import get_logger
from app.domains.channels.models import Conversation
from app.domains.memory.summarizer import summarize_conversation

logger = get_logger(__name__)


@shared_task(name="app.domains.memory.tasks.summarize_conversation_task")
def summarize_conversation_task(conversation_id: Optional[str] = None):
    """Celery task that summarizes a conversation and extracts customer facts.

    If conversation_id is not provided, processes all active conversations
    with recent messages (last 24h).
    """

    async def _run_single(cid: uuid.UUID):
        async with AsyncSessionLocal() as db:
            result = await summarize_conversation(db, cid)
            logger.info(f"Summarized conversation {cid}")
            return {"status": "ok", "conversation_id": str(cid), "summary": result}

    async def _run_all():
        async with AsyncSessionLocal() as db:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
            result = await db.execute(
                select(Conversation.id)
                .where(
                    Conversation.last_message_at >= since,
                    Conversation.is_active == True,
                )
            )
            conversation_ids = [row[0] for row in result.all()]

        processed = []
        for cid in conversation_ids:
            try:
                processed.append(await _run_single(cid))
            except Exception as exc:
                logger.error(f"summarize_conversation_task failed for {cid}: {exc}")

        return {
            "status": "ok",
            "processed": len(processed),
            "total": len(conversation_ids),
        }

    if conversation_id:
        return run_async(_run_single(uuid.UUID(conversation_id)))
    return run_async(_run_all())
