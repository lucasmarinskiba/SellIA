"""Growth Domain API Router"""

import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from app.domains.growth.models import (
    GrowthCampaign, GrowthCampaignType, GrowthCampaignStatus,
    LeadMagnet, InboundLead, NurturingStage,
    SocialProofItem, SocialProofType, SocialProofStatus,
    UgcRequest, ValueSequence,
)
from app.domains.growth.schemas import (
    GrowthCampaignCreate, GrowthCampaignUpdate, GrowthCampaignResponse,
    LeadMagnetCreate, LeadMagnetResponse, LeadMagnetPerformance,
    InboundLeadCreate, InboundLeadResponse,
    SocialProofCreate, SocialProofResponse, SocialProofStats,
    UgcRequestCreate, UgcRequestResponse,
    ValueSequenceCreate, ValueSequenceResponse, ValueSequencePerformance,
    ReferralCampaignCreate, ReferralMetrics, ReferralCampaignReport,
    GrowthDashboardMetrics, CampaignEvaluation,
)
from app.domains.growth.inbound_engine import InboundGrowthEngine
from app.domains.growth.lead_magnet_funnel import LeadMagnetEngine
from app.domains.growth.seo_pipeline import SEOPipeline
from app.domains.growth.value_outreach import ValueFirstOutreach
from app.domains.growth.viral_referral import ViralReferralEngine
from app.domains.growth.social_proof import SocialProofEngine
from app.domains.growth.ugc_collector import UGCCollector
from app.domains.growth.warm_lead_detector import WarmLeadDetector
from app.domains.growth.voice_note_engine import VoiceNoteEngine
from app.domains.growth.content_syndication import ContentSyndicationEngine
from app.domains.growth.comment_responder import CommentResponder

router = APIRouter(prefix="/growth", tags=["growth"])


# ========== Dashboard ==========

@router.get("/dashboard", response_model=GrowthDashboardMetrics)
async def get_growth_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get unified organic growth dashboard metrics."""
    engine = InboundGrowthEngine(db)
    return await engine.get_dashboard_metrics(current_user.business_id)


# ========== Campaigns ==========

@router.post("/campaigns", response_model=GrowthCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: GrowthCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new organic growth campaign."""
    engine = InboundGrowthEngine(db)
    campaign = await engine.create_campaign(
        business_id=current_user.business_id,
        name=data.name,
        campaign_type=GrowthCampaignType(data.campaign_type),
        description=data.description,
        config=data.config,
        target_audience=data.target_audience,
        content_pillars=data.content_pillars,
        tone_of_voice=data.tone_of_voice,
    )
    return campaign


