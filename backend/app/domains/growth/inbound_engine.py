"""Inbound Growth Engine — Main orchestrator for organic customer acquisition.

Coordinates SEO content, lead magnets, value outreach, referrals, social proof,
and UGC collection into a unified "vender sin vender" pipeline.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.growth.models import (
    GrowthCampaign, GrowthCampaignType, GrowthCampaignStatus,
    InboundLead, InboundLeadSource, NurturingStage,
    LeadMagnet,
)
from app.domains.outreach.service import FatigueScoringService
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)


class InboundGrowthEngine:
    """Orchestrates all organic growth strategies for a business."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fatigue = FatigueScoringService(db)

    # ========== Campaign Management ==========

    async def create_campaign(
        self,
        business_id: uuid.UUID,
        name: str,
        campaign_type: GrowthCampaignType,
        description: str = "",
        config: dict = None,
        target_audience: str = "",
        content_pillars: list = None,
        tone_of_voice: str = "educational",
    ) -> GrowthCampaign:
        """Create a new organic growth campaign."""
        campaign = GrowthCampaign(
            business_id=business_id,
            name=name,
            campaign_type=campaign_type,
            description=description,
            config=config or {},
            target_audience=target_audience,
            content_pillars=content_pillars or [],
            tone_of_voice=tone_of_voice,
            status=GrowthCampaignStatus.DRAFT,
        )
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        logger.info(f"Created growth campaign {campaign.id} ({campaign_type}) for business {business_id}")
        return campaign

    async def activate_campaign(self, campaign_id: uuid.UUID) -> GrowthCampaign:
        """Activate a campaign and set start date."""
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        campaign.status = GrowthCampaignStatus.ACTIVE
        campaign.started_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(campaign)
        logger.info(f"Activated growth campaign {campaign_id}")
        return campaign

    async def pause_campaign(self, campaign_id: uuid.UUID) -> GrowthCampaign:
        """Pause a campaign."""
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        campaign.status = GrowthCampaignStatus.PAUSED
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def evaluate_campaign(self, campaign_id: uuid.UUID) -> dict[str, Any]:
        """Evaluate campaign performance and return recommendations."""
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        # Aggregate lead data
        leads_result = await self.db.execute(
            select(func.count(InboundLead.id)).where(
                InboundLead.campaign_id == campaign_id,
                InboundLead.is_active == True,
            )
        )
        total_leads = leads_result.scalar() or 0

        converted_result = await self.db.execute(
            select(func.count(InboundLead.id)).where(
                InboundLead.campaign_id == campaign_id,
                InboundLead.nurturing_stage == NurturingStage.CONVERTED,
            )
        )
        converted_leads = converted_result.scalar() or 0

        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

        # Update campaign metrics
        campaign.leads_generated = total_leads
        campaign.conversions = converted_leads
        campaign.conversion_rate = conversion_rate
        await self.db.commit()

        recommendations = []
        if conversion_rate < 5:
            recommendations.append("Conversion rate is low. Consider improving lead magnet quality or nurturing sequence.")
        if total_leads < 10:
            recommendations.append("Low lead volume. Increase content distribution frequency or expand to new platforms.")
        if campaign.campaign_type == GrowthCampaignType.REFERRAL_VIRAL:
            recommendations.append("Track viral coefficient weekly. Target K > 1.0 for exponential growth.")

        return {
            "campaign_id": str(campaign_id),
            "name": campaign.name,
            "type": campaign.campaign_type.value,
            "status": campaign.status.value,
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate": round(conversion_rate, 2),
            "revenue_attributed": float(campaign.revenue_attributed or 0),
            "content_published": campaign.content_published,
            "recommendations": recommendations,
        }

    async def get_campaigns(
        self,
        business_id: uuid.UUID,
        campaign_type: GrowthCampaignType = None,
        status: GrowthCampaignStatus = None,
    ) -> List[GrowthCampaign]:
        """List campaigns with optional filters."""
        query = select(GrowthCampaign).where(
            GrowthCampaign.business_id == business_id,
            GrowthCampaign.is_active == True,
        )
        if campaign_type:
            query = query.where(GrowthCampaign.campaign_type == campaign_type)
        if status:
            query = query.where(GrowthCampaign.status == status)
        query = query.order_by(desc(GrowthCampaign.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_dashboard_metrics(self, business_id: uuid.UUID) -> dict[str, Any]:
        """Get unified organic growth dashboard metrics."""
        # Leads this week
        week_ago = datetime.now(timezone.utc) - __import__('datetime').timedelta(days=7)
        leads_week_result = await self.db.execute(
            select(func.count(InboundLead.id)).where(
                InboundLead.business_id == business_id,
                InboundLead.first_touch_at >= week_ago,
            )
        )
        leads_this_week = leads_week_result.scalar() or 0

        # Total organic leads
        total_leads_result = await self.db.execute(
            select(func.count(InboundLead.id)).where(
                InboundLead.business_id == business_id,
                InboundLead.is_active == True,
            )
        )
        total_organic_leads = total_leads_result.scalar() or 0

        # Conversions
        conversions_result = await self.db.execute(
            select(func.count(InboundLead.id)).where(
                InboundLead.business_id == business_id,
                InboundLead.nurturing_stage == NurturingStage.CONVERTED,
            )
        )
        total_conversions = conversions_result.scalar() or 0

        # Active campaigns
        active_campaigns_result = await self.db.execute(
            select(func.count(GrowthCampaign.id)).where(
                GrowthCampaign.business_id == business_id,
                GrowthCampaign.status == GrowthCampaignStatus.ACTIVE,
            )
        )
        active_campaigns = active_campaigns_result.scalar() or 0

        # Lead sources breakdown
        sources_result = await self.db.execute(
            select(InboundLead.source_type, func.count(InboundLead.id))
            .where(InboundLead.business_id == business_id, InboundLead.is_active == True)
            .group_by(InboundLead.source_type)
        )
        sources_breakdown = {source.value: count for source, count in sources_result.all()}

        return {
            "leads_this_week": leads_this_week,
            "total_organic_leads": total_organic_leads,
            "total_conversions": total_conversions,
            "conversion_rate": round((total_conversions / total_organic_leads * 100), 2) if total_organic_leads > 0 else 0,
            "active_campaigns": active_campaigns,
            "sources_breakdown": sources_breakdown,
            "period": "last_7_days",
        }

    # ========== Lead Capture ==========

    async def capture_inbound_lead(
        self,
        business_id: uuid.UUID,
        source_type: InboundLeadSource,
        conversation_id: uuid.UUID = None,
        campaign_id: uuid.UUID = None,
        lead_magnet_id: uuid.UUID = None,
        contact_info: dict = None,
        source_detail: str = "",
    ) -> InboundLead:
        """Capture a new organic inbound lead."""
        lead = InboundLead(
            business_id=business_id,
            source_type=source_type,
            conversation_id=conversation_id,
            campaign_id=campaign_id,
            lead_magnet_id=lead_magnet_id,
            contact_info=contact_info or {},
            source_detail=source_detail,
            nurturing_stage=NurturingStage.NEW,
        )
        self.db.add(lead)
        await self.db.commit()
        await self.db.refresh(lead)

        # Emit event
        await event_bus.emit("inbound.lead_captured", {
            "business_id": str(business_id),
            "lead_id": str(lead.id),
            "source_type": source_type.value,
            "conversation_id": str(conversation_id) if conversation_id else None,
        })

        logger.info(f"Captured inbound lead {lead.id} from {source_type.value} for business {business_id}")
        return lead

    async def update_lead_stage(
        self,
        lead_id: uuid.UUID,
        new_stage: NurturingStage,
        engagement_delta: int = 0,
    ) -> InboundLead:
        """Update nurturing stage and engagement score."""
        lead = await self._get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        old_stage = lead.nurturing_stage
        lead.nurturing_stage = new_stage
        lead.engagement_score += engagement_delta
        lead.last_touch_at = datetime.now(timezone.utc)

        if new_stage == NurturingStage.CONVERTED and old_stage != NurturingStage.CONVERTED:
            lead.converted_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def get_leads(
        self,
        business_id: uuid.UUID,
        stage: NurturingStage = None,
        source_type: InboundLeadSource = None,
        limit: int = 50,
    ) -> List[InboundLead]:
        """List inbound leads with filters."""
        query = select(InboundLead).where(
            InboundLead.business_id == business_id,
            InboundLead.is_active == True,
        )
        if stage:
            query = query.where(InboundLead.nurturing_stage == stage)
        if source_type:
            query = query.where(InboundLead.source_type == source_type)
        query = query.order_by(desc(InboundLead.first_touch_at)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ========== Content Distribution ==========

    async def distribute_content(
        self,
        business_id: uuid.UUID,
        content_id: uuid.UUID,
        platforms: List[str],
    ) -> dict[str, Any]:
        """Distribute generated content across platforms."""
        from app.domains.automations.models import ContentCalendar

        results = []
        for platform in platforms:
            entry = ContentCalendar(
                business_id=business_id,
                content_id=content_id,
                platform=platform,
                status="scheduled",
                scheduled_at=datetime.now(timezone.utc),
            )
            self.db.add(entry)
            results.append({"platform": platform, "status": "scheduled"})

        await self.db.commit()
        logger.info(f"Distributed content {content_id} to {len(platforms)} platforms for business {business_id}")
        return {"content_id": str(content_id), "platforms": results}

    # ========== Helpers ==========

    async def _get_campaign(self, campaign_id: uuid.UUID) -> Optional[GrowthCampaign]:
        result = await self.db.execute(
            select(GrowthCampaign).where(GrowthCampaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def _get_lead(self, lead_id: uuid.UUID) -> Optional[InboundLead]:
        result = await self.db.execute(
            select(InboundLead).where(InboundLead.id == lead_id)
        )
        return result.scalar_one_or_none()
