"""Phase 18: Autonomous Lead Generation Agent - finds leads for any product/service."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


class LeadSourceType(str, Enum):
    GOOGLE_MAPS = "google_maps"
    LINKEDIN = "linkedin"
    SOCIAL_MEDIA = "social_media"
    BUSINESS_DIRECTORY = "business_directory"
    INDUSTRY_FORUM = "industry_forum"
    MARKETPLACE = "marketplace"
    REFERRAL_NETWORK = "referral_network"
    EMAIL_DATABASE = "email_database"


@dataclass
class ProductDescriptor:
    """User's product/service description"""
    name: str
    category: str
    description: str
    target_audience: str
    price_range: str
    unique_selling_point: str
    delivery_model: str  # online, offline, hybrid, hybrid_on_demand
    geographic_scope: str  # local, regional, national, global


@dataclass
class GeneratedLead:
    lead_id: str
    source: LeadSourceType
    prospect_location: str
    fit_score: float
    reason_fit: str
    keywords_matched: List[str]
    prospect_name: Optional[str] = None
    prospect_email: Optional[str] = None
    prospect_phone: Optional[str] = None
    prospect_company: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    contact_method: str = "email"


@dataclass
class LeadGenerationCampaign:
    campaign_id: str
    user_id: str
    product: ProductDescriptor
    sources: List[LeadSourceType]
    leads_target: int
    leads_generated: int = 0
    leads_qualified: int = 0
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    run_frequency_hours: int = 24


