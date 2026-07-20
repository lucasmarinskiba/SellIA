"""Computer Use Audit Log API Router

Endpoints para ver actividad REAL de agents:
- GET /audit-logs — historial de actividades
- GET /audit-logs/{id} — detalles de una actividad
- GET /audit-logs/summary — resumen estadístico
- GET /audit-logs/pending — acciones pendientes aprobación
- POST /audit-logs/{id}/approve — aprobar acción
- POST /audit-logs/{id}/reject — rechazar acción
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.logger import get_logger
from app.domains.users.models import User
from app.domains.computer_use.services.audit_log_service import (
    get_audit_log_service,
    AuditLogService,
)
from app.domains.computer_use.models_audit_log import ComputerUseAuditLogSearchFilter
from app.domains.computer_use.schemas_audit_log import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogSearchRequest,
    AuditLogApprovalRequest,
    AuditLogSummaryResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    platform: str = Query(None, description="Filter by platform"),
    action_type: str = Query(None, description="Filter by action type"),
    agent_name: str = Query(None, description="Filter by agent"),
    status: str = Query(None, description="Filter by status"),
    days: int = Query(default=7, ge=1, le=90, description="Last N days"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Lista audit logs del usuario.

    Filtrable por platform/action_type/agent/status/días.
    """
    audit_service = get_audit_log_service(db)

    date_from = datetime.utcnow() - timedelta(days=days)

    filter_obj = ComputerUseAuditLogSearchFilter(
        user_id=str(current_user.id),
        platform=platform,
        action_type=action_type,
        agent_name=agent_name,
        status=status,
        date_from=date_from,
        limit=limit,
        offset=offset,
    )

    logs, total = await audit_service.search(filter_obj)

    return AuditLogListResponse(
        logs=[AuditLogResponse.from_orm(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene detalles de una actividad del audit log."""
    audit_service = get_audit_log_service(db)
    log = await audit_service.get_by_id(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    if log.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    return AuditLogResponse.from_orm(log)


@router.get("/audit-logs/pending", response_model=list[AuditLogResponse])
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Acciones pendientes de aprobación del usuario."""
    audit_service = get_audit_log_service(db)
    logs = await audit_service.get_pending_approvals(str(current_user.id))

    return [AuditLogResponse.from_orm(log) for log in logs]


@router.post("/audit-logs/{log_id}/approve", response_model=AuditLogResponse)
async def approve_audit_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Aprueba una acción pendiente."""
    audit_service = get_audit_log_service(db)

    log = await audit_service.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    if log.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    if log.status != "pending_approval":
        raise HTTPException(status_code=400, detail="Log is not pending approval")

    updated_log = await audit_service.approve(log_id, str(current_user.id))

    logger.info(f"User {current_user.id} approved audit log {log_id}")

    return AuditLogResponse.from_orm(updated_log)


@router.post("/audit-logs/{log_id}/reject", response_model=AuditLogResponse)
async def reject_audit_log(
    log_id: str,
    request: AuditLogApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Rechaza una acción pendiente."""
    audit_service = get_audit_log_service(db)

    log = await audit_service.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    if log.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    if log.status != "pending_approval":
        raise HTTPException(status_code=400, detail="Log is not pending approval")

    updated_log = await audit_service.reject(
        log_id,
        str(current_user.id),
        request.reason,
    )

    logger.info(f"User {current_user.id} rejected audit log {log_id}")

    return AuditLogResponse.from_orm(updated_log)


@router.get("/audit-logs/summary", response_model=AuditLogSummaryResponse)
async def get_audit_log_summary(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Resumen estadístico de actividades.

    Muestra total acciones, por platform, por action_type, por status.
    """
    audit_service = get_audit_log_service(db)
    summary = await audit_service.get_summary(str(current_user.id), days=days)

    return AuditLogSummaryResponse(**summary)
