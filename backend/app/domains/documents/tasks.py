"""Document RAG Celery Tasks"""

import asyncio
import uuid
from celery import shared_task

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.documents.processor import document_processor

logger = get_logger(__name__)


@shared_task
def process_document_task(document_id: str):
    """Process a business document: extract text, chunk, embed, store."""
    async def _run():
        async with AsyncSessionLocal() as db:
            doc_id = uuid.UUID(document_id)
            # Fetch document to get file_path and file_type
            from sqlalchemy import select
            from app.domains.documents.models import BusinessDocument
            result = await db.execute(select(BusinessDocument).where(BusinessDocument.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                logger.error(f"Document {document_id} not found in task")
                return
            await document_processor.process_document(db, doc_id, doc.file_path, doc.file_type)

    asyncio.run(_run())
    logger.info(f"Document processing task completed for {document_id}")
