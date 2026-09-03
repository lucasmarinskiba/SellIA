"""Brand Transformation API — specialist agents (diagnosis, positioning, brand
identity, business model, FOMO engine, GTM, restructuring) plus the staged
Transformation Program orchestrator and standing automations.

Mounted at /api/v1/businesses/{business_id}/brand-transformation
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.brand_transformation import knowledge as K
from app.domains.brand_transformation.orchestrator import TransformationOrchestrator
from app.domains.brand_transformation.schemas import (
    AutomationIn,
    AutomationOut,
    DeployCampaignsIn,
    BrandIdentityOut,
    BusinessModelOut,
    BusinessProfileIn,
    DiagnosisIn,
    DiagnosisOut,
    FOMOPlaybookOut,
    GTMPlanOut,
    PositioningOut,
    ProgramCreateIn,
    ProgramOut,
    RestructuringOut,
    StageInfoOut,
    StageResultOut,
    StageRunIn,
)
from app.domains.brand_transformation.service import (
    BrandIdentityAgent,
    BusinessModelAgent,
    DiagnosisAgent,
    FOMOEngineAgent,
    GoToMarketAgent,
    PositioningAgent,
    RestructuringAgent,
)
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/brand-transformation", tags=["Brand Transformation"])


# --------------------------------------------------------------- reference

@router.get("/health")
async def domain_health(business_id: UUID, current_user: User = Depends(get_current_user)):
    """Whether the agents run on real AI or templated fallback.

    `llm_available` false => every agent returns deterministic fallback output
    (`generated_by == "fallback"`). Set ANTHROPIC_API_KEY to enable AI.
    """
    from app.domains.brand_transformation.service import _MODEL, llm_available

    ok = llm_available()
    return {
        "llm_available": ok,
        "model": _MODEL,
        "agents_mode": "ai" if ok else "fallback",
        "note": None if ok else "No Anthropic API key configured — agents return templated fallback.",
    }


@router.get("/stages", response_model=list[StageInfoOut])
async def list_stages(business_id: UUID, current_user: User = Depends(get_current_user)):
    """The 8 etapas of the transformation program."""
    return [StageInfoOut(**s) for s in K.TRANSFORMATION_STAGES]


@router.get("/knowledge/fomo-levers")
async def fomo_levers(business_id: UUID, current_user: User = Depends(get_current_user)):
    return K.FOMO_LEVERS


@router.get("/knowledge/brand-origins")
async def brand_origins(business_id: UUID, current_user: User = Depends(get_current_user)):
    return K.BRAND_ORIGIN_PLAYBOOKS


@router.get("/knowledge/frameworks")
async def frameworks(business_id: UUID, current_user: User = Depends(get_current_user)):
    return K.FRAMEWORKS


# --------------------------------------------------------------- single agents

@router.post("/agents/diagnosis", response_model=DiagnosisOut)
async def run_diagnosis(
    business_id: UUID,
    body: DiagnosisIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await DiagnosisAgent(db).run(business_id, body.model_dump())


@router.get("/agents/diagnosis/latest", response_model=DiagnosisOut | None)
async def latest_diagnosis(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await DiagnosisAgent(db).latest(business_id)


@router.get("/agents/diagnosis/history", response_model=list[DiagnosisOut])
async def diagnosis_history(
    business_id: UUID,
    limit: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Score trend over time — newest first. Feeds the rediagnosis automation."""
    return await DiagnosisAgent(db).history(business_id, min(limit, 50))


