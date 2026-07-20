"""Viral Referral Engine — Referral loops with viral coefficient tracking.

Leverages existing retention referral infrastructure (ReferralProgram, ReferralCode)
while adding viral campaign orchestration, K-factor tracking, and auto-optimization.
"""

import uuid
import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.retention.models import ReferralProgram, ReferralCode, ReferralUse, ReferralStatus
from app.domains.growth.models import GrowthCampaign, GrowthCampaignType
from app.domains.outreach.service import FatigueScoringService
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)


class ViralReferralEngine:
    """Referral loop engine with viral coefficient calculation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fatigue = FatigueScoringService(db)

    # ========== Campaign Management ==========

    async def create_referral_campaign(
        self,
        business_id: uuid.UUID,
        name: str,
        incentive_type: str = "discount_credit",  # discount_credit, free_product, exclusive_access
        reward_value: float = 20.0,
        max_referrals_per_user: int = 10,
        campaign_id: uuid.UUID = None,
    ) -> ReferralProgram:
        """Create a referral program/campaign."""
        # Check if program already exists
        existing = await self.db.execute(
            select(ReferralProgram).where(
                ReferralProgram.business_id == business_id,
                ReferralProgram.is_active == True,
            )
        )
        program = existing.scalar_one_or_none()

        if not program:
            program = ReferralProgram(
                business_id=business_id,
                name=name,
                reward_type=incentive_type,
                reward_value=reward_value,
                max_referrals_per_user=max_referrals_per_user,
                expiry_days=30,
            )
            self.db.add(program)
            await self.db.commit()
            await self.db.refresh(program)
            logger.info(f"Created referral program {program.id} for business {business_id}")
        else:
            # Update existing
            program.name = name
            program.reward_type = incentive_type
            program.reward_value = reward_value
            program.max_referrals_per_user = max_referrals_per_user
            await self.db.commit()
            await self.db.refresh(program)

        return program

    async def generate_referral_link(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
        program_id: uuid.UUID = None,
    ) -> ReferralCode:
        """Generate a unique referral code for a customer."""
        if not program_id:
            program = await self._get_or_create_default_program(business_id)
            program_id = program.id

        # Generate unique code
        code = self._generate_unique_code()

        ref_code = ReferralCode(
            business_id=business_id,
            program_id=program_id,
            conversation_id=conversation_id,
            code=code,
        )
        self.db.add(ref_code)
        await self.db.commit()
        await self.db.refresh(ref_code)
        logger.info(f"Generated referral code {code} for conversation {conversation_id}")
        return ref_code

    def _generate_unique_code(self, length: int = 8) -> str:
        """Generate a unique referral code."""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    async def _get_or_create_default_program(self, business_id: uuid.UUID) -> ReferralProgram:
        """Get or create default referral program."""
        result = await self.db.execute(
            select(ReferralProgram).where(
                ReferralProgram.business_id == business_id,
                ReferralProgram.is_active == True,
            )
        )
        program = result.scalar_one_or_none()
        if not program:
            program = ReferralProgram(
                business_id=business_id,
                name="Programa de Referidos",
                reward_type="discount_credit",
                reward_value=20,
                max_referrals_per_user=10,
                expiry_days=30,
            )
            self.db.add(program)
            await self.db.commit()
            await self.db.refresh(program)
        return program

    # ========== Messaging ==========

    async def generate_referral_message(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
        code: str,
        incentive_description: str = "",
    ) -> str:
        """Generate a personalized referral share message."""
        system_prompt = """Eres un experto en mensajes de referidos. Creas mensajes que:
1. Suenan genuinos y personales (NO robóticos)
2. Explican el beneficio claramente
3. Hacen que compartir sea fácil y natural
4. NO son spam ni agresivos

Tono: amigo recomendando a otro amigo."""

        user_prompt = f"""Escribe un mensaje de WhatsApp/Instagram para que un cliente comparta su código de referido.

Código: {code}
Beneficio: {incentive_description or "20% de descuento en su próxima compra"}

El mensaje debe:
- Ser corto (máx 100 palabras)
- Incluir el código naturalmente
- Explicar QUÉ gana el que refiere y QUÉ gana el nuevo cliente
- Sonar como una recomendación genuina, no publicidad
- Incluir un CTA suave

