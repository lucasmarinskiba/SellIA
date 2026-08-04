"""
Lead Management + Scoring API
Endpoints para CRUD leads y cálculo automático de score
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.models import Lead as LeadModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/leads", tags=["leads"])

# ============================================================
# MODELOS
# ============================================================
class LeadBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    pain_points: Optional[str] = None
    budget: Optional[float] = None
    timeline: Optional[str] = None  # "immediate", "3-6 months", "unknown"
    source: Optional[str] = None  # "linkedin", "website", "cold-email", "referral"
    notes: Optional[str] = None

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator('budget')
    @classmethod
    def budget_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Budget must be non-negative")
        return v

class Lead(LeadBase):
    id: int
    score: float
    status: str  # "new", "contacted", "qualified", "negotiating", "closed", "lost"
    created_at: datetime
    updated_at: datetime
    last_contacted: Optional[datetime] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    pain_points: Optional[str] = None
    budget: Optional[float] = None
    timeline: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    last_contacted: Optional[datetime] = None

class LeadScore(BaseModel):
    lead_id: int
    score: float
    score_breakdown: dict  # {completeness: 0.8, engagement: 0.7, fit: 0.9}
    reasons: List[str]
    scored_at: datetime


# ============================================================
# SCORING LOGIC
# ============================================================
def calculate_lead_score(lead_data: dict) -> dict:
    """
    Score lead en escala 0-100.
    Factores:
    - Completeness (10%): qué datos hay
    - Engagement (30%): si hizo click, opened email, etc
    - Fit (60%): si match con nuestro producto ideal
    """
    score_breakdown = {}

    # 1. COMPLETENESS (10%)
    completeness_fields = [
        'email', 'phone', 'company', 'job_title', 'industry', 'budget'
    ]
    filled = sum(1 for f in completeness_fields if lead_data.get(f))
    completeness_score = (filled / len(completeness_fields)) * 100
    score_breakdown['completeness'] = completeness_score / 100

    # 2. ENGAGEMENT (30%)
    engagement_score = 0
    if lead_data.get('status') == 'contacted':
        engagement_score += 50
    if lead_data.get('last_contacted'):
        engagement_score += 25
    if lead_data.get('source') in ['website', 'referral']:
        engagement_score += 25
    score_breakdown['engagement'] = engagement_score / 100

    # 3. FIT SCORE (60%) - Ideal Customer Profile
    fit_score = 0

    # Budget fit
    if lead_data.get('budget'):
        if lead_data['budget'] >= 5000:
            fit_score += 30
        elif lead_data['budget'] >= 1000:
            fit_score += 20
        else:
            fit_score += 10

    # Timeline fit
    if lead_data.get('timeline') == 'immediate':
        fit_score += 25
    elif lead_data.get('timeline') == '3-6 months':
        fit_score += 15

    # Industry fit (SaaS > Tech > Others)
    industry = (lead_data.get('industry') or '').lower()
    if any(x in industry for x in ['saas', 'software', 'tech', 'startup']):
        fit_score += 20
    else:
        fit_score += 5

    # Company size fit (SMB/Mid-market preferred)
    company = lead_data.get('company', '').lower()
    if any(x in company for x in ['inc', 'llc', 'corp']):
        fit_score += 5

    score_breakdown['fit'] = fit_score / 100

    # TOTAL SCORE
    total = (
        score_breakdown['completeness'] * 0.10 +
        score_breakdown['engagement'] * 0.30 +
        score_breakdown['fit'] * 0.60
    ) * 100

    return {
        'score': total,
        'breakdown': score_breakdown,
        'reasons': _generate_score_reasons(lead_data, score_breakdown)
    }

def _generate_score_reasons(lead_data: dict, breakdown: dict) -> List[str]:
    """Explicar por qué score."""
    reasons = []

    if breakdown['completeness'] > 0.8:
        reasons.append("✅ Datos completos")
    elif breakdown['completeness'] < 0.5:
        reasons.append("⚠️ Faltan datos clave")

    if breakdown['fit'] > 0.7:
        reasons.append("✅ Buen fit con perfil ideal")

    if lead_data.get('budget', 0) >= 5000:
        reasons.append(f"💰 Budget: ${lead_data['budget']:,.0f}")

    if lead_data.get('timeline') == 'immediate':
        reasons.append("⚡ Timeline inmediato")

    if not lead_data.get('last_contacted'):
        reasons.append("📞 Sin contacto aún")

    return reasons

# ============================================================
# ENDPOINTS
# ============================================================
@router.post("/", response_model=Lead)
async def create_lead(lead_data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Crear nuevo lead."""
    # Calcular score
    lead_dict = lead_data.dict()
    score_result = calculate_lead_score(lead_dict)

    # Crear lead en DB
    lead = LeadModel(
        name=lead_data.name,
        email=str(lead_data.email),
        phone=lead_data.phone,
        company=lead_data.company,
        industry=lead_data.industry,
        job_title=lead_data.job_title,
        pain_points=lead_data.pain_points,
        budget=lead_data.budget,
        timeline=lead_data.timeline,
        source=lead_data.source,
        notes=lead_data.notes,
        status='new',
        score=score_result['score'],
        score_breakdown=score_result['breakdown']
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    logger.info(f"Lead creado: {lead.email} (score: {lead.score:.1f})")
    return lead

@router.get("/", response_model=List[Lead])
async def list_leads(
    skip: int = 0,
    limit: int = 50,
    min_score: float = 0,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> list:
    """Listar leads con filtros (excluye deleted)."""
    query = select(LeadModel).where(
        LeadModel.score >= min_score,
        LeadModel.deleted_at == None  # Exclude soft-deleted
    )

    if status:
        query = query.where(LeadModel.status == status)

    query = query.order_by(LeadModel.score.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    leads = result.scalars().all()
    return leads

@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Obtener detalles de un lead."""
    result = await db.execute(select(LeadModel).where(LeadModel.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    return lead

@router.put("/{lead_id}", response_model=Lead)
async def update_lead(lead_id: int, lead_update: LeadUpdate, db: AsyncSession = Depends(get_db)):
    """Actualizar lead."""
    from sqlalchemy import select as sa_select
    # Row-level lock to prevent concurrent updates
    result = await db.execute(sa_select(LeadModel).where(LeadModel.id == lead_id).with_for_update())
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    update_data = lead_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(lead, field, value)

    lead.updated_at = datetime.now()

    # Recalcular score (atomically within transaction)
    try:
        lead_dict = {f.name: getattr(lead, f.name) for f in lead.__table__.columns}
        score_result = calculate_lead_score(lead_dict)
        lead.score = score_result['score']
        lead.score_breakdown = score_result['breakdown']

        await db.commit()
        await db.refresh(lead)
    except Exception as e:
        await db.rollback()
        logger.error(f"Score calculation failed: {e}")
        raise
    logger.info(f"Lead actualizado: {lead.email} (nuevo score: {lead.score:.1f})")

    return lead

@router.post("/{lead_id}/score", response_model=LeadScore)
async def rescore_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Recalcular score de un lead (útil después de engagement)."""
    result = await db.execute(select(LeadModel).where(LeadModel.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    lead_dict = {f.name: getattr(lead, f.name) for f in lead.__table__.columns}
    score_result = calculate_lead_score(lead_dict)
    lead.score = score_result['score']
    lead.score_breakdown = score_result['breakdown']

    await db.commit()
    await db.refresh(lead)

    return {
        'lead_id': lead_id,
        'score': score_result['score'],
        'score_breakdown': score_result['breakdown'],
        'reasons': score_result['reasons'],
        'scored_at': datetime.now()
    }

@router.post("/{lead_id}/contact")
async def mark_contacted(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Marcar lead como contactado."""
    result = await db.execute(select(LeadModel).where(LeadModel.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    lead.status = 'contacted'
    lead.last_contacted = datetime.now()
    lead.updated_at = datetime.now()

    # Recalcular score (atomically within transaction)
    try:
        lead_dict = {f.name: getattr(lead, f.name) for f in lead.__table__.columns}
        score_result = calculate_lead_score(lead_dict)
        lead.score = score_result['score']
        lead.score_breakdown = score_result['breakdown']

        await db.commit()
        await db.refresh(lead)
    except Exception as e:
        await db.rollback()
        logger.error(f"Score calculation failed: {e}")
        raise

    return lead

@router.delete("/{lead_id}")
async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Soft delete a lead (mark as deleted, don't remove data)."""
    result = await db.execute(select(LeadModel).where(LeadModel.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    lead.deleted_at = datetime.now()
    await db.commit()
    logger.info(f"Lead {lead_id} soft deleted")
    return {"status": "deleted", "lead_id": lead_id}

@router.get("/stats/summary")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Resumen de leads (solo activos)."""
    # Only count non-deleted leads
    result = await db.execute(select(LeadModel).where(LeadModel.deleted_at == None))
    leads_list = result.scalars().all()

    statuses = ['new', 'contacted', 'qualified', 'negotiating', 'closed', 'lost']

    return {
        'total': len(leads_list),
        'by_status': {
            st: len([l for l in leads_list if l.status == st])
            for st in statuses
        },
        'avg_score': sum(l.score for l in leads_list) / len(leads_list) if leads_list else 0,
        'high_quality': len([l for l in leads_list if l.score >= 70]),
    }
