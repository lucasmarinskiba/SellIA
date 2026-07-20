"""SellIA Missions API

Endpoints para crear, ejecutar y monitorear misiones cross-plataforma.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.missions.services import MissionService
from app.domains.missions.schemas import (
    MissionCreate, MissionRead, MissionUpdate,
    MissionLaunchRequest, MissionApproveRequest,
    MissionStepUpdate, BusinessDiagnosticRead,
    DiagnosticRunRequest, DiagnosticRunResponse,
    PlaybookRead,
)
from app.domains.missions.shipping_assistant import ShippingConnectorAssistant
from app.domains.missions.ad_spend_assistant import AdSpendAssistant

router = APIRouter(prefix="/missions", tags=["SellIA Missions"])


def get_service(db: AsyncSession = Depends(get_db)) -> MissionService:
    return MissionService(db)


# ─── Misiones ──────────────────────────────────────────────────────────────────

@router.post("", response_model=MissionRead, status_code=status.HTTP_201_CREATED)
async def create_mission(
    data: MissionCreate,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Crear una misión personalizada."""
    return await service.create_custom(user.id, data)


@router.post("/from-playbook/{playbook_slug}", response_model=MissionRead, status_code=status.HTTP_201_CREATED)
async def create_mission_from_playbook(
    playbook_slug: str,
    request: MissionLaunchRequest,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Crear una misión a partir de un playbook."""
    return await service.create_from_playbook(
        user_id=user.id,
        playbook_slug=playbook_slug,
        business_id=request.business_id,
        auto_approve_low_impact=request.auto_approve_low_impact,
    )


@router.get("", response_model=List[MissionRead])
async def list_missions(
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Listar misiones del usuario autenticado."""
    return await service.list_by_user(user.id, status=status, category=category, limit=limit, offset=offset)


# ─── Diagnósticos ──────────────────────────────────────────────────────────────

@router.post("/diagnostics/run", response_model=DiagnosticRunResponse)
async def run_diagnostic(
    request: DiagnosticRunRequest,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Ejecutar diagnóstico completo del negocio."""
    metrics = request.business_id and {} or {}
    diagnostics = await service.run_diagnostic(user.id, request.business_id, metrics)

    critical_count = sum(1 for d in diagnostics if d.severity == "critical")
    warning_count = sum(1 for d in diagnostics if d.severity == "warning")
    info_count = sum(1 for d in diagnostics if d.severity == "info")

    from app.domains.missions.playbook_library import get_recommended_playbooks
    recommended = get_recommended_playbooks(diagnostics)

    return DiagnosticRunResponse(
        diagnostics=diagnostics,
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        recommended_missions=recommended,
    )


@router.get("/diagnostics/list", response_model=List[BusinessDiagnosticRead])
async def list_diagnostics(
    business_id: Optional[uuid.UUID] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Listar diagnósticos del usuario."""
    return await service.list_diagnostics(user.id, business_id=business_id, is_resolved=is_resolved)


@router.post("/diagnostics/{diagnostic_id}/resolve")
async def resolve_diagnostic(
    diagnostic_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Marcar un diagnóstico como resuelto."""
    success = await service.resolve_diagnostic(diagnostic_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    return {"success": True}


# ─── Playbooks ─────────────────────────────────────────────────────────────────

@router.get("/playbooks", response_model=List[PlaybookRead])
async def list_playbooks(
    category: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Listar playbooks disponibles."""
    return await service.list_playbooks(category)


@router.get("/playbooks/{slug}", response_model=PlaybookRead)
async def get_playbook_detail(
    slug: str,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Obtener detalle de un playbook."""
    playbook = await service.get_playbook(slug)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook no encontrado")
    return playbook


# ─── Shipping Assistant ────────────────────────────────────────────────────────

@router.post("/shipping/recommendations")
async def shipping_recommendations(
    request: dict,
    user: User = Depends(get_current_user),
):
    """Obtener recomendaciones de carriers según contexto."""
    assistant = ShippingConnectorAssistant()
    return assistant.get_carrier_recommendations(request)


@router.post("/shipping/setup-steps")
async def shipping_setup_steps(
    carrier: str,
    request: dict,
    user: User = Depends(get_current_user),
):
    """Obtener pasos de configuración para un carrier."""
    assistant = ShippingConnectorAssistant()
    return assistant.generate_setup_steps(carrier, request)


@router.post("/shipping/estimate-costs")
async def shipping_estimate_costs(
    request: dict,
    user: User = Depends(get_current_user),
):
    """Estimar costos de envío."""
    assistant = ShippingConnectorAssistant()
    return assistant.estimate_shipping_costs(
        request.get("origin"), request.get("destination"),
        request.get("weight"), request.get("dimensions")
    )


@router.get("/shipping/cross-border/{target_country}")
async def cross_border_requirements(
    target_country: str,
    user: User = Depends(get_current_user),
):
    """Obtener requisitos de cross-border."""
    assistant = ShippingConnectorAssistant()
    return assistant.get_cross_border_requirements(target_country)


# ─── Ad Spend Assistant ────────────────────────────────────────────────────────

@router.post("/ads/platform-recommendations")
async def ads_platform_recommendations(
    request: dict,
    user: User = Depends(get_current_user),
):
    """Recomendaciones de plataforma de ads según contexto y presupuesto."""
    assistant = AdSpendAssistant()
    return assistant.get_platform_recommendations(request, request.get("budget", 500))


@router.post("/ads/budget-allocation")
async def ads_budget_allocation(
    request: dict,
    user: User = Depends(get_current_user),
):
    """Distribución recomendada de presupuesto."""
    assistant = AdSpendAssistant()
    return assistant.generate_budget_allocation(
        request.get("monthly_budget", 500),
        request.get("business_type", "ecommerce"),
        request.get("goal", "sales")
    )


@router.post("/ads/campaign-steps")
async def ads_campaign_steps(
    request: dict,
    user: User = Depends(get_current_user),
):
    """Pasos para crear campaña en una plataforma."""
    assistant = AdSpendAssistant()
    return assistant.get_campaign_setup_steps(
        request.get("platform", "meta"),
        request.get("objective", "conversions")
    )


@router.post("/ads/estimate-cpa")
async def ads_estimate_cpa(
    request: dict,
    user: User = Depends(get_current_user),
):
    """Estimar CPA por plataforma y país."""
    assistant = AdSpendAssistant()
    return assistant.estimate_cpa(
        request.get("business_type", "ecommerce"),
        request.get("platform", "meta"),
        request.get("country", "AR")
    )


@router.post("/ads/creative-recommendations")
async def ads_creative_recommendations(
    request: dict,
    user: User = Depends(get_current_user),
):
    """Recomendaciones de creativos por plataforma."""
    assistant = AdSpendAssistant()
    return assistant.get_ad_creatives_recommendations(
        request.get("platform", "meta"),
        request.get("business_type", "ecommerce")
    )


# ─── Operaciones sobre misión específica ───────────────────────────────────────

@router.get("/{mission_id}", response_model=MissionRead)
async def get_mission(
    mission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Obtener detalle de una misión."""
    mission = await service.get(mission_id, user.id)
    if not mission:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    return mission


@router.patch("/{mission_id}", response_model=MissionRead)
async def update_mission(
    mission_id: uuid.UUID,
    data: MissionUpdate,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Actualizar una misión."""
    mission = await service.update(mission_id, user.id, data)
    if not mission:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    return mission


@router.post("/{mission_id}/approve", response_model=MissionRead)
async def approve_mission(
    mission_id: uuid.UUID,
    request: MissionApproveRequest,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Aprobar una misión propuesta."""
    mission = await service.approve(mission_id, user.id, approve_all_steps=request.approve_all_steps)
    if not mission:
        raise HTTPException(status_code=404, detail="Misión no encontrada o no puede ser aprobada")
    return mission


@router.post("/{mission_id}/start", response_model=MissionRead)
async def start_mission(
    mission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Iniciar una misión aprobada."""
    mission = await service.start(mission_id, user.id)
    if not mission:
        raise HTTPException(status_code=400, detail="Misión no encontrada o no está aprobada")
    return mission


@router.post("/{mission_id}/steps/{step_id}", response_model=MissionRead)
async def update_mission_step(
    mission_id: uuid.UUID,
    step_id: uuid.UUID,
    data: MissionStepUpdate,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Actualizar estado de un paso de la misión."""
    mission = await service.update_step(mission_id, step_id, user.id, data)
    if not mission:
        raise HTTPException(status_code=404, detail="Paso o misión no encontrada")
    return mission


@router.post("/{mission_id}/cancel", response_model=MissionRead)
async def cancel_mission(
    mission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Cancelar una misión en ejecución o aprobada."""
    mission = await service.get(mission_id, user.id)
    if not mission:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    if mission.status not in ("approved", "running", "proposed"):
        raise HTTPException(status_code=400, detail="La misión no puede ser cancelada en su estado actual")
    updated = await service.update(mission_id, user.id, MissionUpdate(status="cancelled"))
    if not updated:
        raise HTTPException(status_code=400, detail="No se pudo cancelar la misión")
    return updated


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mission(
    mission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: MissionService = Depends(get_service),
):
    """Eliminar una misión."""
    mission = await service.get(mission_id, user.id)
    if not mission:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    from sqlalchemy import delete
    from app.domains.missions.models import Mission as MissionModel
    await service.db.execute(delete(MissionModel).where(MissionModel.id == mission_id))
    await service.db.commit()
