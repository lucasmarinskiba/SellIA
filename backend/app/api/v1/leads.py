"""
Lead Management + Scoring API
Endpoints para CRUD leads y cálculo automático de score
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/leads", tags=["leads"])

# ============================================================
# MODELOS
# ============================================================
class LeadBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    pain_points: Optional[str] = None
    budget: Optional[float] = None
    timeline: Optional[str] = None  # "immediate", "3-6 months", "unknown"
    source: Optional[str] = None  # "linkedin", "website", "cold-email", "referral"
    notes: Optional[str] = None

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
    email: Optional[str] = None
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
# IN-MEMORY STORAGE (Reemplazar con DB después)
# ============================================================
leads_db = {}
next_lead_id = 1
lead_scores = {}

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
async def create_lead(lead_data: LeadCreate) -> dict:
    """Crear nuevo lead."""
    global next_lead_id

    lead_dict = lead_data.dict()
    lead_dict['id'] = next_lead_id
    lead_dict['status'] = 'new'
    lead_dict['created_at'] = datetime.now()
    lead_dict['updated_at'] = datetime.now()
    lead_dict['last_contacted'] = None

    # Calcular score inicial
    score_result = calculate_lead_score(lead_dict)
    lead_dict['score'] = score_result['score']

    leads_db[next_lead_id] = lead_dict
    lead_scores[next_lead_id] = score_result

    logger.info(f"Lead creado: {lead_dict['email']} (score: {lead_dict['score']:.1f})")
    next_lead_id += 1

    return lead_dict

@router.get("/", response_model=List[Lead])
async def list_leads(
    skip: int = 0,
    limit: int = 50,
    min_score: float = 0,
    status: Optional[str] = None
) -> list:
    """Listar leads con filtros."""
    leads_list = list(leads_db.values())

    # Filtrar por score
    leads_list = [l for l in leads_list if l['score'] >= min_score]

    # Filtrar por status
    if status:
        leads_list = [l for l in leads_list if l['status'] == status]

    # Ordenar por score descendente
    leads_list = sorted(leads_list, key=lambda x: x['score'], reverse=True)

    return leads_list[skip:skip+limit]

@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: int) -> dict:
    """Obtener detalles de un lead."""
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    return leads_db[lead_id]

@router.put("/{lead_id}", response_model=Lead)
async def update_lead(lead_id: int, lead_update: LeadUpdate) -> dict:
    """Actualizar lead."""
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    lead = leads_db[lead_id]
    update_data = lead_update.dict(exclude_unset=True)

    lead.update(update_data)
    lead['updated_at'] = datetime.now()

    # Recalcular score
    score_result = calculate_lead_score(lead)
    lead['score'] = score_result['score']
    lead_scores[lead_id] = score_result

    logger.info(f"Lead actualizado: {lead['email']} (nuevo score: {lead['score']:.1f})")

    return lead

@router.post("/{lead_id}/score", response_model=LeadScore)
async def rescore_lead(lead_id: int) -> dict:
    """Recalcular score de un lead (útil después de engagement)."""
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    lead = leads_db[lead_id]
    score_result = calculate_lead_score(lead)
    lead['score'] = score_result['score']
    lead_scores[lead_id] = score_result

    return {
        'lead_id': lead_id,
        'score': score_result['score'],
        'score_breakdown': score_result['breakdown'],
        'reasons': score_result['reasons'],
        'scored_at': datetime.now()
    }

@router.post("/{lead_id}/contact")
async def mark_contacted(lead_id: int) -> dict:
    """Marcar lead como contactado."""
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    lead = leads_db[lead_id]
    lead['status'] = 'contacted'
    lead['last_contacted'] = datetime.now()
    lead['updated_at'] = datetime.now()

    # Recalcular score (engagement sube)
    score_result = calculate_lead_score(lead)
    lead['score'] = score_result['score']
    lead_scores[lead_id] = score_result

    return lead

@router.get("/stats/summary")
async def get_stats():
    """Resumen de leads."""
    leads_list = list(leads_db.values())

    return {
        'total': len(leads_list),
        'by_status': {
            status: len([l for l in leads_list if l['status'] == status])
            for status in ['new', 'contacted', 'qualified', 'negotiating', 'closed', 'lost']
        },
        'avg_score': sum(l['score'] for l in leads_list) / len(leads_list) if leads_list else 0,
        'high_quality': len([l for l in leads_list if l['score'] >= 70]),
    }
