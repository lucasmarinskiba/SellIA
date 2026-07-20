"""Business Document RAG API Router"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.documents.service import DocumentService
from app.domains.documents.schemas import (
    BusinessDocumentResponse,
    BusinessDocumentDetailResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
)

router = APIRouter(tags=["documents"])


# ========== Documents ==========

@router.post(
    "/businesses/{business_id}/documents",
    response_model=BusinessDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    business_id: UUID,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = DocumentService(db)
    try:
        doc = await svc.upload_document(business_id, file, title)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return doc


@router.get("/businesses/{business_id}/documents", response_model=list[BusinessDocumentResponse])
async def list_documents(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = DocumentService(db)
    return await svc.list_documents(business_id)


@router.get("/businesses/{business_id}/documents/{document_id}", response_model=BusinessDocumentDetailResponse)
async def get_document(
    business_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = DocumentService(db)
    doc = await svc.get_document(document_id)
    if not doc or doc.business_id != business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")
    return doc


@router.delete("/businesses/{business_id}/documents/{document_id}")
async def delete_document(
    business_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = DocumentService(db)
    doc = await svc.get_document(document_id)
    if not doc or doc.business_id != business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")
    await svc.delete_document(document_id)
    return {"message": "Documento eliminado"}


# ========== Semantic Search ==========

@router.post("/businesses/{business_id}/documents/search", response_model=DocumentSearchResponse)
async def search_documents(
    business_id: UUID,
    data: DocumentSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = DocumentService(db)
    results = await svc.search_documents(business_id, data.query, data.k)
    return DocumentSearchResponse(query=data.query, results=results)
