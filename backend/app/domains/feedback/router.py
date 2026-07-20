"""Feedback Hub API router."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.feedback.service import FeedbackService
from app.domains.feedback.schemas import (
    FeedbackCreate, FeedbackUpdate, FeedbackResponse, FeedbackListResponse,
    CommentCreate, CommentResponse, RoadmapResponse, ChangelogEntry,
)
from app.domains.feedback.ai_analyzer import analyze_feedback
from app.domains.feedback.models import FeedbackType, FeedbackStatus

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _svc(db: AsyncSession = Depends(get_db)) -> FeedbackService:
    return FeedbackService(db)


# ===== Public/User Endpoints =====

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    svc: FeedbackService = Depends(_svc),
):
    """Crear nuevo feedback (bug, idea, queja, elogio)."""
    feedback = await svc.create_feedback(
        user_id=current_user.id,
        data=data,
    )

    # AI analysis in background (non-blocking for user)
    try:
        business_id = current_user.businesses[0].id if current_user.businesses else uuid.UUID(int=0)
        fb_type, category, severity, analysis, solution, confidence, duplicate_id = await analyze_feedback(
            db=svc.db,
            business_id=business_id,
            title=data.title,
            description=data.description,
        )
        feedback.ai_analysis = analysis
        feedback.ai_solution_proposal = solution
        feedback.ai_confidence = confidence
        feedback.ai_duplicate_of_id = duplicate_id
        feedback.category = category
        if not duplicate_id:
            feedback.severity = severity
        await svc.db.commit()
        await svc.db.refresh(feedback)
    except Exception:
        pass

    return feedback


@router.get("", response_model=FeedbackListResponse)
async def list_public_feedback(
    status: Optional[FeedbackStatus] = None,
    type: Optional[FeedbackType] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    svc: FeedbackService = Depends(_svc),
):
    """Listar feedback público (roadmap/ideas)."""
    items, total = await svc.list_feedback(status=status, type=type, search=search, limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.get("/my", response_model=FeedbackListResponse)
async def list_my_feedback(
    current_user: User = Depends(get_current_active_user),
    svc: FeedbackService = Depends(_svc),
):
    """Listar feedback del usuario autenticado."""
    items, total = await svc.list_feedback(user_id=current_user.id)
    return {"items": items, "total": total}


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_active_user),
    svc: FeedbackService = Depends(_svc),
):
    """Ver detalle de un feedback."""
    feedback = await svc.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")

    response_data = {**feedback.__dict__}
    if current_user:
        response_data["user_voted"] = await svc.has_voted(feedback_id, current_user.id)
    return response_data


@router.post("/{feedback_id}/vote")
async def vote_feedback(
    feedback_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    svc: FeedbackService = Depends(_svc),
):
    """Votar por un feedback (ideas)."""
    success = await svc.vote(feedback_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Ya votaste este feedback")
    return {"message": "Voto registrado"}


@router.post("/{feedback_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    feedback_id: uuid.UUID,
    data: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    svc: FeedbackService = Depends(_svc),
):
    """Agregar comentario a un feedback."""
    feedback = await svc.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")
    comment = await svc.add_comment(feedback_id, current_user.id, data)
    return comment


@router.get("/{feedback_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    feedback_id: uuid.UUID,
    svc: FeedbackService = Depends(_svc),
):
    """Listar comentarios de un feedback."""
    return await svc.list_comments(feedback_id)


@router.get("/roadmap/public", response_model=RoadmapResponse)
async def get_public_roadmap(svc: FeedbackService = Depends(_svc)):
    """Roadmap público de mejoras (sin auth)."""
    return await svc.get_roadmap()


@router.get("/changelog/public", response_model=list[ChangelogEntry])
async def get_public_changelog(
    limit: int = Query(20, ge=1, le=100),
    svc: FeedbackService = Depends(_svc),
):
    """Changelog público de actualizaciones."""
    items = await svc.get_changelog(limit=limit)
    return items


# ===== Admin Endpoints =====

@router.get("/admin/all", response_model=FeedbackListResponse)
async def admin_list_all(
    status: Optional[FeedbackStatus] = None,
    type: Optional[FeedbackType] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    svc: FeedbackService = Depends(_svc),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin required")
    items, total = await svc.list_feedback(status=status, type=type, limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.patch("/admin/{feedback_id}", response_model=FeedbackResponse)
async def admin_update(
    feedback_id: uuid.UUID,
    data: FeedbackUpdate,
    current_user: User = Depends(get_current_active_user),
    svc: FeedbackService = Depends(_svc),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin required")
    feedback = await svc.update_feedback(feedback_id, data)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")
    return feedback


@router.post("/admin/{feedback_id}/ai-analyze")
async def admin_force_ai_analyze(
    feedback_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    svc: FeedbackService = Depends(_svc),
):
    """Forzar re-análisis AI de un feedback."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin required")

    feedback = await svc.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")

    business_id = current_user.businesses[0].id if current_user.businesses else uuid.UUID(int=0)
    fb_type, category, severity, analysis, solution, confidence, duplicate_id = await analyze_feedback(
        db=svc.db,
        business_id=business_id,
        title=feedback.title,
        description=feedback.description,
    )

    feedback.ai_analysis = analysis
    feedback.ai_solution_proposal = solution
    feedback.ai_confidence = confidence
    feedback.ai_duplicate_of_id = duplicate_id
    feedback.category = category
    await svc.db.commit()
    await svc.db.refresh(feedback)
    return feedback
