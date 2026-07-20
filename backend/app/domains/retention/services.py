"""Retention & Loyalty Services.

Handles referrals, RFM segmentation, NPS campaigns, and loyalty programs.
"""

import uuid
import secrets
from typing import Any, Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.retention.models import (
    LoyaltyProgram, ReferralProgram, ReferralCode, ReferralUse,
    NpsCampaign, NpsResponse, CustomerSegment, CustomerSegmentType,
    ReferralStatus, NpsCampaignStatus,
)
from app.domains.channels.models import Conversation
from app.domains.orders.models import Order
from app.core.logger import get_logger

logger = get_logger(__name__)


class RetentionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Referrals ==========

    async def create_referral_code(self, business_id: uuid.UUID, program_id: uuid.UUID, conversation_id: uuid.UUID, name: str, email: str) -> ReferralCode:
        code = f"REF-{secrets.token_hex(4).upper()}"
        ref = ReferralCode(
            business_id=business_id,
            program_id=program_id,
            conversation_id=conversation_id,
            code=code,
            referrer_name=name,
            referrer_email=email,
        )
        self.db.add(ref)
        await self.db.commit()
        await self.db.refresh(ref)
        return ref

    async def track_referral_use(self, business_id: uuid.UUID, code: str, referred_conversation_id: Optional[uuid.UUID] = None, referred_email: Optional[str] = None) -> Optional[ReferralUse]:
        result = await self.db.execute(select(ReferralCode).where(ReferralCode.code == code, ReferralCode.business_id == business_id))
        code_obj = result.scalar_one_or_none()
        if not code_obj or not code_obj.is_active:
            return None

        code_obj.total_uses += 1
        use = ReferralUse(
            code_id=code_obj.id,
            business_id=business_id,
            referred_conversation_id=referred_conversation_id,
            referred_email=referred_email,
        )
        self.db.add(use)
        await self.db.commit()
        return use

    async def convert_referral(self, use_id: uuid.UUID, order_id: uuid.UUID):
        result = await self.db.execute(select(ReferralUse).where(ReferralUse.id == use_id))
        use = result.scalar_one_or_none()
        if not use:
            return
        use.status = ReferralStatus.CONVERTED
        use.converted_order_id = order_id
        use.converted_at = datetime.now(timezone.utc)

        result = await self.db.execute(select(ReferralCode).where(ReferralCode.id == use.code_id))
        code = result.scalar_one_or_none()
        if code:
            code.total_conversions += 1
        await self.db.commit()

    # ========== NPS ==========

    async def create_nps_campaign(self, business_id: uuid.UUID, name: str, trigger_type: str = "post_purchase", trigger_days: int = 14, **kwargs) -> NpsCampaign:
        camp = NpsCampaign(
            business_id=business_id,
            name=name,
            trigger_type=trigger_type,
            trigger_days=trigger_days,
            **kwargs,
        )
        self.db.add(camp)
        await self.db.commit()
        await self.db.refresh(camp)
        return camp

    async def record_nps_response(self, campaign_id: uuid.UUID, business_id: uuid.UUID, conversation_id: uuid.UUID, score: int, feedback_text: Optional[str] = None) -> NpsResponse:
        category = "detractor" if score <= 6 else ("passive" if score <= 8 else "promoter")
        resp = NpsResponse(
            campaign_id=campaign_id,
            business_id=business_id,
            conversation_id=conversation_id,
            score=score,
            feedback_text=feedback_text,
            category=category,
        )
        self.db.add(resp)
        await self.db.commit()
        await self.db.refresh(resp)
        return resp

    async def get_nps_score(self, business_id: uuid.UUID, campaign_id: Optional[uuid.UUID] = None) -> dict[str, Any]:
        query = select(NpsResponse).where(NpsResponse.business_id == business_id)
        if campaign_id:
            query = query.where(NpsResponse.campaign_id == campaign_id)
        result = await self.db.execute(query)
        responses = result.scalars().all()

        if not responses:
            return {"nps": 0, "promoters": 0, "passives": 0, "detractors": 0, "total": 0}

        promoters = sum(1 for r in responses if r.category == "promoter")
        passives = sum(1 for r in responses if r.category == "passive")
        detractors = sum(1 for r in responses if r.category == "detractor")
        total = len(responses)
        nps = round(((promoters - detractors) / total) * 100) if total else 0

        return {"nps": nps, "promoters": promoters, "passives": passives, "detractors": detractors, "total": total}

    # ========== RFM Segmentation ==========

    async def calculate_rfm_for_business(self, business_id: uuid.UUID):
        """Calculate RFM scores for all customers of a business."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.business_id == business_id,
                Conversation.is_active == True,
            )
        )
        conversations = result.scalars().all()

        now = datetime.now(timezone.utc)

        for conv in conversations:
            orders_result = await self.db.execute(
                select(Order).where(
                    Order.business_id == business_id,
                    Order.conversation_id == conv.id,
                    Order.is_active == True,
                ).order_by(desc(Order.created_at))
            )
            orders = orders_result.scalars().all()

            if not orders:
                continue

            total_revenue = sum(o.total_amount for o in orders)
            total_orders = len(orders)
            avg_order_value = total_revenue / total_orders
            last_order = orders[0].created_at
            days_since_last = (now - last_order).days if last_order else 999

            # Score calculation (quintiles simplified)
            r_score = max(1, min(5, 5 - (days_since_last // 20)))  # Recent = high
            f_score = max(1, min(5, total_orders))  # Frequent = high
            m_score = max(1, min(5, int(total_revenue / Decimal("10000")) + 1))  # High spend = high
            rfm = r_score * 100 + f_score * 10 + m_score

            # Segment assignment
            if r_score >= 4 and f_score >= 4:
                segment = CustomerSegmentType.CHAMPIONS
            elif r_score >= 3 and f_score >= 3:
                segment = CustomerSegmentType.LOYAL
            elif r_score >= 4 and f_score <= 2:
                segment = CustomerSegmentType.NEW
            elif r_score >= 2 and f_score >= 2:
                segment = CustomerSegmentType.POTENTIAL
            elif r_score == 3:
                segment = CustomerSegmentType.AT_RISK
            else:
                segment = CustomerSegmentType.LOST

            # Upsert segment
            seg_result = await self.db.execute(
                select(CustomerSegment).where(
                    CustomerSegment.business_id == business_id,
                    CustomerSegment.conversation_id == conv.id,
                )
            )
            seg = seg_result.scalar_one_or_none()
            if not seg:
                seg = CustomerSegment(business_id=business_id, conversation_id=conv.id)
                self.db.add(seg)

            seg.segment = segment
            seg.r_score = r_score
            seg.f_score = f_score
            seg.m_score = m_score
            seg.rfm_score = rfm
            seg.last_order_at = last_order
            seg.total_orders = total_orders
            seg.total_revenue = total_revenue
            seg.avg_order_value = avg_order_value
            seg.calculated_at = now

        await self.db.commit()
        logger.info(f"RFM calculated for {len(conversations)} customers in business {business_id}")

    async def get_segment_counts(self, business_id: uuid.UUID) -> dict[str, int]:
        result = await self.db.execute(
            select(CustomerSegment.segment, func.count(CustomerSegment.id)).where(
                CustomerSegment.business_id == business_id,
                CustomerSegment.is_active == True,
            ).group_by(CustomerSegment.segment)
        )
        return {row[0].value: row[1] for row in result.all()}
