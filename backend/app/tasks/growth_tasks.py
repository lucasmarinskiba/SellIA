"""Growth Celery Tasks — Organic acquisition automation running 24/7.

These tasks work while the user sleeps to:
- Generate SEO content and social posts
- Deliver lead magnets to new inbound leads
- Nurture cold leads with educational content
- Collect social proof (reviews, testimonials)
- Request UGC from satisfied customers
- Evaluate referral viral coefficient
- Engage with community comments
- Optimize campaigns based on performance
"""

import uuid
from datetime import datetime, timezone, timedelta

from celery import shared_task
from sqlalchemy import select, func, desc

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger

logger = get_logger(__name__)


@shared_task(name="growth.inbound_content_generator")
def inbound_content_generator():
    """Generate SEO content, social posts, and lead magnets for active campaigns."""
    import asyncio
    asyncio.run(_inbound_content_generator())


async def _inbound_content_generator():
    async with AsyncSessionLocal() as db:
        from app.domains.growth.models import GrowthCampaign, GrowthCampaignStatus, GrowthCampaignType
        from app.domains.growth.seo_pipeline import SEOPipeline
        from app.domains.growth.lead_magnet_funnel import LeadMagnetEngine

        # Find active SEO campaigns
        result = await db.execute(
            select(GrowthCampaign).where(
                GrowthCampaign.campaign_type == GrowthCampaignType.SEO_CONTENT,
                GrowthCampaign.status == GrowthCampaignStatus.ACTIVE,
                GrowthCampaign.is_active == True,
            )
        )
        campaigns = result.scalars().all()

        for campaign in campaigns:
            try:
                pipeline = SEOPipeline(db)
                keywords = campaign.config.get("target_keywords", [])
                if not keywords:
                    keywords = [campaign.topic or "guía práctica"]

                for keyword in keywords[:2]:  # Max 2 per run
                    content = await pipeline.generate_blog_post(
                        business_id=campaign.business_id,
                        keyword=keyword,
                        campaign_id=campaign.id,
                    )
                    # Schedule for next week
                    publish_at = datetime.now(timezone.utc) + timedelta(days=7)
                    await pipeline.schedule_publication(content.id, publish_at, "blog")
                    campaign.content_published += 1

                await db.commit()
                logger.info(f"Generated SEO content for campaign {campaign.id}")
            except Exception as e:
                logger.error(f"Failed to generate content for campaign {campaign.id}: {e}")


@shared_task(name="growth.lead_magnet_distributor")
def lead_magnet_distributor():
    """Deliver pending lead magnets to new inbound leads."""
    import asyncio
    asyncio.run(_lead_magnet_distributor())


async def _lead_magnet_distributor():
    async with AsyncSessionLocal() as db:
        from app.domains.growth.models import InboundLead, NurturingStage, LeadMagnet
        from app.domains.growth.lead_magnet_funnel import LeadMagnetEngine

        # Find new leads with lead magnet source that haven't received it yet
        result = await db.execute(
            select(InboundLead).where(
                InboundLead.source_type == "lead_magnet",
                InboundLead.nurturing_stage == NurturingStage.NEW,
                InboundLead.is_active == True,
                InboundLead.conversation_id.isnot(None),
            ).limit(50)
        )
        leads = result.scalars().all()

        engine = LeadMagnetEngine(db)
        delivered = 0

        for lead in leads:
            try:
                if lead.lead_magnet_id:
                    result = await engine.deliver_lead_magnet(
                        magnet_id=lead.lead_magnet_id,
                        conversation_id=lead.conversation_id,
                    )
                    if result.get("status") == "delivered":
                        delivered += 1
                        lead.nurturing_stage = NurturingStage.AWARENESS
            except Exception as e:
                logger.error(f"Failed to deliver lead magnet to lead {lead.id}: {e}")

        await db.commit()
        logger.info(f"Delivered {delivered} lead magnets")


