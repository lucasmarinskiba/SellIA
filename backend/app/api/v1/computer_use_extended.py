"""Computer Use — Extended API Router

Endpoints adicionales para: templates, scheduled tasks, annotations,
browser profiles, proxies, session sharing, batch jobs, tags, webhooks,
export, replay, y analytics.
"""

import os
import csv
import json
import secrets
from datetime import datetime
from datetime import timezone, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.computer_use.models import ComputerUseSession, ComputerUseStep, ComputerUseMessage
from app.domains.computer_use.models_extended import (
    ComputerUseTemplate,
    ComputerUseScheduledTask,
    ComputerUseAnnotation,
    ComputerUseBrowserProfile,
    ComputerUseProxyConfig,
    ComputerUseSessionShare,
    ComputerUseBatchJob,
    ComputerUseSessionTag,
    ComputerUseWebhook,
)
from app.domains.computer_use.schemas_extended import (
    ComputerUseTemplateCreate, ComputerUseTemplateResponse, ComputerUseTemplateListResponse,
    ComputerUseScheduledTaskCreate, ComputerUseScheduledTaskResponse, ComputerUseScheduledTaskListResponse,
    ComputerUseAnnotationCreate, ComputerUseAnnotationResponse,
    ComputerUseBrowserProfileCreate, ComputerUseBrowserProfileResponse,
    ComputerUseProxyConfigCreate, ComputerUseProxyConfigResponse,
    ComputerUseSessionShareCreate, ComputerUseSessionShareResponse,
    ComputerUseBatchJobCreate, ComputerUseBatchJobResponse,
    ComputerUseSessionTagCreate, ComputerUseSessionTagResponse,
    ComputerUseSessionBookmarkCreate, ComputerUseSessionBookmarkResponse,
    ComputerUseSessionNoteCreate, ComputerUseSessionNoteResponse,
    ComputerUseWebhookCreate, ComputerUseWebhookResponse,
    ComputerUseExportRequest, ComputerUseReplayResponse, ComputerUseReplayStep,
    ComputerUseAnalyticsSummary, ComputerUseSessionFilter,
    ComputerUseTemplateImport, ComputerUseBrowserProfileImport,
    ComputerUseProxyConfigImport, ComputerUseWebhookImport,
)
from app.domains.computer_use.services.pdf_service import PDFExportService
from app.domains.computer_use.services.webhook_service import WebhookService

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()
pdf_service = PDFExportService()
webhook_service = WebhookService()


# ========== Templates ==========

@router.post("/templates", response_model=ComputerUseTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: ComputerUseTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    template = ComputerUseTemplate(
        user_id=current_user.id,
        business_id=data.business_id if hasattr(data, 'business_id') else None,
        name=data.name,
        description=data.description,
        task_description=data.task_description,
        start_url=data.start_url,
        tags=data.tags,
        is_public=data.is_public,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/templates", response_model=ComputerUseTemplateListResponse)
async def list_templates(
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(ComputerUseTemplate).where(
        and_(
            ComputerUseTemplate.user_id == current_user.id,
            ComputerUseTemplate.is_public == False
        ) if not search else and_(
            ComputerUseTemplate.user_id == current_user.id,
            ComputerUseTemplate.is_public == False,
            ComputerUseTemplate.name.ilike(f"%{search}%")
        )
    ).order_by(desc(ComputerUseTemplate.created_at))

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).where(ComputerUseTemplate.user_id == current_user.id)
    )
    total = count_result.scalar()

    return ComputerUseTemplateListResponse(
        items=[ComputerUseTemplateResponse.model_validate(t) for t in items],
        total=total,
    )


@router.post("/templates/{template_id}/use")
async def use_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseTemplate).where(
            ComputerUseTemplate.id == template_id,
            ComputerUseTemplate.user_id == current_user.id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    template.usage_count += 1
    await db.commit()

    # Return data to create a session
    return {
        "task_description": template.task_description,
        "start_url": template.start_url,
    }


# ========== Scheduled Tasks ==========

@router.post("/scheduled-tasks", response_model=ComputerUseScheduledTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_task(
    data: ComputerUseScheduledTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = ComputerUseScheduledTask(
        user_id=current_user.id,
        name=data.name,
        task_description=data.task_description,
        start_url=data.start_url,
        cron_expression=data.cron_expression,
        timezone=data.timezone,
        provider=data.provider,
        max_steps=data.max_steps,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/scheduled-tasks", response_model=ComputerUseScheduledTaskListResponse)
async def list_scheduled_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseScheduledTask)
        .where(ComputerUseScheduledTask.user_id == current_user.id)
        .order_by(desc(ComputerUseScheduledTask.created_at))
    )
    items = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).where(ComputerUseScheduledTask.user_id == current_user.id)
    )
    return ComputerUseScheduledTaskListResponse(
        items=[ComputerUseScheduledTaskResponse.model_validate(t) for t in items],
        total=count_result.scalar(),
    )


