"""Document Processor — text extraction, chunking, embedding, search."""

import os
import uuid
import math
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.documents.models import BusinessDocument, DocumentChunk, Vector

logger = get_logger(__name__)
settings = get_settings()

STORAGE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) / "storage" / "documents"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE_CHARS = 1000
CHUNK_OVERLAP_CHARS = 200


class EmbeddingService:
    """Generate embeddings via OpenAI or fallback to random normalized vectors."""

    def __init__(self):
        self._client = None
        self._fallback = False
        try:
            import openai
            if settings.OPENAI_API_KEY:
                self._client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            else:
                self._fallback = True
        except Exception:
            self._fallback = True

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if self._client is not None and not self._fallback:
            try:
                response = await self._client.embeddings.create(
                    input=texts,
                    model="text-embedding-3-large",
                    dimensions=768,
                )
                return [item.embedding for item in response.data]
            except Exception as exc:
                logger.warning(f"OpenAI embedding failed: {exc}; using fallback")
                self._fallback = True
        return [self._random_vector(768) for _ in texts]

    @staticmethod
    def _random_vector(dim: int) -> List[float]:
        vec = [random.gauss(0, 1) for _ in range(dim)]
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm > 0 else vec


embedding_service = EmbeddingService()


def _extract_text_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _extract_text_pdf(file_path: str) -> str:
    text_parts = []
    # Try pdfplumber first (better quality)
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception:
        pass

    # Fallback to PyPDF2
    try:
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception:
        pass

    logger.warning(f"Could not extract text from PDF: {file_path}")
    return ""


def _extract_text_docx(file_path: str) -> str:
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text)
    except Exception:
        logger.warning(f"Could not extract text from DOCX: {file_path}")
        return ""


def _extract_text(file_path: str, file_type: str) -> str:
    ft = file_type.lower()
    if ft == "txt":
        return _extract_text_txt(file_path)
    if ft == "pdf":
        return _extract_text_pdf(file_path)
    if ft in ("docx", "doc"):
        return _extract_text_docx(file_path)
    if ft == "csv":
        return _extract_text_txt(file_path)
    logger.warning(f"Unsupported file type for extraction: {ft}")
    return ""


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks by paragraphs."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current_text = ""
    current_paras = []

    for para in paragraphs:
        if len(current_text) + len(para) + 1 > chunk_size and current_text:
            chunks.append({"text": current_text.strip(), "paras": len(current_paras)})
            # overlap: keep last part of current chunk
            if overlap > 0 and len(current_text) > overlap:
                current_text = current_text[-overlap:]
                # Try to start at a paragraph boundary within the overlap
                split_idx = current_text.find("\n")
                if split_idx != -1:
                    current_text = current_text[split_idx + 1:]
            else:
                current_text = ""
            current_paras = []
        current_text += para + "\n"
        current_paras.append(para)

    if current_text.strip():
        chunks.append({"text": current_text.strip(), "paras": len(current_paras)})

    return chunks


class DocumentProcessor:
    """Process business documents: extract, chunk, embed, store."""

    async def process_document(self, db: AsyncSession, document_id: uuid.UUID, file_path: str, file_type: str) -> None:
        result = await db.execute(select(BusinessDocument).where(BusinessDocument.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            logger.error(f"Document {document_id} not found for processing")
            return

        # Update status
        doc.status = "processing"
        await db.commit()

        try:
            text = _extract_text(file_path, file_type)
            if not text.strip():
                raise ValueError("No text could be extracted from the document")

            chunks = _chunk_text(text)
            if not chunks:
                raise ValueError("No chunks generated from document")

            embeddings = await embedding_service.embed([c["text"] for c in chunks])

            # Delete any existing chunks for this document (re-processing)
            await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

            for idx, (chunk_data, emb) in enumerate(zip(chunks, embeddings)):
                chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    business_id=doc.business_id,
                    content=chunk_data["text"],
                    embedding=emb,
                    chunk_index=idx,
                    page_number=None,
                    chunk_metadata={"paras": chunk_data.get("paras", 0)},
                )
                db.add(chunk)

            doc.chunk_count = len(chunks)
            doc.status = "ready"
            await db.commit()
            logger.info(f"Document {document_id} processed with {len(chunks)} chunks")
        except Exception as exc:
            logger.exception(f"Failed to process document {document_id}: {exc}")
            doc.status = "error"
            doc.extra_data = {**(doc.extra_data or {}), "error": str(exc)}
            await db.commit()

    async def search_documents(self, db: AsyncSession, business_id: uuid.UUID, query: str, k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = (await embedding_service.embed([query]))[0]

        # Use pgvector <=> operator (cosine distance) if available
        # Fallback to simple LIKE search if vector ops fail
        try:
            # Build vector string for raw SQL
            vec_str = f"[{','.join(str(v) for v in query_embedding)}]"
            sql = text("""
                SELECT
                    dc.id AS chunk_id,
                    dc.document_id,
                    dc.content,
                    dc.chunk_index,
                    dc.page_number,
                    dc.chunk_metadata,
                    bd.title AS document_title,
                    dc.embedding <=> CAST(:vec AS vector(768)) AS distance
                FROM document_chunks dc
                JOIN business_documents bd ON bd.id = dc.document_id
                WHERE dc.business_id = :business_id AND bd.status = 'ready'
                ORDER BY dc.embedding <=> CAST(:vec AS vector(768))
                LIMIT :k
            """)
            result = await db.execute(sql, {
                "vec": vec_str,
                "business_id": str(business_id),
                "k": k,
            })
            rows = result.mappings().all()
            return [
                {
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "title": row["document_title"],
                    "content": row["content"],
                    "chunk_index": row["chunk_index"],
                    "page_number": row["page_number"],
                    "score": 1.0 - float(row["distance"]),
                    "metadata": row["chunk_metadata"] or {},
                }
                for row in rows
            ]
        except Exception as exc:
            logger.warning(f"Vector search failed ({exc}), falling back to text search")
            await db.rollback()
            # Fallback: simple text search on content
            result = await db.execute(
                select(DocumentChunk, BusinessDocument.title)
                .join(BusinessDocument, DocumentChunk.document_id == BusinessDocument.id)
                .where(
                    DocumentChunk.business_id == business_id,
                    BusinessDocument.status == "ready",
                    DocumentChunk.content.ilike(f"%{query}%"),
                )
                .limit(k)
            )
            rows = result.all()
            return [
                {
                    "chunk_id": row.DocumentChunk.id,
                    "document_id": row.DocumentChunk.document_id,
                    "title": row.title,
                    "content": row.DocumentChunk.content,
                    "chunk_index": row.DocumentChunk.chunk_index,
                    "page_number": row.DocumentChunk.page_number,
                    "score": 0.5,
                    "metadata": row.DocumentChunk.chunk_metadata or {},
                }
                for row in rows
            ]

    async def delete_document(self, db: AsyncSession, document_id: uuid.UUID) -> bool:
        result = await db.execute(select(BusinessDocument).where(BusinessDocument.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            return False

        # Delete file from storage
        try:
            fp = Path(doc.file_path)
            if fp.exists():
                fp.unlink()
        except Exception as exc:
            logger.warning(f"Could not delete file {doc.file_path}: {exc}")

        # Delete chunks and document (cascade handles chunks in DB)
        await db.delete(doc)
        await db.commit()
        return True


document_processor = DocumentProcessor()