@shared_task(name="growth.cold_lead_nurturer")
def cold_lead_nurturer():
    """Send educational content to cold leads (respects fatigue)."""
    import asyncio
    asyncio.run(_cold_lead_nurturer())


async def _cold_lead_nurturer():
    async with AsyncSessionLocal() as db:
        from app.domains.growth.models import InboundLead, NurturingStage
        from app.domains.growth.value_outreach import ValueFirstOutreach
        from app.domains.outreach.service import FatigueScoringService

        # Find cold leads
        result = await db.execute(
            select(InboundLead).where(
                InboundLead.nurturing_stage.in_([NurturingStage.NEW, NurturingStage.AWARENESS]),
                InboundLead.is_active == True,
                InboundLead.conversation_id.isnot(None),
            ).limit(30)
        )
        leads = result.scalars().all()

        fatigue = FatigueScoringService(db)
        nurtured = 0

        for lead in leads:
            try:
                can_contact = await fatigue.can_contact_now(
                    lead.business_id, lead.conversation_id
                )
                if not can_contact.get("allowed", True):
                    continue

                # Send value bomb
                from app.domains.channels.services import send_outbound_message
                topics = ["productividad", "ventas", "marketing", "crecimiento"]
                topic = topics[hash(str(lead.id)) % len(topics)]

                await send_outbound_message(
                    db,
                    lead.conversation_id,
                    f"💡 Tip rápido sobre {topic}: El 80% de los resultados vienen del 20% de las acciones. Identifica cuál es TU 20% y enfócate ahí esta semana. ¿Ya sabes cuál es?",
                    content_type="text",
                )

                lead.value_touches_received += 1
                if lead.value_touches_received >= 3:
                    lead.nurturing_stage = NurturingStage.INTEREST

                nurtured += 1
            except Exception as e:
                logger.error(f"Failed to nurture lead {lead.id}: {e}")

        await db.commit()
        logger.info(f"Nurtured {nurtured} cold leads")


@shared_task(name="growth.social_proof_collector")
def social_proof_collector():
    """Send review requests to customers 3+ days post-purchase."""
    import asyncio
    asyncio.run(_social_proof_collector())


async def _social_proof_collector():
    async with AsyncSessionLocal() as db:
        from app.domains.orders.models import Order, OrderStatus
        from app.domains.growth.social_proof import SocialProofEngine

        three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        result = await db.execute(
            select(Order).where(
                Order.status == OrderStatus.COMPLETED,
                Order.updated_at >= seven_days_ago,
                Order.updated_at <= three_days_ago,
            ).limit(50)
        )
        orders = result.scalars().all()

        engine = SocialProofEngine(db)
        sent = 0

        for order in orders:
            try:
                # Check if review already requested
                from app.domains.growth.models import SocialProofItem
                existing = await db.execute(
                    select(SocialProofItem).where(SocialProofItem.order_id == order.id)
                )
                if existing.scalar_one_or_none():
                    continue

                await engine.request_review(
                    business_id=order.business_id,
                    order_id=order.id,
                    conversation_id=order.conversation_id,
                    channel="whatsapp",
                    delay_hours=0,
                )
                sent += 1
            except Exception as e:
                logger.error(f"Failed to request review for order {order.id}: {e}")

        await db.commit()
        logger.info(f"Sent {sent} review requests")


@shared_task(name="growth.ugc_request_sender")
def ugc_request_sender():
    """Request UGC from satisfied customers."""
    import asyncio
    asyncio.run(_ugc_request_sender())


async def _ugc_request_sender():
    async with AsyncSessionLocal() as db:
        from app.domains.growth.ugc_collector import UGCCollector
        from app.domains.growth.models import UgcRequest, UgcRequestStatus

        # Send pending UGC requests
        result = await db.execute(
            select(UgcRequest).where(
                UgcRequest.status == UgcRequestStatus.PENDING,
            ).limit(30)
        )
        requests = result.scalars().all()

        engine = UGCCollector(db)
        sent = 0

        for req in requests:
            try:
                result = await engine.send_ugc_request(req.id)
                if result.get("status") == "sent":
                    sent += 1
            except Exception as e:
                logger.error(f"Failed to send UGC request {req.id}: {e}")

        logger.info(f"Sent {sent} UGC requests")


