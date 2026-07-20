"""Lead Generator — Find + Enrich + Score prospects automatically.

Fase 11: Encuentra leads en web → enriquece data → segmenta por fit.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LeadSource(str, Enum):
    """Fuentes de leads."""
    LINKEDIN = "linkedin"
    WEBSITE = "website"
    DIRECTORY = "directory"
    API = "api"
    IMPORT = "import"


class LeadQuality(str, Enum):
    """Calidad de lead."""
    HOT = "hot"  # High fit + high intent
    WARM = "warm"  # Medium fit
    COLD = "cold"  # Low fit, high volume


@dataclass
class Lead:
    """Lead/prospect."""
    lead_id: str
    name: str
    email: str
    phone: Optional[str]
    company: str
    title: str
    industry: str
    company_size: str

    # Data enriquecida
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    budget_estimate: Optional[float] = None

    # Scoring
    fit_score: float = 0.0  # 0-1
    intent_score: float = 0.0  # 0-1
    quality: LeadQuality = LeadQuality.COLD

    # Tracking
    source: LeadSource = LeadSource.IMPORT
    created_at: datetime = None
    last_contacted: Optional[datetime] = None
    contacted_count: int = 0
    responded: bool = False

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "title": self.title,
            "industry": self.industry,
            "company_size": self.company_size,
            "fit_score": self.fit_score,
            "intent_score": self.intent_score,
            "quality": self.quality.value,
            "source": self.source.value,
            "created_at": self.created_at.isoformat(),
            "responded": self.responded,
        }


class LeadGenerator:
    """Genera leads desde múltiples fuentes."""

    def __init__(self):
        self.logger = logger
        self.leads: Dict[str, Lead] = {}

    async def import_leads(
        self,
        leads_data: List[Dict[str, Any]],
        source: LeadSource = LeadSource.IMPORT,
    ) -> List[Lead]:
        """Importa leads desde CSV/API/etc."""
        try:
            imported = []

            for i, lead_data in enumerate(leads_data):
                lead_id = f"lead_{source.value}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}"

                lead = Lead(
                    lead_id=lead_id,
                    name=lead_data.get("name", "Unknown"),
                    email=lead_data.get("email", ""),
                    phone=lead_data.get("phone"),
                    company=lead_data.get("company", ""),
                    title=lead_data.get("title", ""),
                    industry=lead_data.get("industry", ""),
                    company_size=lead_data.get("company_size", ""),
                    source=source,
                )

                self.leads[lead_id] = lead
                imported.append(lead)

            self.logger.info(f"Imported {len(imported)} leads from {source.value}")

            return imported

        except Exception as e:
            self.logger.error(f"Error importing leads: {e}")
            return []

    async def enrich_lead(
        self,
        lead: Lead,
    ) -> Lead:
        """Enriquece lead con datos adicionales."""
        try:
            # Mock enrichment (en prod: usar APIs como Hunter, RocketReach, Apollo)
            if "@" not in lead.email and lead.email:
                # Intentar generar email
                domain = self._guess_company_domain(lead.company)
                lead.email = f"{lead.name.split()[0].lower()}.{lead.name.split()[-1].lower()}@{domain}"

            # Estimar budget basado en company size
            if lead.company_size:
                size_map = {
                    "1-10": 10000,
                    "11-50": 50000,
                    "51-200": 200000,
                    "201-500": 500000,
                    "500+": 1000000,
                }
                lead.budget_estimate = size_map.get(lead.company_size, 50000)

            # LinkedIn URL
            if not lead.linkedin_url:
                lead.linkedin_url = f"https://linkedin.com/in/{lead.name.replace(' ', '-').lower()}"

            self.logger.info(f"Enriched lead: {lead.email}")

            return lead

        except Exception as e:
            self.logger.error(f"Error enriching lead: {e}")
            return lead

    async def score_lead(
        self,
        lead: Lead,
        target_industry: Optional[str] = None,
        target_company_size: Optional[str] = None,
    ) -> Lead:
        """Calcula fit score + quality."""
        try:
            fit_score = 0.0
            intent_score = 0.0

            # Fit: ¿es el cliente ideal?
            if target_industry and lead.industry and target_industry.lower() in lead.industry.lower():
                fit_score += 0.3

            if target_company_size and lead.company_size == target_company_size:
                fit_score += 0.3

            if lead.budget_estimate and lead.budget_estimate >= 50000:
                fit_score += 0.2

            if "@" in lead.email and lead.email.count("@") == 1:
                fit_score += 0.2

            # Intent: ¿está interesado?
            # (En prod: basado en website visits, email opens, etc)
            intent_score = 0.5  # Default 50%

            lead.fit_score = min(fit_score, 1.0)
            lead.intent_score = intent_score

            # Determinar quality
            combined_score = (lead.fit_score + lead.intent_score) / 2

            if combined_score >= 0.7:
                lead.quality = LeadQuality.HOT
            elif combined_score >= 0.4:
                lead.quality = LeadQuality.WARM
            else:
                lead.quality = LeadQuality.COLD

            self.logger.info(f"Scored lead {lead.email}: fit={lead.fit_score:.1%}, quality={lead.quality.value}")

            return lead

        except Exception as e:
            self.logger.error(f"Error scoring lead: {e}")
            return lead

    async def get_leads_by_quality(
        self,
        quality: LeadQuality,
        limit: int = 10,
    ) -> List[Lead]:
        """Obtiene leads por calidad."""
        leads = [l for l in self.leads.values() if l.quality == quality]
        leads.sort(key=lambda l: (l.fit_score + l.intent_score) / 2, reverse=True)

        return leads[:limit]

    async def get_next_to_contact(self, limit: int = 5) -> List[Lead]:
        """Obtiene próximos leads a contactar (HOT primero)."""
        # Priorizar: HOT no contactados → WARM → COLD
        all_leads = list(self.leads.values())

        # Sort by: quality, contacted_count, last_contacted
        all_leads.sort(key=lambda l: (
            0 if l.quality == LeadQuality.HOT else (1 if l.quality == LeadQuality.WARM else 2),
            l.contacted_count,
            l.last_contacted or datetime.min,
        ))

        return all_leads[:limit]

    def _guess_company_domain(self, company: str) -> str:
        """Adivina dominio empresa."""
        # Simplificar nombre
        domain = company.lower()
        domain = domain.replace(" ", "").replace("inc.", "").replace("llc", "")

        return f"{domain}.com"


def get_lead_generator() -> LeadGenerator:
    return LeadGenerator()