@router.post("/agents/positioning", response_model=PositioningOut)
async def run_positioning(
    business_id: UUID,
    body: StageRunIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (body.profile or _require_profile()).model_dump()
    return await PositioningAgent(db).run(business_id, profile, extra=body.extra_instructions)


@router.post("/agents/brand-identity", response_model=BrandIdentityOut)
async def run_brand_identity(
    business_id: UUID,
    body: StageRunIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (body.profile or _require_profile()).model_dump()
    return await BrandIdentityAgent(db).run(business_id, profile, extra=body.extra_instructions)


@router.post("/agents/business-model", response_model=BusinessModelOut)
async def run_business_model(
    business_id: UUID,
    body: StageRunIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (body.profile or _require_profile()).model_dump()
    return await BusinessModelAgent(db).run(business_id, profile, extra=body.extra_instructions)


@router.post("/agents/fomo-engine", response_model=FOMOPlaybookOut)
async def run_fomo_engine(
    business_id: UUID,
    body: StageRunIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (body.profile or _require_profile()).model_dump()
    return await FOMOEngineAgent(db).run(business_id, profile, extra=body.extra_instructions)


async def _resolve_playbook(db: AsyncSession, business_id: UUID, playbook_id: UUID | None):
    agent = FOMOEngineAgent(db)
    pb = await agent.by_id(business_id, playbook_id) if playbook_id else await agent.latest(business_id)
    if not pb:
        raise HTTPException(status_code=404, detail="no FOMO playbook found — run POST /agents/fomo-engine first")
    return pb


@router.get("/agents/fomo-engine/campaign-preview")
async def fomo_campaign_preview(
    business_id: UUID,
    playbook_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Map the latest (or a given) FOMO playbook's mechanisms to proposed
    on-site `fomo` campaigns. Read-only — nothing is created."""
    from app.domains.brand_transformation.fomo_bridge import FOMOBridge

    pb = await _resolve_playbook(db, business_id, playbook_id)
    return await FOMOBridge(db).preview(pb)


@router.post("/agents/fomo-engine/deploy-campaigns")
async def fomo_deploy_campaigns(
    business_id: UUID,
    body: DeployCampaignsIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create real `fomo` campaigns from a FOMO playbook's mechanisms. Campaigns
    are created as drafts unless `activate` is true. `dry_run` returns the plan
    only. Campaign links are written back onto the playbook (`deployed_campaigns`)."""
    from app.domains.brand_transformation.fomo_bridge import FOMOBridge

    pb = await _resolve_playbook(db, business_id, body.playbook_id)
    return await FOMOBridge(db).deploy(
        pb,
        owner_user_id=current_user.id,
        activate=body.activate,
        levers=body.levers or None,
        dry_run=body.dry_run,
    )


@router.post("/agents/gtm", response_model=GTMPlanOut)
async def run_gtm(
    business_id: UUID,
    body: StageRunIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (body.profile or _require_profile()).model_dump()
    return await GoToMarketAgent(db).run(business_id, profile, extra=body.extra_instructions)


@router.post("/agents/restructuring", response_model=RestructuringOut)
async def run_restructuring(
    business_id: UUID,
    body: StageRunIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (body.profile or _require_profile()).model_dump()
    return await RestructuringAgent(db).run(business_id, profile, extra=body.extra_instructions)


def _require_profile() -> BusinessProfileIn:
    raise HTTPException(status_code=422, detail="profile is required for this agent")


# --------------------------------------------------------------- program

@router.post("/programs", response_model=ProgramOut)
async def create_program(
    business_id: UUID,
    body: ProgramCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await TransformationOrchestrator(db).create_program(
        business_id, body.name, body.profile.model_dump()
    )


@router.get("/programs", response_model=list[ProgramOut])
async def list_programs(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await TransformationOrchestrator(db).list_programs(business_id)


@router.get("/programs/{program_id}", response_model=ProgramOut)
async def get_program(
    business_id: UUID,
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prog = await TransformationOrchestrator(db).get_program(program_id)
    if not prog or prog.business_id != business_id:
        raise HTTPException(status_code=404, detail="program not found")
    return prog


@router.get("/programs/{program_id}/roadmap")
async def get_program_roadmap(
    business_id: UUID,
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Etapa 7 output — roadmap + execution plan (dependency graph, decision
    gates, kill switches, leading-indicator dashboard). Run the `roadmap` stage
    first to populate it."""
    prog = await TransformationOrchestrator(db).get_program(program_id)
    if not prog or prog.business_id != business_id:
        raise HTTPException(status_code=404, detail="program not found")
    return {
        "program_id": prog.id,
        "status": prog.status,
        "completed_stages": prog.completed_stages,
        "roadmap": prog.roadmap,
        "execution_plan": prog.execution_plan,
        "metrics_board_kpis": (prog.roadmap or {}).get("metrics_board"),
        "synthesized": "roadmap" in (prog.completed_stages or []),
    }


@router.post("/programs/{program_id}/stages/{stage_key}/run", response_model=StageResultOut)
async def run_program_stage(
    business_id: UUID,
    program_id: UUID,
    stage_key: str,
    body: StageRunIn | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orch = TransformationOrchestrator(db)
    prog = await orch.get_program(program_id)
    if not prog or prog.business_id != business_id:
        raise HTTPException(status_code=404, detail="program not found")
    profile = body.profile.model_dump() if body and body.profile else None
    extra = body.extra_instructions if body else None
    return await orch.run_stage(prog, stage_key, profile, extra)


@router.post("/programs/{program_id}/run-all", response_model=list[StageResultOut])
async def run_program_all(
    business_id: UUID,
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orch = TransformationOrchestrator(db)
    prog = await orch.get_program(program_id)
    if not prog or prog.business_id != business_id:
        raise HTTPException(status_code=404, detail="program not found")
    return await orch.run_all(prog)


@router.post("/programs/{program_id}/coherence-audit")
async def program_coherence_audit(
    business_id: UUID,
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cross-stage consistency check: do the 7 artifacts actually agree?
    Catches internal drift (three different enemies, an offer that can't fund
    the loop, FOMO that fails the brand's own ethics review, a roadmap that
    violates its own dependencies)."""
    orch = TransformationOrchestrator(db)
    prog = await orch.get_program(program_id)
    if not prog or prog.business_id != business_id:
        raise HTTPException(status_code=404, detail="program not found")
    return await orch.coherence_audit(prog)


# --------------------------------------------------------------- automations

@router.post("/automations", response_model=AutomationOut)
async def create_automation(
    business_id: UUID,
    body: AutomationIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await TransformationOrchestrator(db).create_automation(
        business_id, body.automation_type, body.schedule, body.config
    )


@router.get("/automations", response_model=list[AutomationOut])
async def list_automations(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await TransformationOrchestrator(db).list_automations(business_id)


@router.post("/automations/{automation_id}/run")
async def run_automation(
    business_id: UUID,
    automation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    from app.domains.brand_transformation.models import BrandAutomation

    r = await db.execute(select(BrandAutomation).where(BrandAutomation.id == automation_id))
    automation = r.scalar_one_or_none()
    if not automation or automation.business_id != business_id:
        raise HTTPException(status_code=404, detail="automation not found")
    return await TransformationOrchestrator(db).run_automation(automation)
