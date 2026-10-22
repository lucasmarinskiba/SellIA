"""Support system API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.support.models import MessageSenderType, TicketStatus
from app.domains.support.schemas import (
    CSATSubmit,
    FAQCreate,
    FAQResponse,
    FAQUpdate,
    KnowledgeBaseArticleCreate,
    KnowledgeBaseArticleResponse,
    KnowledgeBaseArticleUpdate,
    SupportStatsResponse,
    SupportTicketCreate,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
    SupportTicketResponse,
    SupportTicketUpdate,
    TicketMessageCreate,
    TicketMessageResponse,
)
from app.domains.support.service import SupportService
from app.domains.users.models import User

router = APIRouter(prefix="/support", tags=["support"])


def _svc(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SupportService:
    return SupportService(db)


# ===== Tickets (User) =====


@router.post(
    "/tickets",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    data: SupportTicketCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    """Crear un nuevo ticket de soporte."""
    ticket = await svc.create_ticket(current_user.id, data)
    return ticket


@router.get("/tickets", response_model=SupportTicketListResponse)
async def list_my_tickets(
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
    status: TicketStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Listar tickets del usuario autenticado."""
    items, total = await svc.list_tickets(
        user_id=current_user.id, status=status, limit=limit, offset=offset
    )
    return {"items": items, "total": total}


@router.get("/tickets/{ticket_id}", response_model=SupportTicketDetailResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    """Obtener detalle de un ticket con sus mensajes."""
    ticket = await svc.get_ticket(ticket_id, user_id=current_user.id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    messages = await svc.list_messages(ticket_id, include_internal=False)
    return {**ticket.__dict__, "messages": messages}


@router.post(
    "/tickets/{ticket_id}/messages",
    response_model=TicketMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_message(
    ticket_id: uuid.UUID,
    data: TicketMessageCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    """Agregar un mensaje a un ticket."""
    ticket = await svc.get_ticket(ticket_id, user_id=current_user.id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    msg = await svc.add_message(
        ticket_id=ticket_id,
        content=data.content,
        sender_type=MessageSenderType.USER,
        sender_id=current_user.id,
    )
    return msg


@router.post("/tickets/{ticket_id}/escalate", response_model=SupportTicketResponse)
async def escalate_ticket(
    ticket_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    """Escalar un ticket a soporte humano."""
    ticket = await svc.get_ticket(ticket_id, user_id=current_user.id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    ticket = await svc.escalate_ticket(ticket_id)
    return ticket


@router.post("/tickets/{ticket_id}/csat", response_model=SupportTicketResponse)
async def submit_csat(
    ticket_id: uuid.UUID,
    data: CSATSubmit,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    """Enviar satisfacción del cliente (CSAT) para un ticket resuelto."""
    ticket = await svc.get_ticket(ticket_id, user_id=current_user.id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.status != TicketStatus.RESOLVED:
        raise HTTPException(
            status_code=400, detail="Solo se puede calificar tickets resueltos"
        )
    ticket = await svc.submit_csat(ticket_id, data)
    return ticket


# ===== FAQ (Public) =====


@router.get("/faq", response_model=list[FAQResponse])
async def list_faqs(
    svc: Annotated[SupportService, Depends(_svc)],
    business_id: uuid.UUID | None = None,
    search: str | None = None,
):
    """Listar FAQs públicas."""
    return await svc.list_faqs(business_id=business_id, search=search)


# ===== Knowledge Base (Public) =====


@router.get("/kb", response_model=list[KnowledgeBaseArticleResponse])
async def list_kb_articles(
    svc: Annotated[SupportService, Depends(_svc)],
    business_id: uuid.UUID | None = None,
    search: str | None = None,
):
    """Listar artículos de knowledge base."""
    return await svc.list_kb_articles(business_id=business_id, search=search)


# ===== Admin Endpoints =====


@router.get("/admin/tickets", response_model=SupportTicketListResponse)
async def admin_list_tickets(
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
    status: TicketStatus | None = None,
    priority: str | None = None,
    assigned_to: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Admin: Listar todos los tickets. Requiere superuser."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    items, total = await svc.list_tickets(
        status=status, assigned_to=assigned_to, limit=limit, offset=offset
    )
    return {"items": items, "total": total}


@router.get("/admin/tickets/{ticket_id}", response_model=SupportTicketDetailResponse)
async def admin_get_ticket(
    ticket_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    """Admin: Ver ticket completo con mensajes internos."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    ticket = await svc.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    messages = await svc.list_messages(ticket_id, include_internal=True)
    return {**ticket.__dict__, "messages": messages}


@router.patch("/admin/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def admin_update_ticket(
    ticket_id: uuid.UUID,
    data: SupportTicketUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    """Admin: Actualizar ticket (asignar, cambiar estado, prioridad)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    ticket = await svc.update_ticket(ticket_id, data)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


@router.post(
    "/admin/tickets/{ticket_id}/messages", response_model=TicketMessageResponse
)
async def admin_add_message(
    ticket_id: uuid.UUID,
    data: TicketMessageCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    """Admin: Responder a un ticket."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    ticket = await svc.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    msg = await svc.add_message(
        ticket_id=ticket_id,
        content=data.content,
        sender_type=MessageSenderType.AGENT,
        sender_id=current_user.id,
        is_internal=data.is_internal,
    )
    return msg


@router.get("/admin/stats", response_model=SupportStatsResponse)
async def admin_get_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
    business_id: uuid.UUID | None = None,
):
    """Admin: Estadísticas de soporte."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    stats = await svc.get_stats(business_id=business_id)
    return stats


# ===== Admin FAQ Management =====


@router.post(
    "/admin/faqs", response_model=FAQResponse, status_code=status.HTTP_201_CREATED
)
async def admin_create_faq(
    data: FAQCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
    business_id: uuid.UUID | None = None,
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    return await svc.create_faq(data, business_id=business_id)


@router.patch("/admin/faqs/{faq_id}", response_model=FAQResponse)
async def admin_update_faq(
    faq_id: uuid.UUID,
    data: FAQUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    faq = await svc.update_faq(faq_id, data)
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ no encontrada")
    return faq


@router.delete("/admin/faqs/{faq_id}")
async def admin_delete_faq(
    faq_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    if not await svc.delete_faq(faq_id):
        raise HTTPException(status_code=404, detail="FAQ no encontrada")
    return {"message": "FAQ eliminada"}


# ===== Admin KB Management =====


@router.post(
    "/admin/kb",
    response_model=KnowledgeBaseArticleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_kb_article(
    data: KnowledgeBaseArticleCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
    business_id: uuid.UUID | None = None,
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    return await svc.create_kb_article(data, business_id=business_id)


@router.patch("/admin/kb/{article_id}", response_model=KnowledgeBaseArticleResponse)
async def admin_update_kb_article(
    article_id: uuid.UUID,
    data: KnowledgeBaseArticleUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    article = await svc.update_kb_article(article_id, data)
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    return article


@router.delete("/admin/kb/{article_id}")
async def admin_delete_kb_article(
    article_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    svc: Annotated[SupportService, Depends(_svc)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere privilegios de admin")
    if not await svc.delete_kb_article(article_id):
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    return {"message": "Artículo eliminado"}