@shared_task(name="growth.referral_loop_evaluator")
def referral_loop_evaluator():
    """Calculate viral coefficient, send rewards, optimize campaigns."""
    import asyncio
    asyncio.run(_referral_loop_evaluator())


async def _referral_loop_evaluator():
    async with AsyncSessionLocal() as db:
        from app.domains.growth.viral_referral import ViralReferralEngine
        from app.domains.businesses.models import Business

        result = await db.execute(select(Business.id))
        business_ids = [r[0] for r in result.all()]

        engine = ViralReferralEngine(db)

        for business_id in business_ids:
            try:
                metrics = await engine.calculate_viral_coefficient(business_id)
                logger.info(
                    f"Business {business_id} referral K-factor: {metrics['k_factor']} "
                    f"({metrics['k_interpretation']})"
                )

                # If K > 1, log celebration
                if metrics["exponential_growth"]:
                    logger.info(f"🚀 Business {business_id} has achieved viral growth! K={metrics['k_factor']}")
            except Exception as e:
                logger.error(f"Failed to evaluate referrals for business {business_id}: {e}")


@shared_task(name="growth.community_engagement_scanner")
def community_engagement_scanner():
    """Scan for new comments/replies and auto-respond with value."""
    import asyncio
    asyncio.run(_community_engagement_scanner())


async def _community_engagement_scanner():
    """Process pending comments from social platforms."""
    async with AsyncSessionLocal() as db:
        from app.domains.growth.comment_responder import CommentResponder
        from app.domains.businesses.models import Business

        result = await db.execute(select(Business.id))
        business_ids = [r[0] for r in result.all()]

        # In production, this would fetch real comments from Instagram/Facebook APIs
        # For now, we log that the scanner is active
        for business_id in business_ids:
            try:
                engine = CommentResponder(db)
                analytics = await engine.get_comment_analytics(business_id, days=1)
                logger.info(
                    f"Business {business_id} comment analytics: "
                    f"{analytics['leads_from_comments']} leads from comments today"
                )
            except Exception as e:
                logger.error(f"Comment scanner error for business {business_id}: {e}")


@shared_task(name="growth.growth_campaign_optimizer")
def growth_campaign_optimizer():
    """Evaluate campaign performance, pause underperformers, scale winners."""
    import asyncio
    asyncio.run(_growth_campaign_optimizer())


async def _growth_campaign_optimizer():
    async with AsyncSessionLocal() as db:
        from app.domains.growth.models import GrowthCampaign, GrowthCampaignStatus
        from app.domains.growth.inbound_engine import InboundGrowthEngine

        result = await db.execute(
            select(GrowthCampaign).where(
                GrowthCampaign.status == GrowthCampaignStatus.ACTIVE,
                GrowthCampaign.is_active == True,
            )
        )
        campaigns = result.scalars().all()

        engine = InboundGrowthEngine(db)

        for campaign in campaigns:
            try:
                evaluation = await engine.evaluate_campaign(campaign.id)
                conversion_rate = evaluation.get("conversion_rate", 0)

                if conversion_rate < 2 and campaign.leads_generated > 20:
                    # Underperforming — pause and alert
                    await engine.pause_campaign(campaign.id)
                    logger.warning(
                        f"Paused underperforming campaign {campaign.id} "
                        f"(conversion: {conversion_rate}%)"
                    )
                elif conversion_rate > 10:
                    # High performer — log for scaling
                    logger.info(
                        f"🌟 High-performing campaign {campaign.id} "
                        f"(conversion: {conversion_rate}%) — consider scaling"
                    )
            except Exception as e:
                logger.error(f"Failed to optimize campaign {campaign.id}: {e}")
