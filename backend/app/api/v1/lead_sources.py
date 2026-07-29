"""
Lead Sources + Prospecting
- LinkedIn scraper (mock + ready for real)
- Website form integration
- Manual lead import
- Referral tracking
- Lead source analytics
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/lead-sources", tags=["lead-sources"])

# ============================================================
# ENUMS
# ============================================================
class SourceType(str, Enum):
    LINKEDIN = "linkedin"
    WEBSITE = "website"
    MANUAL = "manual"
    REFERRAL = "referral"
    EMAIL = "email"
    COLD_OUTREACH = "cold_outreach"

class SourceStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    INACTIVE = "inactive"

# ============================================================
# MODELOS
# ============================================================
class LinkedInConfig(BaseModel):
    # Para integración real con LinkedIn API
    search_keywords: List[str]  # ["CTO", "VP Sales", "Founder"]
    search_title: List[str]  # ["Chief Technology Officer", ...]
    company_keywords: Optional[List[str]] = None  # ["SaaS", "Tech", ...]
    min_connections: int = 500
    filter_country: Optional[str] = None

class WebsiteFormConfig(BaseModel):
    form_endpoint: str  # URL donde recibir submissions
    form_fields: List[str]  # ["name", "email", "company", "message"]
    auto_workflow_id: Optional[int] = None  # Auto-enroll en workflow

class LeadSourceBase(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: SourceType
    auto_workflow_id: Optional[int] = None  # Auto-enroll nuevo lead en este workflow
    industry_filter: Optional[str] = None
    config: dict  # LinkedInConfig, WebsiteFormConfig, etc.

class LeadSource(LeadSourceBase):
    id: int
    status: SourceStatus
    leads_generated: int
    created_at: datetime
    updated_at: datetime
    last_fetch: Optional[datetime] = None

class LeadSourceCreate(LeadSourceBase):
    pass

class LeadSourceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[SourceStatus] = None
    config: Optional[dict] = None
    auto_workflow_id: Optional[int] = None

class LinkedInSearchResult(BaseModel):
    name: str
    title: str
    company: str
    location: str
    profile_url: str
    email: Optional[str] = None
    linkedin_url: str
    connections: int

class WebsiteFormSubmission(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    message: Optional[str] = None
    form_source: str  # URL/form_id

class LeadSourceAnalytics(BaseModel):
    source_id: int
    source_name: str
    source_type: SourceType
    total_leads: int
    this_month: int
    this_week: int
    avg_score: float
    converted_count: int
    conversion_rate: float

# ============================================================
# IN-MEMORY STORAGE
# ============================================================
lead_sources_db = {}
next_source_id = 1

# Mock LinkedIn results (para testing)
MOCK_LINKEDIN_RESULTS = [
    LinkedInSearchResult(
        name="Sarah Johnson",
        title="VP Sales",
        company="TechCorp",
        location="San Francisco, CA",
        profile_url="https://linkedin.com/in/sarahjohnson",
        email="sarah@techcorp.com",
        linkedin_url="https://linkedin.com/in/sarahjohnson",
        connections=750
    ),
    LinkedInSearchResult(
        name="Mike Chen",
        title="CTO",
        company="StartupAI",
        location="San Francisco, CA",
        profile_url="https://linkedin.com/in/mikechen",
        email="mike@startupia.com",
        linkedin_url="https://linkedin.com/in/mikechen",
        connections=620
    ),
    LinkedInSearchResult(
        name="Jennifer Davis",
        title="Founder & CEO",
        company="SaaS Innovations",
        location="New York, NY",
        profile_url="https://linkedin.com/in/jenniferdavis",
        email="jennifer@saasinno.com",
        linkedin_url="https://linkedin.com/in/jenniferdavis",
        connections=1200
    ),
]

# Predefined lead sources
PREDEFINED_SOURCES = {
    "linkedin_saas_sales_leaders": {
        "name": "LinkedIn - SaaS Sales Leaders",
        "description": "Busca VP Sales + Sales Directors en SaaS companies",
        "source_type": SourceType.LINKEDIN,
        "config": {
            "search_keywords": ["VP Sales", "Sales Director", "Sales Manager"],
            "search_title": ["VP Sales", "Sales Director", "Director of Sales"],
            "company_keywords": ["SaaS", "Software", "Tech"],
            "min_connections": 300,
            "filter_country": "US"
        }
    },
    "linkedin_tech_founders": {
        "name": "LinkedIn - Tech Founders",
        "description": "Busca Founders y CTOs de startups tech",
        "source_type": SourceType.LINKEDIN,
        "config": {
            "search_keywords": ["Founder", "CTO", "Chief Technology Officer"],
            "search_title": ["Founder", "Co-Founder", "CTO"],
            "company_keywords": ["Startup", "Tech", "AI"],
            "min_connections": 200,
            "filter_country": None
        }
    }
}

# ============================================================
# FUNCIONES
# ============================================================
def mock_linkedin_search(config: dict) -> List[LinkedInSearchResult]:
    """Mock LinkedIn search (v2: integrar con LinkedIn API)."""
    logger.info(f"[MOCK] LinkedIn search: {config}")
    return MOCK_LINKEDIN_RESULTS

def create_lead_from_linkedin(result: LinkedInSearchResult, source_id: int) -> dict:
    """Convertir LinkedIn result a lead."""
    return {
        "name": result.name,
        "email": result.email or f"{result.name.lower().replace(' ', '')}@linkedin.com",
        "company": result.company,
        "job_title": result.title,
        "industry": "SaaS",  # Extract from company keywords
        "phone": None,
        "pain_points": None,
        "budget": None,
        "timeline": None,
        "source": "linkedin",
        "notes": f"LinkedIn profile: {result.linkedin_url}\nConnections: {result.connections}"
    }

# ============================================================
# ENDPOINTS
# ============================================================
@router.post("/", response_model=LeadSource)
async def create_lead_source(source_data: LeadSourceCreate) -> dict:
    """Crear fuente de leads."""
    global next_source_id

    source_dict = source_data.dict()
    source_dict['id'] = next_source_id
    source_dict['status'] = SourceStatus.ACTIVE
    source_dict['leads_generated'] = 0
    source_dict['created_at'] = datetime.now()
    source_dict['updated_at'] = datetime.now()
    source_dict['last_fetch'] = None

    lead_sources_db[next_source_id] = source_dict
    logger.info(f"Lead source creada: {source_dict['name']} (id: {next_source_id})")
    next_source_id += 1

    return source_dict

@router.get("/", response_model=List[LeadSource])
async def list_lead_sources(status: Optional[SourceStatus] = None) -> list:
    """Listar fuentes de leads."""
    sources = list(lead_sources_db.values())

    if status:
        sources = [s for s in sources if s['status'] == status]

    return sources

@router.get("/{source_id}", response_model=LeadSource)
async def get_lead_source(source_id: int) -> dict:
    """Obtener detalles de fuente."""
    if source_id not in lead_sources_db:
        raise HTTPException(status_code=404, detail="Lead source no encontrada")
    return lead_sources_db[source_id]

@router.put("/{source_id}", response_model=LeadSource)
async def update_lead_source(source_id: int, source_update: LeadSourceUpdate) -> dict:
    """Actualizar fuente."""
    if source_id not in lead_sources_db:
        raise HTTPException(status_code=404, detail="Lead source no encontrada")

    source = lead_sources_db[source_id]
    update_data = source_update.dict(exclude_unset=True)

    source.update(update_data)
    source['updated_at'] = datetime.now()

    logger.info(f"Lead source actualizada: {source_id}")
    return source

@router.post("/{source_id}/activate")
async def activate_source(source_id: int) -> dict:
    """Activar fuente."""
    if source_id not in lead_sources_db:
        raise HTTPException(status_code=404, detail="Lead source no encontrada")

    source = lead_sources_db[source_id]
    source['status'] = SourceStatus.ACTIVE
    source['updated_at'] = datetime.now()

    logger.info(f"Lead source activada: {source_id}")
    return source

@router.post("/{source_id}/pause")
async def pause_source(source_id: int) -> dict:
    """Pausar fuente."""
    if source_id not in lead_sources_db:
        raise HTTPException(status_code=404, detail="Lead source no encontrada")

    source = lead_sources_db[source_id]
    source['status'] = SourceStatus.PAUSED
    source['updated_at'] = datetime.now()

    logger.info(f"Lead source pausada: {source_id}")
    return source

@router.post("/{source_id}/fetch-leads")
async def fetch_leads_from_source(source_id: int) -> dict:
    """Ejecutar scraping/fetch de leads desde fuente."""
    if source_id not in lead_sources_db:
        raise HTTPException(status_code=404, detail="Lead source no encontrada")

    source = lead_sources_db[source_id]

    if source['source_type'] == SourceType.LINKEDIN:
        # Mock LinkedIn search
        linkedin_results = mock_linkedin_search(source['config'])

        # Convertir a leads (en prod: crear via /api/v1/leads)
        leads_data = [create_lead_from_linkedin(r, source_id) for r in linkedin_results]

        source['leads_generated'] += len(leads_data)
        source['last_fetch'] = datetime.now()

        return {
            "source_id": source_id,
            "source_type": source['source_type'],
            "leads_found": len(leads_data),
            "leads": leads_data,
            "message": f"Found {len(leads_data)} leads. Enroll in workflow to start outreach."
        }
    else:
        raise HTTPException(status_code=400, detail="Fetch not supported for this source type")

@router.post("/website/submit-form")
async def handle_website_form_submission(submission: WebsiteFormSubmission) -> dict:
    """Recibir lead desde website form."""
    # En prod: crear lead via /api/v1/leads, enroll en workflow

    logger.info(f"Website form submission: {submission.email} from {submission.form_source}")

    return {
        "status": "received",
        "email": submission.email,
        "message": "Lead received. Will be enrolled in nurture workflow.",
        "timestamp": datetime.now()
    }

@router.post("/referral/submit")
async def handle_referral(
    referrer_name: str,
    referrer_email: str,
    referred_name: str,
    referred_email: str,
    referred_company: Optional[str] = None
) -> dict:
    """Recibir referral de lead."""
    logger.info(f"Referral: {referrer_email} referred {referred_email}")

    return {
        "status": "received",
        "referred_email": referred_email,
        "referrer": referrer_email,
        "message": "Referral recorded. Lead will be marked as high priority.",
        "timestamp": datetime.now()
    }

@router.get("/{source_id}/analytics", response_model=LeadSourceAnalytics)
async def get_source_analytics(source_id: int) -> dict:
    """Analytics de fuente de leads."""
    if source_id not in lead_sources_db:
        raise HTTPException(status_code=404, detail="Lead source no encontrada")

    source = lead_sources_db[source_id]

    return {
        "source_id": source_id,
        "source_name": source['name'],
        "source_type": source['source_type'],
        "total_leads": source['leads_generated'],
        "this_month": source['leads_generated'],  # Mock
        "this_week": source['leads_generated'] // 4,  # Mock
        "avg_score": 65.0,  # Mock
        "converted_count": source['leads_generated'] // 5,  # Mock
        "conversion_rate": 0.20  # 20% mock rate
    }

@router.post("/templates/predefined/{template_name}")
async def create_from_predefined(template_name: str) -> dict:
    """Crear lead source desde template."""
    if template_name not in PREDEFINED_SOURCES:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    template = PREDEFINED_SOURCES[template_name]
    source_data = LeadSourceCreate(**template)

    return await create_lead_source(source_data)

@router.get("/templates/predefined")
async def list_predefined_templates() -> dict:
    """Listar templates predefinidos."""
    return {
        name: {
            "name": data["name"],
            "description": data["description"],
            "source_type": data["source_type"]
        }
        for name, data in PREDEFINED_SOURCES.items()
    }