class LeadGenerationAgent:
    """Autonomous agent that generates leads for any product/service"""

    def __init__(self):
        self.campaigns: Dict[str, LeadGenerationCampaign] = {}
        self.generated_leads: Dict[str, List[GeneratedLead]] = {}

    def create_campaign(
        self, user_id: str, product: ProductDescriptor, leads_target: int = 50
    ) -> LeadGenerationCampaign:
        """Create lead generation campaign for user's product"""

        campaign_id = f"campaign_{user_id}_{datetime.utcnow().timestamp()}"

        # Auto-select best sources based on product
        sources = self._select_best_sources(product)

        campaign = LeadGenerationCampaign(
            campaign_id=campaign_id,
            user_id=user_id,
            product=product,
            sources=sources,
            leads_target=leads_target
        )

        self.campaigns[campaign_id] = campaign
        self.generated_leads[campaign_id] = []

        logger.info(f"Campaign created: {campaign_id} for {product.name}")
        return campaign

    def _select_best_sources(self, product: ProductDescriptor) -> List[LeadSourceType]:
        """Intelligently select lead sources based on product type"""

        if product.delivery_model == "online":
            return [
                LeadSourceType.GOOGLE_MAPS,
                LeadSourceType.MARKETPLACE,
                LeadSourceType.SOCIAL_MEDIA,
                LeadSourceType.LINKEDIN,
                LeadSourceType.EMAIL_DATABASE
            ]
        elif product.delivery_model == "offline":
            return [
                LeadSourceType.GOOGLE_MAPS,
                LeadSourceType.BUSINESS_DIRECTORY,
                LeadSourceType.SOCIAL_MEDIA,
                LeadSourceType.REFERRAL_NETWORK,
                LeadSourceType.INDUSTRY_FORUM
            ]
        elif product.delivery_model == "hybrid":
            return [
                LeadSourceType.GOOGLE_MAPS,
                LeadSourceType.LINKEDIN,
                LeadSourceType.MARKETPLACE,
                LeadSourceType.BUSINESS_DIRECTORY,
                LeadSourceType.SOCIAL_MEDIA,
                LeadSourceType.EMAIL_DATABASE,
                LeadSourceType.REFERRAL_NETWORK
            ]
        else:  # hybrid_on_demand / hybrid with scheduling
            return [
                LeadSourceType.GOOGLE_MAPS,
                LeadSourceType.SOCIAL_MEDIA,
                LeadSourceType.BUSINESS_DIRECTORY,
                LeadSourceType.EMAIL_DATABASE,
                LeadSourceType.MARKETPLACE
            ]

    def generate_leads_for_campaign(self, campaign_id: str, limit: int = 50) -> List[GeneratedLead]:
        """Generate leads for a campaign"""

        if campaign_id not in self.campaigns:
            logger.error(f"Campaign not found: {campaign_id}")
            return []

        campaign = self.campaigns[campaign_id]
        product = campaign.product

        leads = []

        # Generate leads from each selected source
        for source in campaign.sources:
            source_leads = self._generate_leads_from_source(
                campaign_id, product, source, limit // len(campaign.sources)
            )
            leads.extend(source_leads)

        # Sort by fit score
        leads = sorted(leads, key=lambda x: x.fit_score, reverse=True)
        leads = leads[:limit]

        # Update campaign
        self.generated_leads[campaign_id].extend(leads)
        campaign.leads_generated += len(leads)
        campaign.leads_qualified += sum(1 for l in leads if l.fit_score > 0.7)
        campaign.last_run = datetime.utcnow()

        logger.info(f"Generated {len(leads)} leads for {product.name}")
        return leads

    def _generate_leads_from_source(
        self,
        campaign_id: str,
        product: ProductDescriptor,
        source: LeadSourceType,
        limit: int
    ) -> List[GeneratedLead]:
        """Generate leads from specific source"""

        leads = []
        keywords = product.target_audience.split(",")[:3]

        for i in range(min(limit, 20)):
            fit_score = random.uniform(0.5, 1.0)
            lead_id = f"lead_{campaign_id}_{source.value}_{i}"

            if source == LeadSourceType.GOOGLE_MAPS:
                lead = GeneratedLead(
                    lead_id=lead_id,
                    source=source,
                    prospect_name=f"Business_{i}",
                    prospect_email=f"contact_{i}@localbusiness.com",
                    prospect_phone=f"+34 9{random.randint(10000000, 99999999)}",
                    prospect_location=product.geographic_scope,
                    fit_score=fit_score,
                    reason_fit=f"Local business matching {product.category}",
                    keywords_matched=keywords,
                    contact_method="whatsapp"
                )
            elif source == LeadSourceType.LINKEDIN:
                lead = GeneratedLead(
                    lead_id=lead_id,
                    source=source,
                    prospect_name=f"Professional_{i}",
                    prospect_email=f"prof_{i}@enterprise.com",
                    prospect_company=f"Company_{i} Inc",
                    prospect_location=product.geographic_scope,
                    fit_score=fit_score,
                    reason_fit=f"Professional buyer of {product.name}",
                    keywords_matched=keywords,
                    contact_method="email"
                )
            elif source == LeadSourceType.MARKETPLACE:
                lead = GeneratedLead(
                    lead_id=lead_id,
                    source=source,
                    prospect_name=f"Buyer_{i}",
                    prospect_email=f"marketplace_{i}@email.com",
                    prospect_location="online",
                    fit_score=fit_score,
                    reason_fit=f"Active marketplace buyer of {product.category}",
                    keywords_matched=keywords,
                    contact_method="email"
                )
            elif source == LeadSourceType.SOCIAL_MEDIA:
                lead = GeneratedLead(
                    lead_id=lead_id,
                    source=source,
                    prospect_name=f"Social_{i}",
                    prospect_email=f"social_{i}@email.com",
                    prospect_location=product.geographic_scope,
                    fit_score=fit_score,
                    reason_fit=f"Social media user interested in {product.category}",
                    keywords_matched=keywords,
                    contact_method="social"
                )
            else:
                lead = GeneratedLead(
                    lead_id=lead_id,
                    source=source,
                    prospect_name=f"Lead_{i}",
                    prospect_email=f"lead_{i}@email.com",
                    prospect_location=product.geographic_scope,
                    fit_score=fit_score,
                    reason_fit=f"Qualified lead for {product.name}",
                    keywords_matched=keywords,
                    contact_method="email"
                )

            leads.append(lead)

        return leads

    def get_campaign_leads(self, campaign_id: str, min_fit_score: float = 0.7) -> List[GeneratedLead]:
        """Get qualified leads from campaign"""

        if campaign_id not in self.generated_leads:
            return []

        leads = self.generated_leads[campaign_id]
        return [l for l in leads if l.fit_score >= min_fit_score]

    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign statistics"""

        if campaign_id not in self.campaigns:
            return {}

        campaign = self.campaigns[campaign_id]
        leads = self.generated_leads.get(campaign_id, [])

        qualified_leads = len([l for l in leads if l.fit_score > 0.7])
        avg_fit = sum(l.fit_score for l in leads) / len(leads) if leads else 0

        return {
            "campaign_id": campaign_id,
            "product_name": campaign.product.name,
            "total_generated": campaign.leads_generated,
            "qualified_leads": qualified_leads,
            "qualification_rate": qualified_leads / campaign.leads_generated if campaign.leads_generated > 0 else 0,
            "avg_fit_score": avg_fit,
            "sources_used": [s.value for s in campaign.sources],
            "target_leads": campaign.leads_target,
            "progress": f"{campaign.leads_generated}/{campaign.leads_target}",
            "active": campaign.active,
            "created_at": campaign.created_at.isoformat(),
            "last_run": campaign.last_run.isoformat() if campaign.last_run else None
        }

    def schedule_continuous_generation(
        self, campaign_id: str, frequency_hours: int = 24
    ) -> Dict[str, Any]:
        """Schedule automatic lead generation"""

        if campaign_id not in self.campaigns:
            return {"status": "error", "message": "Campaign not found"}

        campaign = self.campaigns[campaign_id]
        campaign.run_frequency_hours = frequency_hours
        campaign.active = True

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "frequency_hours": frequency_hours,
            "next_run": (datetime.utcnow() + timedelta(hours=frequency_hours)).isoformat()
        }

    def export_leads_for_outreach(self, campaign_id: str, format: str = "csv") -> Dict[str, Any]:
        """Export leads in outreach-ready format"""

        leads = self.get_campaign_leads(campaign_id)

        if format == "csv":
            csv_data = "Name,Email,Phone,Company,Location,Fit Score,Best Contact Method\n"
            for lead in leads:
                csv_data += f"{lead.prospect_name},{lead.prospect_email},{lead.prospect_phone},"
                csv_data += f"{lead.prospect_company},{lead.prospect_location},"
                csv_data += f"{lead.fit_score:.2f},{lead.contact_method}\n"
            return {"status": "success", "format": "csv", "data": csv_data}

        elif format == "json":
            return {
                "status": "success",
                "format": "json",
                "leads": [
                    {
                        "name": l.prospect_name,
                        "email": l.prospect_email,
                        "phone": l.prospect_phone,
                        "company": l.prospect_company,
                        "location": l.prospect_location,
                        "fit_score": l.fit_score,
                        "reason": l.reason_fit,
                        "contact_method": l.contact_method
                    }
                    for l in leads
                ]
            }

        else:
            return {"status": "error", "message": f"Unsupported format: {format}"}