@router.get("/campaigns", response_model=List[GrowthCampaignResponse])
async def list_campaigns(
    campaign_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List growth campaigns with optional filters."""
    engine = InboundGrowthEngine(db)
    campaigns = await engine.get_campaigns(
        business_id=current_user.business_id,
        campaign_type=GrowthCampaignType(campaign_type) if campaign_type else None,
        status=GrowthCampaignStatus(status) if status else None,
    )
    return campaigns


@router.post("/campaigns/{campaign_id}/activate", response_model=GrowthCampaignResponse)
async def activate_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a growth campaign."""
    engine = InboundGrowthEngine(db)
    return await engine.activate_campaign(campaign_id)


@router.post("/campaigns/{campaign_id}/pause", response_model=GrowthCampaignResponse)
async def pause_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause a growth campaign."""
    engine = InboundGrowthEngine(db)
    return await engine.pause_campaign(campaign_id)


@router.get("/campaigns/{campaign_id}/evaluate", response_model=CampaignEvaluation)
async def evaluate_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate campaign performance."""
    engine = InboundGrowthEngine(db)
    return await engine.evaluate_campaign(campaign_id)


# ========== Lead Magnets ==========

@router.post("/lead-magnets", response_model=LeadMagnetResponse, status_code=status.HTTP_201_CREATED)
async def create_lead_magnet(
    data: LeadMagnetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a new lead magnet with AI."""
    engine = LeadMagnetEngine(db)
    from app.domains.growth.models import LeadMagnetFormat
    magnet = await engine.generate_lead_magnet(
        business_id=current_user.business_id,
        topic=data.topic,
        magnet_format=LeadMagnetFormat(data.magnet_format),
        target_audience=data.target_audience,
        campaign_id=data.campaign_id,
    )
    return magnet


@router.get("/lead-magnets", response_model=List[LeadMagnetResponse])
async def list_lead_magnets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all lead magnets for the business."""
    from sqlalchemy import select, desc
    result = await db.execute(
        select(LeadMagnet).where(
            LeadMagnet.business_id == current_user.business_id,
            LeadMagnet.is_active == True,
        ).order_by(desc(LeadMagnet.created_at))
    )
    return list(result.scalars().all())


@router.get("/lead-magnets/{magnet_id}/performance", response_model=LeadMagnetPerformance)
async def get_lead_magnet_performance(
    magnet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get performance report for a lead magnet."""
    engine = LeadMagnetEngine(db)
    return await engine.get_performance_report(magnet_id)


@router.get("/lead-magnets/top", response_model=List[dict])
async def get_top_lead_magnets(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get top performing lead magnets."""
    engine = LeadMagnetEngine(db)
    return await engine.get_top_performing_magnets(current_user.business_id, limit)


# ========== Inbound Leads ==========

@router.post("/leads", response_model=InboundLeadResponse, status_code=status.HTTP_201_CREATED)
async def capture_inbound_lead(
    data: InboundLeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Capture a new organic inbound lead."""
    engine = InboundGrowthEngine(db)
    lead = await engine.capture_inbound_lead(
        business_id=current_user.business_id,
        source_type=data.source_type,
        conversation_id=data.conversation_id,
        campaign_id=data.campaign_id,
        lead_magnet_id=data.lead_magnet_id,
        contact_info=data.contact_info,
        source_detail=data.source_detail,
    )
    return lead


@router.get("/leads", response_model=List[InboundLeadResponse])
async def list_inbound_leads(
    stage: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List inbound leads with filters."""
    engine = InboundGrowthEngine(db)
    return await engine.get_leads(
        business_id=current_user.business_id,
        stage=NurturingStage(stage) if stage else None,
        source_type=source_type,
        limit=limit,
    )


# ========== SEO Content ==========

@router.post("/seo-content/blog-post")
async def generate_seo_blog_post(
    keyword: str,
    search_intent: str = "informational",
    word_count: int = 1200,
    campaign_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an SEO-optimized blog post."""
    pipeline = SEOPipeline(db)
    content = await pipeline.generate_blog_post(
        business_id=current_user.business_id,
        keyword=keyword,
        search_intent=search_intent,
        word_count=word_count,
        campaign_id=campaign_id,
    )
    return {"content_id": str(content.id), "title": content.meta_data.get("title", ""), "status": content.status}


@router.post("/seo-content/guide")
async def generate_seo_guide(
    topic: str,
    difficulty: str = "beginner",
    campaign_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a how-to guide."""
    pipeline = SEOPipeline(db)
    content = await pipeline.generate_guide(
        business_id=current_user.business_id,
        topic=topic,
        difficulty=difficulty,
        campaign_id=campaign_id,
    )
    return {"content_id": str(content.id), "title": content.meta_data.get("title", ""), "status": content.status}


@router.get("/seo-content/scheduled")
async def get_scheduled_content(
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get scheduled SEO content."""
    pipeline = SEOPipeline(db)
    return await pipeline.get_scheduled_content(current_user.business_id, platform)


# ========== Social Proof ==========

@router.get("/social-proof", response_model=List[SocialProofResponse])
async def get_social_proof_wall(
    item_type: Optional[str] = None,
    count: int = Query(10, ge=1, le=50),
    min_rating: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get approved social proof items."""
    engine = SocialProofEngine(db)
    items = await engine.get_social_proof_wall(
        business_id=current_user.business_id,
        item_type=SocialProofType(item_type) if item_type else None,
        count=count,
        min_rating=min_rating,
    )
    return items


@router.post("/social-proof", response_model=SocialProofResponse, status_code=status.HTTP_201_CREATED)
async def collect_social_proof(
    data: SocialProofCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Collect a testimonial/review."""
    engine = SocialProofEngine(db)
    item = await engine.collect_testimonial(
        business_id=current_user.business_id,
        conversation_id=data.conversation_id,
        content=data.content,
        order_id=data.order_id,
        customer_name=data.customer_name,
        media_urls=data.media_urls,
    )
    return item


@router.post("/social-proof/{item_id}/approve", response_model=SocialProofResponse)
async def approve_social_proof(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a social proof item."""
    engine = SocialProofEngine(db)
    item = await engine.approve_item(item_id, approved_by=current_user.id)
    return item


@router.post("/social-proof/{item_id}/reject", response_model=SocialProofResponse)
async def reject_social_proof(
    item_id: uuid.UUID,
    reason: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a social proof item."""
    engine = SocialProofEngine(db)
    item = await engine.reject_item(item_id, reason=reason)
    return item


@router.get("/social-proof/stats", response_model=SocialProofStats)
async def get_social_proof_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get social proof statistics."""
    engine = SocialProofEngine(db)
    return await engine.get_stats(current_user.business_id)


@router.get("/social-proof/moderation-queue", response_model=List[SocialProofResponse])
async def get_moderation_queue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pending social proof items for moderation."""
    engine = SocialProofEngine(db)
    return await engine.get_moderation_queue(current_user.business_id)


# ========== UGC ==========

@router.post("/ugc/requests", response_model=UgcRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_ugc_request(
    data: UgcRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a UGC request."""
    engine = UGCCollector(db)
    request = await engine.request_ugc(
        business_id=current_user.business_id,
        order_id=data.order_id,
        conversation_id=data.conversation_id,
        content_type=data.content_type,
        incentive=data.incentive,
        campaign_id=data.campaign_id,
    )
    return request


@router.post("/ugc/requests/{request_id}/send")
async def send_ugc_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a pending UGC request."""
    engine = UGCCollector(db)
    return await engine.send_ugc_request(request_id)


@router.get("/ugc/gallery")
async def get_ugc_gallery(
    content_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get approved UGC gallery."""
    engine = UGCCollector(db)
    return await engine.get_ugc_gallery(current_user.business_id, content_type, limit)


@router.post("/ugc/requests/{request_id}/approve", response_model=UgcRequestResponse)
async def approve_ugc(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a UGC submission."""
    engine = UGCCollector(db)
    return await engine.approve_ugc(request_id)


# ========== Referrals ==========

@router.post("/referrals/campaign")
async def create_referral_campaign(
    data: ReferralCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update a referral program."""
    engine = ViralReferralEngine(db)
    program = await engine.create_referral_campaign(
        business_id=current_user.business_id,
        name=data.name,
        incentive_type=data.incentive_type,
        reward_value=data.reward_value,
        max_referrals_per_user=data.max_referrals_per_user,
    )
    return {"program_id": str(program.id), "name": program.name, "reward_type": program.reward_type}


@router.post("/referrals/generate-link")
async def generate_referral_link(
    conversation_id: uuid.UUID,
    program_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a referral code for a customer."""
    engine = ViralReferralEngine(db)
    code = await engine.generate_referral_link(
        business_id=current_user.business_id,
        conversation_id=conversation_id,
        program_id=program_id,
    )
    return {"code": code.code, "referral_link": f"https://ref.example.com/{code.code}"}


@router.get("/referrals/metrics", response_model=ReferralMetrics)
async def get_referral_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get viral coefficient and referral metrics."""
    engine = ViralReferralEngine(db)
    return await engine.calculate_viral_coefficient(current_user.business_id)


@router.get("/referrals/report", response_model=ReferralCampaignReport)
async def get_referral_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full referral campaign report."""
    engine = ViralReferralEngine(db)
    return await engine.get_campaign_report(current_user.business_id)


# ========== Value Sequences ==========

@router.post("/value-sequences", response_model=ValueSequenceResponse, status_code=status.HTTP_201_CREATED)
async def create_value_sequence(
    data: ValueSequenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an educational value sequence."""
    engine = ValueFirstOutreach(db)
    sequence = await engine.create_educational_sequence(
        business_id=current_user.business_id,
        name=data.name,
        topic=data.topic,
        message_count=data.message_count,
        total_duration_days=data.total_duration_days,
        target_segment=data.target_segment,
        campaign_id=data.campaign_id,
    )
    return sequence


@router.get("/value-sequences", response_model=List[ValueSequenceResponse])
async def list_value_sequences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List value sequences."""
    from sqlalchemy import select
    result = await db.execute(
        select(ValueSequence).where(
            ValueSequence.business_id == current_user.business_id,
            ValueSequence.is_active == True,
        )
    )
    return list(result.scalars().all())


@router.get("/value-sequences/{sequence_id}/performance", response_model=ValueSequencePerformance)
async def get_value_sequence_performance(
    sequence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get value sequence performance."""
    engine = ValueFirstOutreach(db)
    return await engine.get_sequence_performance(sequence_id)


@router.post("/value-sequences/{sequence_id}/enroll")
async def enroll_in_sequence(
    sequence_id: uuid.UUID,
    conversation_id: uuid.UUID,
    inbound_lead_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enroll a lead in a value sequence."""
    engine = ValueFirstOutreach(db)
    enrollment = await engine.enroll_lead(sequence_id, conversation_id, inbound_lead_id)
    return {"enrollment_id": str(enrollment.id), "status": enrollment.status}


# ========== Warm Lead Detector ==========

@router.get("/warming-leads")
async def get_warming_leads(
    lookback_hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get leads that are showing warming signals."""
    engine = WarmLeadDetector(db)
    return await engine.scan_for_warming_leads(current_user.business_id, lookback_hours)


@router.get("/warming-leads/report")
async def get_warming_report(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get warming leads report."""
    engine = WarmLeadDetector(db)
    return await engine.get_warming_report(current_user.business_id, days)


# ========== Voice Notes ==========

@router.post("/voice-notes/welcome")
async def generate_welcome_voice_note(
    lead_name: str,
    source: str = "organic",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a welcome voice note script."""
    engine = VoiceNoteEngine(db)
    script = await engine.generate_welcome_voice_note(current_user.business_id, lead_name, source)
    return {"script": script, "estimated_seconds": len(script.split()) // 2}


@router.post("/voice-notes/value")
async def generate_value_voice_note(
    lead_name: str,
    topic: str,
    tip: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a value voice note script."""
    engine = VoiceNoteEngine(db)
    script = await engine.generate_value_voice_note(current_user.business_id, lead_name, topic, tip)
    return {"script": script, "estimated_seconds": len(script.split()) // 2}


@router.post("/voice-notes/soft-close")
async def generate_soft_close_voice_note(
    lead_name: str,
    product_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a soft-close voice note script."""
    engine = VoiceNoteEngine(db)
    script = await engine.generate_soft_close_voice_note(current_user.business_id, lead_name, product_name)
    return {"script": script, "estimated_seconds": len(script.split()) // 2}


# ========== Content Syndication ==========

@router.post("/syndicate/{content_id}")
async def syndicate_content(
    content_id: uuid.UUID,
    platforms: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Syndicate content across multiple platforms."""
    engine = ContentSyndicationEngine(db)
    return await engine.syndicate_content(current_user.business_id, content_id, platforms)


# ========== Comment Responder ==========

@router.post("/comments/process")
async def process_comment(
    platform: str,
    post_id: str,
    comment_id: str,
    author_username: str,
    comment_text: str,
    author_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process a social media comment and generate response strategy."""
    engine = CommentResponder(db)
    return await engine.process_comment(
        business_id=current_user.business_id,
        platform=platform,
        post_id=post_id,
        comment_id=comment_id,
        author_username=author_username,
        comment_text=comment_text,
        author_id=author_id,
    )


@router.get("/comments/analytics")
async def get_comment_analytics(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comment engagement analytics."""
    engine = CommentResponder(db)
    return await engine.get_comment_analytics(current_user.business_id, days)
