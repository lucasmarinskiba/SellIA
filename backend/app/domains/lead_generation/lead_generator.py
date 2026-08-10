"""Phase 11: Multi-channel lead generation."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


class LeadSource(str, Enum):
    GOOGLE_MAPS = "google_maps"
    GOOGLE_SEARCH = "google_search"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"
    MARKETPLACE = "marketplace"
    EMAIL = "email"
    DIRECTORY = "directory"
    REFERRAL = "referral"
    COLD_OUTREACH = "cold_outreach"


class LeadQuality(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


@dataclass
class Lead:
    lead_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source: LeadSource = LeadSource.GOOGLE_SEARCH
    quality: LeadQuality = LeadQuality.WARM
    estimated_budget: Optional[float] = None
    estimated_timeline: Optional[str] = None
    contact_method: str = "email"
    raw_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    enriched: bool = False


class LeadGenerator:
    """Generate leads by business model"""

    def __init__(self):
        self.generated_count = 0

    def generate_leads(
        self, business_model: str, location: str = "", target_audience: str = "",
        limit: int = 100
    ) -> List[Lead]:
        """Generate leads based on business model"""

        logger.info(f"Generating {limit} leads for {business_model}")

        leads = []

        if business_model == "physical_store":
            leads = self._generate_local_store_leads(location, limit)
        elif business_model == "online_only":
            leads = self._generate_ecommerce_leads(target_audience, limit)
        elif business_model == "service_at_home":
            leads = self._generate_service_leads(location, limit)
        elif business_model == "b2b_consulting":
            leads = self._generate_b2b_leads(target_audience, limit)
        elif business_model == "global_ecommerce":
            leads = self._generate_global_leads(limit)
        else:
            leads = self._generate_generic_leads(limit)

        self.generated_count += len(leads)
        logger.info(f"Generated {len(leads)} leads total")
        return leads

    def _generate_local_store_leads(self, location: str, limit: int) -> List[Lead]:
        """Local store: Google Maps, local directories, neighborhood"""
        leads = []

        names = ["María García", "Juan López", "Carlos Mendez", "Ana Rodríguez",
                "Roberto Silva", "Laura Fernández", "Miguel Ángel", "Sofia Martínez"]
        emails = ["maria@email.com", "juan@email.com", "carlos@email.com", "ana@email.com"]

        for i in range(min(limit, 30)):
            lead = Lead(
                lead_id=f"local_{i}",
                name=random.choice(names),
                email=random.choice(emails),
                phone=f"+34 {random.randint(6,9)}{random.randint(10000000, 99999999)}",
                location=location or "Madrid",
                source=LeadSource.GOOGLE_MAPS,
                quality=LeadQuality.WARM if i < 10 else LeadQuality.COLD,
                estimated_budget=random.choice([500, 1000, 2000, 5000]),
                contact_method="whatsapp"
            )
            leads.append(lead)

        return leads

    def _generate_ecommerce_leads(self, category: str, limit: int) -> List[Lead]:
        """E-commerce: search keywords, marketplace, retargeting"""
        leads = []

        for i in range(min(limit, 50)):
            lead = Lead(
                lead_id=f"ecom_{i}",
                name=f"Buyer_{i}",
                email=f"customer_{i}@example.com",
                location="online",
                source=LeadSource.GOOGLE_SEARCH if i < 25 else LeadSource.MARKETPLACE,
                quality=LeadQuality.WARM if random.random() > 0.5 else LeadQuality.COLD,
                estimated_budget=random.choice([50, 100, 250, 500, 1000]),
                estimated_timeline="1-7 days",
                contact_method="email"
            )
            leads.append(lead)

        return leads

    def _generate_service_leads(self, location: str, limit: int) -> List[Lead]:
        """Service at home: Google Maps, directories, WhatsApp"""
        leads = []

        service_types = ["plomería", "electricidad", "limpieza", "pintura", "reparación"]

        for i in range(min(limit, 40)):
            lead = Lead(
                lead_id=f"service_{i}",
                name=f"Cliente_{i}",
                phone=f"+34 {random.randint(6,9)}{random.randint(10000000, 99999999)}",
                location=location or "Barcelona",
                source=random.choice([LeadSource.GOOGLE_MAPS, LeadSource.WHATSAPP,
                                     LeadSource.DIRECTORY]),
                quality=LeadQuality.HOT if i < 15 else LeadQuality.WARM,
                estimated_budget=random.choice([300, 500, 1000, 2000]),
                contact_method="whatsapp"
            )
            leads.append(lead)

        return leads

    def _generate_b2b_leads(self, industry: str, limit: int) -> List[Lead]:
        """B2B: LinkedIn, business directories, cold outreach"""
        leads = []

        companies = ["TechCorp SA", "Innovate SL", "Digital Solutions", "Cloud Enterprise",
                    "Business Systems", "Enterprise Plus", "Soluciones Empresariales"]
        roles = ["CEO", "CTO", "Manager", "Director", "Head of Operations"]

        for i in range(min(limit, 60)):
            lead = Lead(
                lead_id=f"b2b_{i}",
                name=f"{random.choice(roles)} - {random.choice(companies)}",
                email=f"contact_{i}@company.com",
                company=random.choice(companies),
                source=LeadSource.LINKEDIN if i < 30 else LeadSource.EMAIL,
                quality=LeadQuality.WARM if i < 20 else LeadQuality.COLD,
                estimated_budget=random.choice([5000, 10000, 25000, 50000]),
                estimated_timeline="30-90 days",
                contact_method="email"
            )
            leads.append(lead)

        return leads

    def _generate_global_leads(self, limit: int) -> List[Lead]:
        """Global e-commerce: international marketplaces"""
        leads = []

        countries = ["US", "UK", "Germany", "France", "Spain", "Mexico", "Brazil", "China"]

        for i in range(min(limit, 80)):
            lead = Lead(
                lead_id=f"global_{i}",
                name=f"International_Buyer_{i}",
                email=f"buyer_{i}@international.com",
                location=random.choice(countries),
                source=random.choice([LeadSource.MARKETPLACE, LeadSource.GOOGLE_SEARCH]),
                quality=LeadQuality.WARM,
                estimated_budget=random.choice([100, 500, 1000, 5000]),
                contact_method="email"
            )
            leads.append(lead)

        return leads

    def _generate_generic_leads(self, limit: int) -> List[Lead]:
        """Generic: mixed channels"""
        leads = []

        for i in range(min(limit, 50)):
            lead = Lead(
                lead_id=f"generic_{i}",
                name=f"Prospect_{i}",
                email=f"prospect_{i}@email.com",
                source=random.choice([LeadSource.EMAIL, LeadSource.GOOGLE_SEARCH,
                                     LeadSource.REFERRAL]),
                quality=LeadQuality.COLD,
                estimated_budget=random.choice([500, 1000, 2000]),
                contact_method="email"
            )
            leads.append(lead)

        return leads