Ejemplo de estructura:
"Ey, estoy usando [servicio] y me está funcionando genial. Si querés probarlo, usá mi código {code} y conseguís [beneficio]. A mí también me dan un bonus. Win-win! 🙌"""

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=500,
                temperature=0.75,
            ) or f"¡Hola! Estoy usando este servicio y me encanta. Si querés probarlo, usá mi código {code} y conseguís un descuento especial. ¡Saludos!"
        except Exception as e:
            logger.error(f"Failed to generate referral message: {e}")
            return f"¡Hola! Estoy usando este servicio y me encanta. Si querés probarlo, usá mi código {code} y conseguís un descuento especial. ¡Saludos!"

    # ========== Tracking ==========

    async def track_click(self, code: str) -> dict[str, Any]:
        """Track when someone clicks a referral link."""
        ref_code = await self._get_code_by_string(code)
        if not ref_code:
            return {"status": "not_found"}

        ref_code.total_uses += 1
        await self.db.commit()

        logger.info(f"Tracked click for referral code {code}")
        return {
            "status": "tracked",
            "code": code,
            "total_uses": ref_code.total_uses,
        }

    async def track_signup(
        self,
        code: str,
        new_conversation_id: uuid.UUID,
        new_email: str = None,
    ) -> dict[str, Any]:
        """Track when a referral converts to a signup."""
        ref_code = await self._get_code_by_string(code)
        if not ref_code:
            return {"status": "not_found"}

        # Create ReferralUse record
        referral_use = ReferralUse(
            code_id=ref_code.id,
            business_id=ref_code.business_id,
            referred_conversation_id=new_conversation_id,
            referred_email=new_email,
            status=ReferralStatus.CONVERTED,
        )
        self.db.add(referral_use)

        ref_code.total_conversions += 1
        await self.db.commit()

        # Emit event
        await event_bus.emit("referral.signup", {
            "business_id": str(ref_code.business_id),
            "referrer_conversation_id": str(ref_code.conversation_id) if ref_code.conversation_id else None,
            "new_conversation_id": str(new_conversation_id),
            "code": code,
        })

        logger.info(f"Tracked signup for referral code {code}")
        return {
            "status": "converted",
            "code": code,
            "total_conversions": ref_code.total_conversions,
        }

    async def track_purchase(
        self,
        code: str,
        order_id: uuid.UUID,
        order_value: float,
    ) -> dict[str, Any]:
        """Track when a referred user makes their first purchase."""
        ref_code = await self._get_code_by_string(code)
        if not ref_code:
            return {"status": "not_found"}

        ref_code.total_revenue += order_value
        await self.db.commit()

        # Update the ReferralUse record
        referral_use = await self.db.execute(
            select(ReferralUse).where(
                ReferralUse.code_id == ref_code.id,
                ReferralUse.status == ReferralStatus.CONVERTED,
                ReferralUse.reward_given == False,
            ).order_by(desc(ReferralUse.created_at)).limit(1)
        )
        use_record = referral_use.scalar_one_or_none()
        if use_record:
            use_record.converted_order_id = order_id
            use_record.reward_given = True
            await self.db.commit()

        # Emit event
        await event_bus.emit("referral.converted", {
            "business_id": str(ref_code.business_id),
            "referrer_conversation_id": str(ref_code.conversation_id) if ref_code.conversation_id else None,
            "order_id": str(order_id),
            "order_value": float(order_value),
            "code": code,
        })

        return {
            "status": "purchase_tracked",
            "code": code,
            "revenue": float(order_value),
        }

    # ========== Viral Coefficient ==========

    async def calculate_viral_coefficient(self, business_id: uuid.UUID) -> dict[str, Any]:
        """Calculate viral coefficient (K-factor) for a business.

        K = (signups / referrers) * (conversions / signups)
        K > 1.0 means exponential growth.
        """
        # Count unique referrers
        referrers_result = await self.db.execute(
            select(func.count(func.distinct(ReferralCode.conversation_id))).where(
                ReferralCode.business_id == business_id,
                ReferralCode.is_active == True,
            )
        )
        unique_referrers = referrers_result.scalar() or 0

        # Count total signups
        signups_result = await self.db.execute(
            select(func.count(ReferralUse.id)).where(
                ReferralUse.business_id == business_id,
                ReferralUse.status.in_([ReferralStatus.CONVERTED, ReferralStatus.REWARDED]),
            )
        )
        total_signups = signups_result.scalar() or 0

        # Count total conversions (purchases)
        conversions_result = await self.db.execute(
            select(func.count(ReferralUse.id)).where(
                ReferralUse.business_id == business_id,
                ReferralUse.converted_order_id.isnot(None),
            )
        )
        total_conversions = conversions_result.scalar() or 0

        # Calculate K-factor
        signups_per_referrer = (total_signups / unique_referrers) if unique_referrers > 0 else 0
        conversion_rate = (total_conversions / total_signups * 100) if total_signups > 0 else 0
        k_factor = signups_per_referrer * (conversion_rate / 100)

        # Revenue attributed
        revenue_result = await self.db.execute(
            select(func.sum(ReferralCode.total_revenue)).where(
                ReferralCode.business_id == business_id,
            )
        )
        total_revenue = revenue_result.scalar() or 0

        return {
            "business_id": str(business_id),
            "unique_referrers": unique_referrers,
            "total_signups": total_signups,
            "total_conversions": total_conversions,
            "signups_per_referrer": round(signups_per_referrer, 2),
            "conversion_rate": round(conversion_rate, 2),
            "k_factor": round(k_factor, 3),
            "k_interpretation": "viral" if k_factor >= 1.0 else "linear" if k_factor >= 0.5 else "sub_linear",
            "total_revenue": float(total_revenue),
            "exponential_growth": k_factor >= 1.0,
        }

    async def get_campaign_report(self, business_id: uuid.UUID) -> dict[str, Any]:
        """Get full referral campaign report."""
        viral_metrics = await self.calculate_viral_coefficient(business_id)

        # Top referrers
        top_referrers_result = await self.db.execute(
            select(ReferralCode).where(
                ReferralCode.business_id == business_id,
            ).order_by(desc(ReferralCode.total_conversions)).limit(10)
        )
        top_referrers = []
        for ref in top_referrers_result.scalars().all():
            top_referrers.append({
                "code": ref.code,
                "clicks": ref.total_uses,
                "signups": ref.total_conversions,
                "revenue": float(ref.total_revenue),
            })

        return {
            **viral_metrics,
            "top_referrers": top_referrers,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ========== Helpers ==========

    async def _get_code_by_string(self, code: str) -> Optional[ReferralCode]:
        result = await self.db.execute(
            select(ReferralCode).where(ReferralCode.code == code)
        )
        return result.scalar_one_or_none()
