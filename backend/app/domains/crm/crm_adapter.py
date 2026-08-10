"""CRM Adapter - Unified interface for Salesforce, HubSpot, Pipedrive, custom data."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class CRMType(str, Enum):
    """Supported CRM platforms."""
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    CUSTOM = "custom"


@dataclass
class CRMLead:
    """Unified lead structure from any CRM."""
    id: str
    company_name: str
    contact_name: str
    email: str
    phone: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[int] = None  # employees
    annual_revenue: Optional[float] = None
    website: Optional[str] = None

    # Sales signals
    lead_score: Optional[float] = None  # 0-100
    source: Optional[str] = None  # "LinkedIn", "Inbound", "Referral"
    stage: Optional[str] = None  # "new", "qualified", "proposal", "negotiation"
    owner: Optional[str] = None

    # Engagement signals
    email_opens: Optional[int] = None
    email_clicks: Optional[int] = None
    page_views: Optional[int] = None
    demo_attended: Optional[bool] = False
    call_scheduled: Optional[bool] = False

    # Deal info
    estimated_value: Optional[float] = None  # $ amount
    close_date: Optional[str] = None  # ISO date
    budget: Optional[str] = None  # "50k-100k"

    # Custom fields
    custom_fields: Dict[str, Any] = None

    def dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "id": self.id,
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "email": self.email,
            "phone": self.phone,
            "industry": self.industry,
            "company_size": self.company_size,
            "annual_revenue": self.annual_revenue,
            "website": self.website,
            "lead_score": self.lead_score,
            "source": self.source,
            "stage": self.stage,
            "owner": self.owner,
            "email_opens": self.email_opens,
            "email_clicks": self.email_clicks,
            "page_views": self.page_views,
            "demo_attended": self.demo_attended,
            "call_scheduled": self.call_scheduled,
            "estimated_value": self.estimated_value,
            "close_date": self.close_date,
            "budget": self.budget,
            "custom_fields": self.custom_fields or {},
        }


class CRMAdapter(ABC):
    """Abstract CRM adapter interface."""

    crm_type: CRMType

    @abstractmethod
    async def fetch_lead(self, lead_id: str) -> Optional[CRMLead]:
        """Fetch single lead from CRM."""
        pass

    @abstractmethod
    async def fetch_leads(self, filters: Optional[Dict[str, Any]] = None) -> List[CRMLead]:
        """Fetch multiple leads from CRM."""
        pass

    @abstractmethod
    async def update_lead(self, lead_id: str, data: Dict[str, Any]) -> bool:
        """Update lead in CRM."""
        pass

    @abstractmethod
    async def create_activity(
        self, lead_id: str, activity_type: str, description: str
    ) -> bool:
        """Log activity (email, call, note) in CRM."""
        pass


class MockCRMAdapter(CRMAdapter):
    """Mock CRM adapter for testing (no external dependencies)."""

    crm_type = CRMType.CUSTOM

    def __init__(self):
        self.leads_db = self._init_sample_data()

    def _init_sample_data(self) -> Dict[str, CRMLead]:
        """Initialize sample CRM data for testing."""
        return {
            "lead_001": CRMLead(
                id="lead_001",
                company_name="TechCorp Inc",
                contact_name="John Doe",
                email="john@techcorp.com",
                phone="+1-555-0001",
                industry="Technology",
                company_size=250,
                annual_revenue=50_000_000,
                website="techcorp.com",
                lead_score=85,
                source="LinkedIn",
                stage="new",
                owner="sales@sellia.ai",
                email_opens=3,
                email_clicks=1,
                page_views=5,
                demo_attended=False,
                call_scheduled=False,
                estimated_value=75000,
                budget="50k-100k",
            ),
            "lead_002": CRMLead(
                id="lead_002",
                company_name="CloudSystems LLC",
                contact_name="Sarah Smith",
                email="sarah@cloudsystems.com",
                phone="+1-555-0002",
                industry="Cloud",
                company_size=45,
                annual_revenue=8_000_000,
                website="cloudsystems.com",
                lead_score=72,
                source="Inbound",
                stage="qualified",
                owner="sales@sellia.ai",
                email_opens=5,
                email_clicks=3,
                page_views=12,
                demo_attended=True,
                call_scheduled=True,
                estimated_value=50000,
                budget="30k-75k",
            ),
            "lead_003": CRMLead(
                id="lead_003",
                company_name="Enterprise Solutions Corp",
                contact_name="Robert Johnson",
                email="robert@enterprisesolutions.com",
                phone="+1-555-0003",
                industry="Enterprise Software",
                company_size=2500,
                annual_revenue=500_000_000,
                website="enterprisesolutions.com",
                lead_score=95,
                source="Referral",
                stage="proposal",
                owner="sales@sellia.ai",
                email_opens=8,
                email_clicks=5,
                page_views=25,
                demo_attended=True,
                call_scheduled=True,
                estimated_value=150000,
                budget="100k-200k",
            ),
            "lead_004": CRMLead(
                id="lead_004",
                company_name="StartupAI Inc",
                contact_name="Maria Garcia",
                email="maria@startupia.com",
                phone="+1-555-0004",
                industry="AI/ML",
                company_size=12,
                annual_revenue=500_000,
                website="startupia.com",
                lead_score=68,
                source="Content",
                stage="new",
                owner="sales@sellia.ai",
                email_opens=2,
                email_clicks=0,
                page_views=3,
                demo_attended=False,
                call_scheduled=False,
                estimated_value=35000,
                budget="20k-50k",
            ),
            "lead_005": CRMLead(
                id="lead_005",
                company_name="Financial Services Inc",
                contact_name="David Lee",
                email="david@finservices.com",
                phone="+1-555-0005",
                industry="Financial Services",
                company_size=1200,
                annual_revenue=200_000_000,
                website="finservices.com",
                lead_score=88,
                source="LinkedIn",
                stage="negotiation",
                owner="sales@sellia.ai",
                email_opens=12,
                email_clicks=8,
                page_views=40,
                demo_attended=True,
                call_scheduled=True,
                estimated_value=200000,
                budget="150k-250k",
            ),
        }

    async def fetch_lead(self, lead_id: str) -> Optional[CRMLead]:
        """Fetch single lead."""
        logger.info(f"Fetching lead {lead_id} from mock CRM")
        return self.leads_db.get(lead_id)

    async def fetch_leads(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[CRMLead]:
        """Fetch multiple leads with optional filtering."""
        leads = list(self.leads_db.values())

        if not filters:
            return leads

        # Simple filtering logic
        filtered = []
        for lead in leads:
            match = True
            for key, value in filters.items():
                if key == "min_lead_score" and (lead.lead_score or 0) < value:
                    match = False
                    break
                elif key == "stage" and lead.stage != value:
                    match = False
                    break
                elif key == "industry" and lead.industry != value:
                    match = False
                    break
                elif key == "min_company_size" and (lead.company_size or 0) < value:
                    match = False
                    break

            if match:
                filtered.append(lead)

        logger.info(f"Fetched {len(filtered)} leads matching filters {filters}")
        return filtered

    async def update_lead(self, lead_id: str, data: Dict[str, Any]) -> bool:
        """Update lead in mock CRM."""
        if lead_id not in self.leads_db:
            logger.warning(f"Lead {lead_id} not found")
            return False

        lead = self.leads_db[lead_id]
        for key, value in data.items():
            if hasattr(lead, key):
                setattr(lead, key, value)

        logger.info(f"Updated lead {lead_id}: {data}")
        return True

    async def create_activity(
        self, lead_id: str, activity_type: str, description: str
    ) -> bool:
        """Log activity in mock CRM."""
        if lead_id not in self.leads_db:
            return False

        logger.info(
            f"Activity logged for {lead_id}: {activity_type} - {description}"
        )
        return True


class CRMAdapterFactory:
    """Factory for creating CRM adapters."""

    _adapters: Dict[CRMType, CRMAdapter] = {}

    @classmethod
    async def create_adapter(
        cls, crm_type: CRMType, config: Optional[Dict[str, Any]] = None
    ) -> CRMAdapter:
        """Create CRM adapter based on type."""
        if crm_type == CRMType.CUSTOM:
            if CRMType.CUSTOM not in cls._adapters:
                cls._adapters[CRMType.CUSTOM] = MockCRMAdapter()
            return cls._adapters[CRMType.CUSTOM]

        # Future: Add Salesforce, HubSpot, Pipedrive adapters
        # For now, default to mock
        logger.warning(f"CRM type {crm_type} not implemented, using mock adapter")
        return await cls.create_adapter(CRMType.CUSTOM)

    @classmethod
    async def get_default_adapter(cls) -> CRMAdapter:
        """Get default (mock) adapter."""
        return await cls.create_adapter(CRMType.CUSTOM)
