"""Automations API Router"""

from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.automations.models import (
    Workflow, EmailTemplate, EmailSequence, SequenceStep, ChatbotRule,
    SequenceSubscription, SequenceEmailLog, WorkflowVariant,
    GeneratedContent, ContentCalendar,
)
from app.domains.subscriptions.models import Subscription
from app.domains.automations.schemas import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse,
    EmailSequenceCreate, EmailSequenceResponse, EmailSequenceUpdate,
    SequenceAnalytics,
    ChatbotRuleCreate, ChatbotRuleUpdate, ChatbotRuleResponse,
    WorkflowVariantCreate, WorkflowVariantUpdate, WorkflowVariantResponse,
    WorkflowABTestResult,
    GeneratedContentResponse, ContentCalendarResponse, ContentCalendarCreate,
    ContentGenerationRequest, ContentGenerationResponse,
)
from app.domains.automations.seed import seed_automations

router = APIRouter()


# ========== Workflows ==========

@router.get("/workflows", response_model=list[WorkflowResponse])
async def list_workflows(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Workflow).where(
            Workflow.business_id == business_id,
            Workflow.is_active == True,
        ).order_by(desc(Workflow.created_at))
    )
    return result.scalars().all()


@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    wf = Workflow(**data.model_dump())
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return wf