# ========== Annotations ==========

@router.post("/sessions/{session_id}/annotations", response_model=ComputerUseAnnotationResponse, status_code=status.HTTP_201_CREATED)
async def create_annotation(
    session_id: UUID,
    data: ComputerUseAnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    annotation = ComputerUseAnnotation(
        session_id=session_id,
        step_number=data.step_number,
        user_id=current_user.id,
        content=data.content,
        x_coordinate=data.x_coordinate,
        y_coordinate=data.y_coordinate,
        color=data.color,
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)
    return annotation


@router.get("/sessions/{session_id}/annotations", response_model=list[ComputerUseAnnotationResponse])
async def list_annotations(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    result = await db.execute(
        select(ComputerUseAnnotation)
        .where(ComputerUseAnnotation.session_id == session_id)
        .order_by(ComputerUseAnnotation.step_number, ComputerUseAnnotation.created_at)
    )
    annotations = result.scalars().all()
    return [ComputerUseAnnotationResponse.model_validate(a) for a in annotations]


# ========== Browser Profiles ==========

@router.post("/browser-profiles", response_model=ComputerUseBrowserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_browser_profile(
    data: ComputerUseBrowserProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if data.is_default:
        await db.execute(
            select(ComputerUseBrowserProfile).where(
                ComputerUseBrowserProfile.user_id == current_user.id,
                ComputerUseBrowserProfile.is_default == True,
            )
        )
        # Would unset other defaults here

    profile = ComputerUseBrowserProfile(
        user_id=current_user.id,
        name=data.name,
        viewport_width=data.viewport_width,
        viewport_height=data.viewport_height,
        user_agent=data.user_agent,
        locale=data.locale,
        timezone_id=data.timezone_id,
        cookies=data.cookies,
        local_storage=data.local_storage,
        geolocation=data.geolocation,
        is_default=data.is_default,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/browser-profiles", response_model=list[ComputerUseBrowserProfileResponse])
async def list_browser_profiles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseBrowserProfile)
        .where(ComputerUseBrowserProfile.user_id == current_user.id)
        .order_by(desc(ComputerUseBrowserProfile.is_default), desc(ComputerUseBrowserProfile.created_at))
    )
    profiles = result.scalars().all()
    return [ComputerUseBrowserProfileResponse.model_validate(p) for p in profiles]


# ========== Proxy Configs ==========

@router.post("/proxy-configs", response_model=ComputerUseProxyConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_proxy_config(
    data: ComputerUseProxyConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from app.core.encryption import encrypt_value
    password_encrypted = encrypt_value(data.password) if data.password else None

    proxy = ComputerUseProxyConfig(
        user_id=current_user.id,
        name=data.name,
        proxy_type=data.proxy_type,
        host=data.host,
        port=data.port,
        username=data.username,
        password_encrypted=password_encrypted,
        rotation_url=data.rotation_url,
    )
    db.add(proxy)
    await db.commit()
    await db.refresh(proxy)
    return proxy


@router.get("/proxy-configs", response_model=list[ComputerUseProxyConfigResponse])
async def list_proxy_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseProxyConfig)
        .where(ComputerUseProxyConfig.user_id == current_user.id)
        .order_by(desc(ComputerUseProxyConfig.created_at))
    )
    configs = result.scalars().all()
    return [ComputerUseProxyConfigResponse.model_validate(c) for c in configs]


# ========== Session Sharing ==========

@router.post("/sessions/{session_id}/shares", response_model=ComputerUseSessionShareResponse, status_code=status.HTTP_201_CREATED)
async def share_session(
    session_id: UUID,
    data: ComputerUseSessionShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_days) if data.expires_days else None

    share = ComputerUseSessionShare(
        session_id=session_id,
        shared_by_user_id=current_user.id,
        shared_with_user_id=data.shared_with_user_id,
        shared_with_email=data.shared_with_email,
        permission=data.permission,
        token=token,
        expires_at=expires_at,
    )
    db.add(share)
    await db.commit()
    await db.refresh(share)
    return share


@router.get("/sessions/{session_id}/shares", response_model=list[ComputerUseSessionShareResponse])
async def list_session_shares(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSessionShare)
        .where(ComputerUseSessionShare.session_id == session_id)
        .where(ComputerUseSessionShare.shared_by_user_id == current_user.id)
        .order_by(desc(ComputerUseSessionShare.created_at))
    )
    shares = result.scalars().all()
    return [ComputerUseSessionShareResponse.model_validate(s) for s in shares]


@router.get("/shared-sessions/{token}")
async def get_shared_session(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ComputerUseSessionShare).where(
            ComputerUseSessionShare.token == token,
            ComputerUseSessionShare.is_active == True,
        )
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="Enlace no válido")
    if share.expires_at and share.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Enlace expirado")

    session_result = await db.execute(
        select(ComputerUseSession).where(ComputerUseSession.id == share.session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    return {
        "session": session,
        "permission": share.permission,
    }


# ========== Batch Jobs ==========

@router.post("/batch-jobs", response_model=ComputerUseBatchJobResponse, status_code=status.HTTP_201_CREATED)
async def create_batch_job(
    data: ComputerUseBatchJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = ComputerUseBatchJob(
        user_id=current_user.id,
        name=data.name,
        task_description=data.task_description,
        urls=data.urls,
        provider=data.provider,
        max_steps_per_url=data.max_steps_per_url,
        concurrency=data.concurrency,
        total_count=len(data.urls),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/batch-jobs", response_model=list[ComputerUseBatchJobResponse])
async def list_batch_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseBatchJob)
        .where(ComputerUseBatchJob.user_id == current_user.id)
        .order_by(desc(ComputerUseBatchJob.created_at))
    )
    jobs = result.scalars().all()
    return [ComputerUseBatchJobResponse.model_validate(j) for j in jobs]


# ========== Session Tags ==========

@router.post("/sessions/{session_id}/tags", response_model=ComputerUseSessionTagResponse, status_code=status.HTTP_201_CREATED)
async def add_session_tag(
    session_id: UUID,
    data: ComputerUseSessionTagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    tag = ComputerUseSessionTag(
        session_id=session_id,
        tag=data.tag.lower().strip(),
        color=data.color,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.get("/sessions/{session_id}/tags", response_model=list[ComputerUseSessionTagResponse])
async def list_session_tags(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    result = await db.execute(
        select(ComputerUseSessionTag)
        .where(ComputerUseSessionTag.session_id == session_id)
        .order_by(ComputerUseSessionTag.tag)
    )
    tags = result.scalars().all()
    return [ComputerUseSessionTagResponse.model_validate(t) for t in tags]


@router.get("/tags/search")
async def search_sessions_by_tag(
    tag: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession)
        .join(ComputerUseSessionTag)
        .where(
            ComputerUseSession.user_id == current_user.id,
            ComputerUseSessionTag.tag == tag.lower().strip(),
        )
        .order_by(desc(ComputerUseSession.created_at))
    )
    sessions = result.scalars().all()
    return sessions


# ========== Bookmarks ==========

@router.post("/sessions/{session_id}/bookmarks", response_model=ComputerUseSessionBookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    session_id: UUID,
    data: ComputerUseSessionBookmarkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    from app.domains.computer_use.models_extended import ComputerUseSessionBookmark
    bookmark = ComputerUseSessionBookmark(
        session_id=session_id,
        step_number=data.step_number,
        user_id=current_user.id,
        label=data.label,
        color=data.color,
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    return bookmark


@router.get("/sessions/{session_id}/bookmarks", response_model=list[ComputerUseSessionBookmarkResponse])
async def list_bookmarks(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    from app.domains.computer_use.models_extended import ComputerUseSessionBookmark
    result = await db.execute(
        select(ComputerUseSessionBookmark)
        .where(ComputerUseSessionBookmark.session_id == session_id)
        .order_by(ComputerUseSessionBookmark.step_number)
    )
    bookmarks = result.scalars().all()
    return [ComputerUseSessionBookmarkResponse.model_validate(b) for b in bookmarks]


# ========== Clone Session ==========

@router.post("/sessions/{session_id}/clone")
async def clone_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Clona una sesión completada como punto de partida."""
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    new_session = ComputerUseSession(
        user_id=current_user.id,
        business_id=original.business_id,
        task_description=original.task_description,
        status="pending",
        current_url=original.current_url,
        browser_type=original.browser_type,
        total_steps=0,
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return {
        "original_session_id": session_id,
        "new_session_id": new_session.id,
        "message": "Sesión clonada. Iniciala para continuar desde el mismo punto.",
    }


# ========== Mobile Presets ==========

@router.get("/mobile-presets")
async def list_mobile_presets():
    """Lista los presets de emulación móvil disponibles."""
    from app.domains.computer_use.services.mobile_presets import list_presets, MOBILE_PRESETS
    return {
        "presets": [
            {"id": k, "name": v["name"], "viewport": {"width": v["viewport_width"], "height": v["viewport_height"]}}
            for k, v in MOBILE_PRESETS.items()
        ]
    }


# ========== Import/Export Config ==========

@router.post("/config/export")
async def export_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Exporta toda la configuración de Computer Use del usuario."""
    config = {
        "templates": [],
        "profiles": [],
        "proxies": [],
        "webhooks": [],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

    # Templates
    result = await db.execute(
        select(ComputerUseTemplate).where(ComputerUseTemplate.user_id == current_user.id)
    )
    for t in result.scalars().all():
        config["templates"].append({
            "name": t.name,
            "description": t.description,
            "task_description": t.task_description,
            "start_url": t.start_url,
            "tags": t.tags,
        })

    # Profiles
    result = await db.execute(
        select(ComputerUseBrowserProfile).where(ComputerUseBrowserProfile.user_id == current_user.id)
    )
    for p in result.scalars().all():
        config["profiles"].append({
            "name": p.name,
            "viewport_width": p.viewport_width,
            "viewport_height": p.viewport_height,
            "user_agent": p.user_agent,
            "locale": p.locale,
            "timezone_id": p.timezone_id,
            "cookies": p.cookies,
            "local_storage": p.local_storage,
        })

    # Proxies (sin contraseñas)
    result = await db.execute(
        select(ComputerUseProxyConfig).where(ComputerUseProxyConfig.user_id == current_user.id)
    )
    for px in result.scalars().all():
        config["proxies"].append({
            "name": px.name,
            "proxy_type": px.proxy_type,
            "host": px.host,
            "port": px.port,
            "username": px.username,
        })

    # Webhooks (sin secrets)
    result = await db.execute(
        select(ComputerUseWebhook).where(ComputerUseWebhook.user_id == current_user.id)
    )
    for w in result.scalars().all():
        config["webhooks"].append({
            "name": w.name,
            "url": w.url,
            "events": w.events,
        })

    return config


@router.post("/config/import")
async def import_config(
    config: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Importa configuración de Computer Use."""
    imported = {"templates": 0, "profiles": 0, "proxies": 0, "webhooks": 0}

    for tmpl in config.get("templates", []):
        validated = ComputerUseTemplateImport(**tmpl)
        t = ComputerUseTemplate(user_id=current_user.id, **validated.model_dump())
        db.add(t)
        imported["templates"] += 1

    for prof in config.get("profiles", []):
        validated = ComputerUseBrowserProfileImport(**prof)
        p = ComputerUseBrowserProfile(user_id=current_user.id, **validated.model_dump())
        db.add(p)
        imported["profiles"] += 1

    for proxy_data in config.get("proxies", []):
        validated = ComputerUseProxyConfigImport(**proxy_data)
        px = ComputerUseProxyConfig(user_id=current_user.id, **validated.model_dump())
        db.add(px)
        imported["proxies"] += 1

    for wh_data in config.get("webhooks", []):
        validated = ComputerUseWebhookImport(**wh_data)
        w = ComputerUseWebhook(user_id=current_user.id, **validated.model_dump())
        db.add(w)
        imported["webhooks"] += 1

    await db.commit()
    return {"imported": imported}


# ========== Session Notes ==========

@router.post("/sessions/{session_id}/notes")
async def create_session_note(
    session_id: UUID,
    data: ComputerUseSessionNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    from app.domains.computer_use.models_extended import ComputerUseSessionNote
    note = ComputerUseSessionNote(
        session_id=session_id,
        user_id=current_user.id,
        content=data.content,
        is_pinned=data.is_pinned,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/sessions/{session_id}/notes")
async def list_session_notes(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    from app.domains.computer_use.models_extended import ComputerUseSessionNote
    result = await db.execute(
        select(ComputerUseSessionNote)
        .where(ComputerUseSessionNote.session_id == session_id)
        .order_by(ComputerUseSessionNote.is_pinned.desc(), ComputerUseSessionNote.created_at.desc())
    )
    notes = result.scalars().all()
    return notes


# ========== Markdown Export ==========

@router.post("/sessions/{session_id}/export/markdown")
async def export_markdown(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    steps_result = await db.execute(
        select(ComputerUseStep)
        .where(ComputerUseStep.session_id == session_id)
        .order_by(ComputerUseStep.step_number)
    )
    steps = steps_result.scalars().all()
    steps_data = [{
        "step_number": s.step_number,
        "action_type": s.action_type,
        "action_params": s.action_params,
        "reason": s.llm_response,
        "execution_result": s.execution_result,
    } for s in steps]

    ann_result = await db.execute(
        select(ComputerUseAnnotation).where(ComputerUseAnnotation.session_id == session_id)
    )
    annotations = ann_result.scalars().all()
    ann_data = [{"step_number": a.step_number, "content": a.content} for a in annotations]

    from app.domains.computer_use.services.markdown_export import MarkdownExportService
    md_service = MarkdownExportService()
    markdown = md_service.export_session(
        {"task_description": session.task_description, "status": session.status, "total_steps": session.total_steps,
         "started_at": session.started_at, "completed_at": session.completed_at, "result_data": session.result_data},
        steps_data, ann_data,
    )

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=session_{session_id}.md"},
    )


# ========== Webhooks ==========

@router.post("/webhooks", response_model=ComputerUseWebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: ComputerUseWebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    webhook = ComputerUseWebhook(
        user_id=current_user.id,
        name=data.name,
        url=str(data.url),
        events=data.events,
        secret=data.secret,
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return webhook


@router.get("/webhooks", response_model=list[ComputerUseWebhookResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseWebhook)
        .where(ComputerUseWebhook.user_id == current_user.id)
        .order_by(desc(ComputerUseWebhook.created_at))
    )
    webhooks = result.scalars().all()
    return [ComputerUseWebhookResponse.model_validate(w) for w in webhooks]


# ========== Export ==========

@router.post("/sessions/{session_id}/export")
async def export_session(
    session_id: UUID,
    data: ComputerUseExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    # Get steps
    steps_result = await db.execute(
        select(ComputerUseStep)
        .where(ComputerUseStep.session_id == session_id)
        .order_by(ComputerUseStep.step_number)
    )
    steps = steps_result.scalars().all()
    steps_data = [{
        "step_number": s.step_number,
        "screenshot_path": s.screenshot_path,
        "action_type": s.action_type,
        "action_params": s.action_params,
        "reason": s.llm_response,
        "execution_result": s.execution_result,
        "execution_ms": s.execution_ms,
        "executed_at": s.executed_at,
    } for s in steps]

    # Get annotations
    ann_result = await db.execute(
        select(ComputerUseAnnotation).where(ComputerUseAnnotation.session_id == session_id)
    )
    annotations = ann_result.scalars().all()
    ann_data = [{
        "step_number": a.step_number,
        "content": a.content,
        "x_coordinate": a.x_coordinate,
        "y_coordinate": a.y_coordinate,
        "color": a.color,
    } for a in annotations]

    session_data = {
        "id": str(session.id),
        "task_description": session.task_description,
        "status": session.status,
        "total_steps": session.total_steps,
        "created_at": session.created_at,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "result_data": session.result_data,
        "error_message": session.error_message,
    }

    if data.format == "pdf":
        path = await pdf_service.export_session(
            session_id, session_data, steps_data, ann_data, data.include_screenshots
        )
        return FileResponse(path, media_type="application/pdf", filename=f"session_{session_id}.pdf")

    elif data.format == "csv":
        path = await pdf_service.export_csv(steps_data)
        return FileResponse(path, media_type="text/csv", filename=f"session_{session_id}_steps.csv")

    elif data.format == "json":
        path = await pdf_service.export_json(session_data, steps_data, ann_data)
        return FileResponse(path, media_type="application/json", filename=f"session_{session_id}.json")

    raise HTTPException(status_code=400, detail="Formato no soportado")


# ========== Replay ==========

@router.get("/sessions/{session_id}/replay", response_model=ComputerUseReplayResponse)
async def get_session_replay(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    steps_result = await db.execute(
        select(ComputerUseStep)
        .where(ComputerUseStep.session_id == session_id)
        .order_by(ComputerUseStep.step_number)
    )
    steps = steps_result.scalars().all()

    ann_result = await db.execute(
        select(ComputerUseAnnotation).where(ComputerUseAnnotation.session_id == session_id)
    )
    annotations = ann_result.scalars().all()

    replay_steps = []
    for step in steps:
        step_anns = [a for a in annotations if a.step_number == step.step_number]
        replay_steps.append(ComputerUseReplayStep(
            step_number=step.step_number,
            screenshot_url=f"/api/v1/computer-use/sessions/{session_id}/screenshots/{step.step_number}",
            action_type=step.action_type,
            action_params=step.action_params or {},
            reason=step.llm_response,
            execution_result=step.execution_result,
            execution_ms=step.execution_ms,
            annotations=[ComputerUseAnnotationResponse.model_validate(a) for a in step_anns],
        ))

    return ComputerUseReplayResponse(
        session_id=session_id,
        task_description=session.task_description,
        status=session.status,
        total_steps=session.total_steps,
        steps=replay_steps,
    )


# ========== Analytics ==========

@router.get("/analytics/summary", response_model=ComputerUseAnalyticsSummary)
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Total sessions
    total_result = await db.execute(
        select(func.count()).where(ComputerUseSession.user_id == current_user.id)
    )
    total = total_result.scalar() or 0

    # By status
    completed_result = await db.execute(
        select(func.count()).where(ComputerUseSession.user_id == current_user.id, ComputerUseSession.status == "completed")
    )
    completed = completed_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count()).where(ComputerUseSession.user_id == current_user.id, ComputerUseSession.status == "failed")
    )
    failed = failed_result.scalar() or 0

    stopped_result = await db.execute(
        select(func.count()).where(ComputerUseSession.user_id == current_user.id, ComputerUseSession.status == "stopped")
    )
    stopped = stopped_result.scalar() or 0

    # Avg steps
    avg_steps_result = await db.execute(
        select(func.avg(ComputerUseSession.total_steps)).where(ComputerUseSession.user_id == current_user.id)
    )
    avg_steps = avg_steps_result.scalar() or 0.0

    # Avg duration (for completed sessions)
    from sqlalchemy import extract
    avg_dur_result = await db.execute(
        select(func.avg(
            extract('epoch', ComputerUseSession.completed_at - ComputerUseSession.started_at)
        )).where(
            ComputerUseSession.user_id == current_user.id,
            ComputerUseSession.status == "completed",
            ComputerUseSession.started_at.isnot(None),
            ComputerUseSession.completed_at.isnot(None),
        )
    )
    avg_dur = avg_dur_result.scalar()

    # Most used provider
    provider_result = await db.execute(
        select(ComputerUseSession.provider_used, func.count())
        .where(ComputerUseSession.user_id == current_user.id, ComputerUseSession.provider_used.isnot(None))
        .group_by(ComputerUseSession.provider_used)
        .order_by(desc(func.count()))
        .limit(1)
    )
    provider_row = provider_result.first()
    most_provider = provider_row[0] if provider_row else None

    # Most common action
    action_result = await db.execute(
        select(ComputerUseStep.action_type, func.count())
        .join(ComputerUseSession)
        .where(ComputerUseSession.user_id == current_user.id)
        .group_by(ComputerUseStep.action_type)
        .order_by(desc(func.count()))
        .limit(1)
    )
    action_row = action_result.first()
    most_action = action_row[0] if action_row else None

    # Time-based counts
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    today_count = (await db.execute(
        select(func.count()).where(ComputerUseSession.user_id == current_user.id, ComputerUseSession.created_at >= today)
    )).scalar() or 0

    week_count = (await db.execute(
        select(func.count()).where(ComputerUseSession.user_id == current_user.id, ComputerUseSession.created_at >= week_start)
    )).scalar() or 0

    month_count = (await db.execute(
        select(func.count()).where(ComputerUseSession.user_id == current_user.id, ComputerUseSession.created_at >= month_start)
    )).scalar() or 0

    return ComputerUseAnalyticsSummary(
        total_sessions=total,
        completed_sessions=completed,
        failed_sessions=failed,
        stopped_sessions=stopped,
        avg_steps_per_session=round(float(avg_steps), 1),
        avg_session_duration_seconds=round(float(avg_dur), 1) if avg_dur else None,
        most_used_provider=most_provider,
        most_common_action=most_action,
        sessions_today=today_count,
        sessions_this_week=week_count,
        sessions_this_month=month_count,
    )


# ========== Multi-Session Grid ==========

@router.get("/active-sessions")
async def list_active_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista todas las sesiones activas del usuario para el grid de monitoreo."""
    result = await db.execute(
        select(ComputerUseSession)
        .where(
            ComputerUseSession.user_id == current_user.id,
            ComputerUseSession.status.in_(["pending", "running", "paused"]),
        )
        .order_by(desc(ComputerUseSession.created_at))
    )
    sessions = result.scalars().all()
    return {
        "items": [{
            "id": str(s.id),
            "task_description": s.task_description,
            "status": s.status,
            "current_url": s.current_url,
            "total_steps": s.total_steps,
            "browser_type": s.browser_type,
            "created_at": s.created_at,
            "started_at": s.started_at,
        } for s in sessions],
        "total": len(sessions),
    }


# ========== Browser Pool Stats ==========

@router.get("/browser-pool/stats")
async def get_browser_pool_stats(
    current_user: User = Depends(get_current_active_user),
):
    """Estadísticas del pool de navegadores."""
    from app.domains.computer_use.services.browser_pool import get_browser_pool
    pool = get_browser_pool()
    return pool.get_stats()
