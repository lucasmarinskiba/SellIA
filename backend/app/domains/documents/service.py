"""Business Document Service Layer"""

import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.logger import get_logger
from app.domains.documents.models import BusinessDocument, DocumentChunk
from app.domains.documents.processor import document_processor, STORAGE_DIR
from app.domains.documents.tasks import process_document_task

logger = get_logger(__name__)

ALLOWED_TYPES = {"pdf", "txt", "docx", "csv"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _get_file_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext


def _is_allowed_type(ext: str) -> bool:
    return ext in ALLOWED_TYPES


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_document(
        self,
        business_id: uuid.UUID,
        file: UploadFile,
        title: Optional[str] = None,
    ) -> BusinessDocument:
        if not file.filename:
            raise ValueError("Filename is required")

        ext = _get_file_extension(file.filename)
        if not _is_allowed_type(ext):
            raise ValueError(f"File type not allowed: {ext}")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {len(content)} bytes (max {MAX_FILE_SIZE})")

        safe_title = title or Path(file.filename).stem
        unique_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = STORAGE_DIR / unique_name

        with open(file_path, "wb") as f:
            f.write(content)

        doc = BusinessDocument(
            id=uuid.uuid4(),
            business_id=business_id,
            title=safe_title,
            file_path=str(file_path),
            file_type=ext,
            file_size=len(content),
            status="processing",
            chunk_count=0,
            extra_data={"original_filename": file.filename},
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        # Queue Celery task
        try:
            process_document_task.delay(str(doc.id))
        except Exception as exc:
            logger.warning(f"Could not queue Celery task: {exc}; processing will happen on next read or manually")

        return doc

    async def list_documents(self, business_id: uuid.UUID) -> List[BusinessDocument]:
        result = await self.db.execute(
            select(BusinessDocument)
            .where(BusinessDocument.business_id == business_id)
            .order_by(desc(BusinessDocument.created_at))
        )
        return result.scalars().all()

    async def get_document(self, document_id: uuid.UUID) -> Optional[BusinessDocument]:
        result = await self.db.execute(
            select(BusinessDocument).where(BusinessDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def delete_document(self, document_id: uuid.UUID) -> bool:
        return await document_processor.delete_document(self.db, document_id)

    async def search_documents(
        self,
        business_id: uuid.UUID,
        query: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        return await document_processor.search_documents(self.db, business_id, query, k)