@router.patch("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(wf, field, value)
    await db.commit()
    await db.refresh(wf)
    return wf


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    wf.is_active = False
    await db.commit()
    return {"message": "Workflow eliminado"}


# ========== Email Templates ==========

@router.get("/email-templates", response_model=list[EmailTemplateResponse])
async def list_templates(
    business_id: UUID,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(EmailTemplate).where(
        EmailTemplate.business_id == business_id,
        EmailTemplate.is_active == True,
    )
    if category:
        query = query.where(EmailTemplate.category == category)
    result = await db.execute(query.order_by(desc(EmailTemplate.created_at)))
    return result.scalars().all()


@router.post("/email-templates", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tmpl = EmailTemplate(**data.model_dump())
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return tmpl


@router.patch("/email-templates/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: UUID,
    data: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)
    await db.commit()
    await db.refresh(tmpl)
    return tmpl


@router.delete("/email-templates/{template_id}")
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    tmpl.is_active = False
    await db.commit()
    return {"message": "Template eliminado"}


# ========== Email Sequences ==========

@router.get("/email-sequences", response_model=list[EmailSequenceResponse])
async def list_sequences(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(EmailSequence).where(
            EmailSequence.business_id == business_id,
            EmailSequence.is_active == True,
        ).order_by(desc(EmailSequence.created_at))
    )
    return result.scalars().all()


@router.post("/email-sequences", response_model=EmailSequenceResponse, status_code=status.HTTP_201_CREATED)
async def create_sequence(
    data: EmailSequenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    seq_data = data.model_dump(exclude={"steps"})
    seq = EmailSequence(**seq_data)
    db.add(seq)
    await db.flush()

    for step_data in data.steps:
        step = SequenceStep(sequence_id=seq.id, **step_data.model_dump())
        db.add(step)

    await db.commit()
    await db.refresh(seq)
    return seq


@router.get("/email-sequences/{sequence_id}", response_model=EmailSequenceResponse)
async def get_sequence(
    sequence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(EmailSequence).where(EmailSequence.id == sequence_id)
    )
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Secuencia no encontrada")
    return seq


@router.patch("/email-sequences/{sequence_id}", response_model=EmailSequenceResponse)
async def update_sequence(
    sequence_id: UUID,
    data: EmailSequenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(EmailSequence).where(EmailSequence.id == sequence_id))
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Secuencia no encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(seq, field, value)
    await db.commit()
    await db.refresh(seq)
    return seq


@router.get("/email-sequences/{sequence_id}/analytics", response_model=SequenceAnalytics)
async def get_sequence_analytics(
    sequence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(EmailSequence).where(EmailSequence.id == sequence_id)
    )
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Secuencia no encontrada")

    # Total subscribers
    sub_result = await db.execute(
        select(func.count(SequenceSubscription.id))
        .where(SequenceSubscription.sequence_id == sequence_id)
    )
    total_subscribers = sub_result.scalar() or 0

    # Total sent
    sent_result = await db.execute(
        select(func.count(SequenceEmailLog.id))
        .where(SequenceEmailLog.sequence_id == sequence_id, SequenceEmailLog.status == "sent")
    )
    total_sent = sent_result.scalar() or 0

    # Total opens
    open_result = await db.execute(
        select(func.count(SequenceEmailLog.id))
        .where(SequenceEmailLog.sequence_id == sequence_id, SequenceEmailLog.opened_at != None)
    )
    total_opens = open_result.scalar() or 0

    # Total clicks
    click_result = await db.execute(
        select(func.count(SequenceEmailLog.id))
        .where(SequenceEmailLog.sequence_id == sequence_id, SequenceEmailLog.clicked_at != None)
    )
    total_clicks = click_result.scalar() or 0

    open_rate = round((total_opens / total_sent * 100), 2) if total_sent > 0 else 0.0
    click_rate = round((total_clicks / total_sent * 100), 2) if total_sent > 0 else 0.0

    # Sent trend by day
    trend_result = await db.execute(
        select(func.date(SequenceEmailLog.sent_at), func.count(SequenceEmailLog.id))
        .where(SequenceEmailLog.sequence_id == sequence_id, SequenceEmailLog.sent_at != None)
        .group_by(func.date(SequenceEmailLog.sent_at))
        .order_by(func.date(SequenceEmailLog.sent_at))
    )
    sent_trend = [
        {"date": str(row[0]), "count": row[1]}
        for row in trend_result.all()
    ]

    return SequenceAnalytics(
        sequence_id=sequence_id,
        total_subscribers=total_subscribers,
        total_sent=total_sent,
        total_opens=total_opens,
        total_clicks=total_clicks,
        open_rate=open_rate,
        click_rate=click_rate,
        sent_trend=sent_trend,
    )


@router.delete("/email-sequences/{sequence_id}")
async def delete_sequence(
    sequence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(EmailSequence).where(EmailSequence.id == sequence_id))
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Secuencia no encontrada")
    seq.is_active = False
    await db.commit()
    return {"message": "Secuencia eliminada"}


# ========== Chatbot Rules ==========

@router.get("/chatbot-rules", response_model=list[ChatbotRuleResponse])
async def list_rules(
    business_id: UUID,
    intent: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(ChatbotRule).where(
        ChatbotRule.business_id == business_id,
        ChatbotRule.is_active == True,
    )
    if intent:
        query = query.where(ChatbotRule.intent == intent)
    result = await db.execute(query.order_by(desc(ChatbotRule.priority)))
    return result.scalars().all()


@router.post("/chatbot-rules", response_model=ChatbotRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: ChatbotRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rule = ChatbotRule(**data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.patch("/chatbot-rules/{rule_id}", response_model=ChatbotRuleResponse)
async def update_rule(
    rule_id: UUID,
    data: ChatbotRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(ChatbotRule).where(ChatbotRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/chatbot-rules/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(ChatbotRule).where(ChatbotRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    rule.is_active = False
    await db.commit()
    return {"message": "Regla eliminada"}


# ========== Execute Workflow ==========

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: UUID,
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Manually trigger a workflow execution."""
    from app.domains.automations.engine import WorkflowEngine

    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.business_id == business_id,
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")

    engine = WorkflowEngine(db)
    executions = await engine.process_trigger(
        trigger_type=workflow.trigger_type,
        business_id=business_id,
        trigger_data={"manual": True, "triggered_by": str(current_user.id)},
    )

    return {
        "message": "Workflow ejecutado",
        "executions": [{"id": str(e.id), "status": e.status} for e in executions],
    }


# ========== Seed Pre-built Automations ==========

@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_business_automations(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Seed pre-built workflows, templates, sequences and chatbot rules for a business."""
    try:
        await seed_automations(db, business_id)
        return {"message": "Automatizaciones predefinidas creadas correctamente"}
    except Exception:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Error seeding automations")
        raise HTTPException(status_code=500, detail="Internal server error")



# ========== Workflow Variants (A/B Testing) ==========

@router.post("/workflows/{workflow_id}/variants", response_model=WorkflowVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_variant(
    workflow_id: UUID,
    data: WorkflowVariantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new variant for A/B testing a workflow."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")

    variant = WorkflowVariant(
        workflow_id=workflow_id,
        business_id=workflow.business_id,
        variant_name=data.variant_name,
        traffic_split=data.traffic_split,
        actions=data.actions,
        is_control=data.is_control,
        is_active=data.is_active if data.is_active is not None else True,
    )
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return variant


@router.get("/workflows/{workflow_id}/variants", response_model=list[WorkflowVariantResponse])
async def list_workflow_variants(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all variants for a workflow."""
    result = await db.execute(
        select(WorkflowVariant)
        .where(WorkflowVariant.workflow_id == workflow_id)
        .order_by(WorkflowVariant.created_at)
    )
    return result.scalars().all()


@router.patch("/workflows/{workflow_id}/variants/{variant_id}", response_model=WorkflowVariantResponse)
async def update_workflow_variant(
    workflow_id: UUID,
    variant_id: UUID,
    data: WorkflowVariantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a variant's traffic split, actions, or active status."""
    variant = await db.get(WorkflowVariant, variant_id)
    if not variant or variant.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Variante no encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(variant, field, value)

    await db.commit()
    await db.refresh(variant)
    return variant


@router.delete("/workflows/{workflow_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_variant(
    workflow_id: UUID,
    variant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a variant. Cannot delete the control variant if other variants exist."""
    variant = await db.get(WorkflowVariant, variant_id)
    if not variant or variant.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Variante no encontrada")

    if variant.is_control:
        others = await db.execute(
            select(func.count(WorkflowVariant.id)).where(
                WorkflowVariant.workflow_id == workflow_id,
                WorkflowVariant.id != variant_id
            )
        )
        if others.scalar() > 0:
            raise HTTPException(status_code=400, detail="No se puede eliminar la variante control mientras existan otras variantes")

    await db.delete(variant)
    await db.commit()
    return None


@router.get("/workflows/{workflow_id}/ab-test-results")
async def get_ab_test_results(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Compare variant performance: executions, conversions, and rates."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")

    result = await db.execute(
        select(WorkflowVariant).where(WorkflowVariant.workflow_id == workflow_id)
    )
    variants = result.scalars().all()

    if not variants:
        return {"workflow_id": str(workflow_id), "variants": [], "winner": None}

    total_exec = sum(v.execution_count or 0 for v in variants)

    variant_stats = []
    best_rate = -1.0
    winner = None

    for v in variants:
        execs = v.execution_count or 0
        convs = v.conversion_count or 0
        rate = (convs / execs * 100) if execs > 0 else 0.0
        share = (execs / total_exec * 100) if total_exec > 0 else 0.0

        variant_stats.append({
            "id": str(v.id),
            "variant_name": v.variant_name,
            "is_control": v.is_control,
            "traffic_split": v.traffic_split,
            "execution_count": execs,
            "conversion_count": convs,
            "conversion_rate": round(rate, 2),
            "traffic_share": round(share, 2),
            "is_active": v.is_active,
        })

        if execs >= 10 and rate > best_rate:
            best_rate = rate
            winner = v.variant_name

    return {
        "workflow_id": str(workflow_id),
        "workflow_name": workflow.name,
        "total_executions": total_exec,
        "variants": variant_stats,
        "winner": winner,
        "recommendation": (
            f"La variante '{winner}' tiene la mejor tasa de conversión ({round(best_rate, 2)}%). "
            f"Considera aumentar su tráfico al 100%."
            if winner else "Se necesitan al menos 10 ejecuciones por variante para determinar un ganador."
        ),
    }


# ========== AI Content Generation ==========

@router.post("/content/generate", response_model=ContentGenerationResponse)
async def generate_content(
    data: ContentGenerationRequest,
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Genera contenido con IA (imagen, video, copy, carousel, thumbnail)."""
    from app.tasks.content_tasks import (
        generate_product_images_task,
        generate_video_clips_task,
        generate_product_copy_task,
        generate_carousel_task,
        generate_thumbnail_task,
    )

    task_dispatch = {
        "image": generate_product_images_task,
        "video": generate_video_clips_task,
        "copy": generate_product_copy_task,
        "carousel": generate_carousel_task,
        "thumbnail": generate_thumbnail_task,
    }

    task_func = task_dispatch.get(data.content_type)
    if not task_func:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de contenido no soportado: {data.content_type}. Usa: {list(task_dispatch.keys())}"
        )

    # Enqueue Celery task
    kwargs = {
        "business_id": str(business_id),
    }

    if data.catalog_item_id:
        kwargs["catalog_item_id"] = str(data.catalog_item_id)

    if data.content_type in ["image", "video", "copy"]:
        if not data.catalog_item_id:
            raise HTTPException(
                status_code=400,
                detail=f"catalog_item_id es requerido para content_type='{data.content_type}'"
            )

    if data.content_type == "thumbnail":
        kwargs["video_title"] = data.prompt_override or "Video"
        kwargs["video_description"] = data.purpose or ""

    if data.generation_config:
        # Merge specific configs
        for key, value in data.generation_config.items():
            kwargs[key] = value

    task = task_func.delay(**kwargs)

    return ContentGenerationResponse(
        task_id=task.id,
        status="queued",
        message=f"Tarea de generación de {data.content_type} encolada correctamente. Task ID: {task.id}",
    )


@router.get("/content", response_model=list[GeneratedContentResponse])
async def list_generated_content(
    business_id: UUID,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    agent_slug: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista contenido generado por IA para un negocio."""
    query = select(GeneratedContent).where(
        GeneratedContent.business_id == business_id
    ).order_by(desc(GeneratedContent.created_at))

    if content_type:
        query = query.where(GeneratedContent.content_type == content_type)
    if status:
        query = query.where(GeneratedContent.status == status)
    if agent_slug:
        query = query.where(GeneratedContent.agent_slug == agent_slug)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/content/{content_id}", response_model=GeneratedContentResponse)
async def get_generated_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene un contenido generado específico."""
    result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    return content


@router.patch("/content/{content_id}/approve")
async def approve_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Aprueba contenido generado para publicación."""
    result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")

    content.approval_status = "approved"
    content.reviewed_by = current_user.id
    content.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(content)

    return {"message": "Contenido aprobado", "content_id": str(content_id)}


@router.patch("/content/{content_id}/reject")
async def reject_content(
    content_id: UUID,
    feedback: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Rechaza contenido generado con feedback."""
    result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")

    content.approval_status = "rejected"
    content.reviewed_by = current_user.id
    content.reviewed_at = datetime.now(timezone.utc)
    if feedback:
        content.feedback_notes = feedback
    await db.commit()
    await db.refresh(content)

    return {"message": "Contenido rechazado", "content_id": str(content_id)}


# ========== Content Calendar ==========

@router.get("/calendar", response_model=list[ContentCalendarResponse])
async def list_calendar(
    business_id: UUID,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista publicaciones programadas en el calendario de contenido."""
    query = select(ContentCalendar).where(
        ContentCalendar.business_id == business_id
    ).order_by(desc(ContentCalendar.scheduled_at))

    if platform:
        query = query.where(ContentCalendar.platform == platform)
    if status:
        query = query.where(ContentCalendar.status == status)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/calendar", response_model=ContentCalendarResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_entry(
    data: ContentCalendarCreate,
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Crea una entrada en el calendario de contenido."""
    entry = ContentCalendar(business_id=business_id, **data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.patch("/calendar/{entry_id}", response_model=ContentCalendarResponse)
async def update_calendar_entry(
    entry_id: UUID,
    data: ContentCalendarCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Actualiza una entrada del calendario."""
    result = await db.execute(
        select(ContentCalendar).where(ContentCalendar.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/calendar/{entry_id}")
async def delete_calendar_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Elimina una entrada del calendario."""
    result = await db.execute(
        select(ContentCalendar).where(ContentCalendar.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    entry.status = "cancelled"
    await db.commit()
    return {"message": "Entrada cancelada"}


@router.post("/calendar/{entry_id}/publish")
async def publish_calendar_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Publica manualmente una entrada del calendario."""
    result = await db.execute(
        select(ContentCalendar).where(ContentCalendar.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    # TODO: Integrar con APIs de plataforma
    entry.status = "published"
    entry.published_at = datetime.now(timezone.utc)
    entry.published_by = current_user.id
    await db.commit()

    return {"message": "Publicación completada", "entry_id": str(entry_id)}


# ========== Content Tools & Pricing ==========

@router.get("/content/tools")
async def list_content_tools(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista herramientas de IA de contenido disponibles según el plan del negocio."""
    from app.integrations.content_generation.plan_tools import (
        get_tools_for_plan, TOOL_REGISTRY, get_plan_comparison
    )
    from app.integrations.content_generation.router import ContentGenerationRouter

    # Obtener plan del negocio
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()
    plan_tier = sub.plan.slug if sub and sub.plan else "free"

    allowed_slugs = get_tools_for_plan(plan_tier)
    tools = []
    router = ContentGenerationRouter()

    for slug in allowed_slugs:
        tool = TOOL_REGISTRY.get(slug)
        if not tool:
            continue
        provider = router.providers.get(tool.provider_module)
        is_ready = provider.is_available if provider else False
        tools.append({
            "slug": slug,
            "name": tool.name,
            "category": tool.category,
            "description": tool.description,
            "cost_tier": tool.cost_tier,
            "min_plan": tool.min_plan,
            "is_ready": is_ready,
            "fallback_tool": tool.fallback_tool,
        })

    return {
        "plan": plan_tier,
        "tool_count": len(tools),
        "tools": tools,
    }


@router.get("/content/tools/{tool_slug}")
async def get_tool_detail(
    tool_slug: str,
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene detalle de una herramienta específica."""
    from app.integrations.content_generation.plan_tools import (
        TOOL_REGISTRY, get_plan_upgrade_message, is_tool_allowed
    )
    from app.integrations.content_generation.router import ContentGenerationRouter

    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()
    plan_tier = sub.plan.slug if sub and sub.plan else "free"

    tool = TOOL_REGISTRY.get(tool_slug)
    if not tool:
        raise HTTPException(status_code=404, detail="Herramienta no encontrada")

    router = ContentGenerationRouter()
    provider = router.providers.get(tool.provider_module)
    pricing = provider.get_pricing_table() if provider else {}

    return {
        "slug": tool.slug,
        "name": tool.name,
        "category": tool.category,
        "description": tool.description,
        "cost_tier": tool.cost_tier,
        "min_plan": tool.min_plan,
        "is_allowed": is_tool_allowed(tool_slug, plan_tier),
        "is_ready": provider.is_available if provider else False,
        "pricing": pricing,
        "fallback_tool": tool.fallback_tool,
        "upgrade_message": get_plan_upgrade_message(tool_slug, plan_tier) if not is_tool_allowed(tool_slug, plan_tier) else None,
    }


@router.get("/content/pricing")
async def get_content_pricing(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Tabla de precios de herramientas de contenido según plan."""
    from app.integrations.content_generation.plan_tools import get_plan_comparison
    from app.integrations.content_generation.router import ContentGenerationRouter

    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()
    plan_tier = sub.plan.slug if sub and sub.plan else "free"

    router = ContentGenerationRouter()
    pricing = router.get_pricing_summary(plan_tier)
    comparison = get_plan_comparison()

    return {
        "current_plan": plan_tier,
        "pricing": pricing,
        "plan_comparison": comparison,
    }


@router.get("/content/usage")
async def get_content_usage(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Reporte de uso mensual de generación de contenido."""
    from app.integrations.content_generation.budget import BudgetController

    controller = BudgetController()
    report = await controller.get_usage_report(str(business_id))

    # Obtener stats de DB
    from datetime import timedelta
    month_ago = datetime.now(timezone.utc) - timedelta(days=30)

    result = await db.execute(
        select(GeneratedContent).where(
            and_(
                GeneratedContent.business_id == business_id,
                GeneratedContent.created_at >= month_ago,
            )
        )
    )
    contents = result.scalars().all()

    by_type = {}
    by_tool = {}
    total_cost = 0
    for c in contents:
        by_type[c.content_type] = by_type.get(c.content_type, 0) + 1
        by_tool[c.ai_model_used or "unknown"] = by_tool.get(c.ai_model_used or "unknown", 0) + 1
        total_cost += (c.generation_cost or 0) / 100

    return {
        "daily_report": report,
        "monthly_stats": {
            "total_generations": len(contents),
            "total_cost_usd": round(total_cost, 2),
            "by_type": by_type,
            "by_tool": by_tool,
        },
    }
