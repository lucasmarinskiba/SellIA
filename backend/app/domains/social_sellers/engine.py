"""Social Seller Engine

Gestiona vendedores virtuales por plataforma, sus relaciones con clientes,
y el rendimiento de cada seller en tiempo real.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, List, Dict
from decimal import Decimal

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.social_sellers.models import SocialSeller, SellerCustomerRelationship, SellerPerformance
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.security.models import BusinessUserRole
from app.core.logger import get_logger

logger = get_logger(__name__)


DEFAULT_VOICE_CONFIGS = {
    "instagram": {
        "tone": "amigable y visual",
        "emojis": True,
        "catch_phrases": ["Mirá esto ✨", "Te va a encantar 💜"],
        "response_speed": "fast",
    },
    "tiktok": {
        "tone": "energético y trending",
        "emojis": True,
        "catch_phrases": ["Esto es fuego 🔥", "No te lo podés perder 🚀"],
        "response_speed": "instant",
    },
    "facebook": {
        "tone": "cálido y comunitario",
        "emojis": True,
        "catch_phrases": ["Gracias por tu interés 💙", "Te ayudo con gusto 😊"],
        "response_speed": "fast",
    },
    "whatsapp": {
        "tone": "personal y cercano",
        "emojis": True,
        "catch_phrases": ["Hola! 👋", "Te escribo al toque ⚡"],
        "response_speed": "instant",
    },
    "twitter": {
        "tone": "directo y witty",
        "emojis": True,
        "catch_phrases": ["Dale, vamos 🎯", "Acá estamos 💬"],
        "response_speed": "fast",
    },
    "threads": {
        "tone": "conversacional y relajado",
        "emojis": True,
        "catch_phrases": ["Pasó esto 👀", "Contame más 🙌"],
        "response_speed": "fast",
    },
    "linkedin": {
        "tone": "profesional y consultivo",
        "emojis": False,
        "catch_phrases": ["Gracias por contactarnos.", "Te comparto la información."],
        "response_speed": "normal",
    },
}


class SocialSellerEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_business_access(self, business_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Verifica si el usuario tiene acceso al negocio."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and user.is_superuser:
            return True

        result = await self.db.execute(
            select(BusinessUserRole).where(
                BusinessUserRole.user_id == user_id,
                BusinessUserRole.business_id == business_id,
                BusinessUserRole.is_active == True,
            )
        )
        if result.scalar_one_or_none():
            return True

        result = await self.db.execute(
            select(Business).where(
                Business.id == business_id,
                Business.user_id == user_id,
            )
        )
        if result.scalar_one_or_none():
            return True

        return False

    async def create_seller(
        self,
        business_id: uuid.UUID,
        platform: str,
        name: str,
        personality_slug: Optional[str] = None,
        voice_config: Optional[dict] = None,
        greeting_message: Optional[str] = None,
        closing_message: Optional[str] = None,
        ai_auto_reply: bool = True,
    ) -> SocialSeller:
        """Crea un nuevo social seller con configuración por defecto según plataforma."""
        platform_lower = platform.lower()
        default_voice = DEFAULT_VOICE_CONFIGS.get(platform_lower, DEFAULT_VOICE_CONFIGS["instagram"])
        final_voice = {**default_voice, **(voice_config or {})}

        seller = SocialSeller(
            business_id=business_id,
            platform=platform_lower,
            name=name,
            personality_slug=personality_slug,
            voice_config=final_voice,
            stats={
                "total_sales": 0,
                "revenue": 0,
                "conversion_rate": 0,
                "loyal_customers": 0,
            },
            status="active",
            ai_auto_reply=ai_auto_reply,
            greeting_message=greeting_message,
            closing_message=closing_message,
        )
        self.db.add(seller)
        await self.db.commit()
        await self.db.refresh(seller)
        return seller

    async def get_sellers(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> List[SocialSeller]:
        """Lista todos los sellers de un negocio."""
        query = select(SocialSeller).where(SocialSeller.business_id == business_id)
        if status:
            query = query.where(SocialSeller.status == status)
        query = query.order_by(desc(SocialSeller.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_seller(self, seller_id: uuid.UUID) -> Optional[SocialSeller]:
        """Obtiene un seller con conteo de relaciones."""
        result = await self.db.execute(
            select(SocialSeller).where(SocialSeller.id == seller_id)
        )
        seller = result.scalar_one_or_none()
        if seller:
            rel_count = await self.db.execute(
                select(func.count(SellerCustomerRelationship.id)).where(
                    SellerCustomerRelationship.seller_id == seller_id
                )
            )
            seller._customer_count = rel_count.scalar() or 0
        return seller

    async def update_seller(self, seller_id: uuid.UUID, **updates) -> Optional[SocialSeller]:
        """Actualiza un seller existente."""
        result = await self.db.execute(
            select(SocialSeller).where(SocialSeller.id == seller_id)
        )
        seller = result.scalar_one_or_none()
        if not seller:
            return None

        allowed = {"name", "avatar_url", "personality_slug", "voice_config", "stats", "status", "ai_auto_reply", "greeting_message", "closing_message"}
        for key, value in updates.items():
            if key in allowed and value is not None:
                setattr(seller, key, value)

        seller.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(seller)
        return seller

    async def delete_seller(self, seller_id: uuid.UUID) -> bool:
        """Elimina un seller y sus relaciones en cascada."""
        result = await self.db.execute(
            select(SocialSeller).where(SocialSeller.id == seller_id)
        )
        seller = result.scalar_one_or_none()
        if not seller:
            return False

        await self.db.delete(seller)
        await self.db.commit()
        return True

    async def assign_customer(self, seller_id: uuid.UUID, conversation_id: uuid.UUID) -> SellerCustomerRelationship:
        """Asigna un cliente (conversación) a un seller."""
        existing = await self.db.execute(
            select(SellerCustomerRelationship).where(
                SellerCustomerRelationship.seller_id == seller_id,
                SellerCustomerRelationship.customer_id == conversation_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError('El cliente ya está asignado a este seller.')

        rel = SellerCustomerRelationship(
            seller_id=seller_id,
            customer_id=conversation_id,
            first_contact_at=datetime.now(timezone.utc),
            last_contact_at=datetime.now(timezone.utc),
            total_interactions=1,
            relationship_stage="first_contact",
        )
        self.db.add(rel)
        await self.db.commit()
        await self.db.refresh(rel)
        return rel

    async def get_seller_customers(
        self,
        seller_id: uuid.UUID,
        stage: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Obtiene los clientes asignados a un seller enriquecidos con datos de conversación."""
        from app.domains.channels.models import Conversation
        from app.domains.social_sellers.models import UnifiedCustomer

        query = select(SellerCustomerRelationship).where(
            SellerCustomerRelationship.seller_id == seller_id
        )
        if stage:
            query = query.where(SellerCustomerRelationship.relationship_stage == stage)
        query = query.order_by(desc(SellerCustomerRelationship.last_contact_at)).limit(limit)
        result = await self.db.execute(query)
        relationships = list(result.scalars().all())

        if not relationships:
            return []

        conversation_ids = [rel.customer_id for rel in relationships]

        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id.in_(conversation_ids))
        )
        conversations = {c.id: c for c in conv_result.scalars().all()}

        seller_result = await self.db.execute(
            select(SocialSeller).where(SocialSeller.id == seller_id)
        )
        seller = seller_result.scalar_one_or_none()
        business_id = seller.business_id if seller else None

        unified_customers = {}
        if business_id:
            uc_result = await self.db.execute(
                select(UnifiedCustomer).where(UnifiedCustomer.business_id == business_id)
            )
            all_uc = list(uc_result.scalars().all())
            for uc in all_uc:
                if uc.master_email:
                    unified_customers[('email', uc.master_email.lower())] = uc
                if uc.master_phone:
                    normalized = uc.master_phone.strip().replace(' ', '').replace('-', '')
                    unified_customers[('phone', normalized)] = uc
                for plat, ext_id in (uc.identity_map or {}).items():
                    unified_customers[('platform', plat.lower(), ext_id)] = uc

        output = []
        for rel in relationships:
            conv = conversations.get(rel.customer_id)
            customer_name = conv.lead_name if conv else None
            customer_avatar = (conv.extra_data or {}).get('avatar_url') if conv else None

            uc = None
            if conv and business_id:
                if conv.lead_email:
                    uc = unified_customers.get(('email', conv.lead_email.lower()))
                if not uc and conv.lead_phone:
                    normalized = conv.lead_phone.strip().replace(' ', '').replace('-', '')
                    uc = unified_customers.get(('phone', normalized))
                if not uc and conv.lead_source and conv.external_id:
                    uc = unified_customers.get(('platform', conv.lead_source.lower(), conv.external_id))

            output.append({
                'id': rel.id,
                'seller_id': rel.seller_id,
                'customer_id': rel.customer_id,
                'customer_name': customer_name or 'Desconocido',
                'customer_avatar': customer_avatar,
                'first_contact_at': rel.first_contact_at,
                'last_contact_at': rel.last_contact_at,
                'total_interactions': rel.total_interactions,
                'deals_closed': rel.deals_closed,
                'total_revenue': rel.total_revenue,
                'relationship_stage': rel.relationship_stage,
                'loyalty_score': rel.loyalty_score,
                'next_best_action': rel.next_best_action,
                'unified_customer_id': uc.id if uc else None,
                'unified_display_name': uc.display_name if uc else None,
                'unified_identity_map': uc.identity_map if uc else None,
                'unified_total_lifetime_value': uc.total_lifetime_value if uc else None,
                'created_at': rel.created_at,
                'updated_at': rel.updated_at,
            })

        return output

    async def get_customer_insight(
        self,
        seller_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """Devuelve un perfil enriquecido del cliente para el seller."""
        result = await self.db.execute(
            select(SellerCustomerRelationship).where(
                SellerCustomerRelationship.seller_id == seller_id,
                SellerCustomerRelationship.customer_id == conversation_id,
            )
        )
        rel = result.scalar_one_or_none()
        if not rel:
            return None

        return {
            "customer_id": str(rel.customer_id),
            "seller_id": str(rel.seller_id),
            "relationship_stage": rel.relationship_stage,
            "loyalty_score": rel.loyalty_score,
            "total_interactions": rel.total_interactions,
            "deals_closed": rel.deals_closed,
            "total_revenue": float(rel.total_revenue) if rel.total_revenue else 0,
            "next_best_action": rel.next_best_action,
            "last_contact_at": rel.last_contact_at.isoformat() if rel.last_contact_at else None,
            "first_contact_at": rel.first_contact_at.isoformat() if rel.first_contact_at else None,
        }

    async def record_interaction(
        self,
        seller_id: uuid.UUID,
        conversation_id: uuid.UUID,
        interaction_type: str = "message",
        revenue: Optional[Decimal] = None,
    ) -> Optional[SellerCustomerRelationship]:
        """Registra una interacción y actualiza estadísticas de la relación."""
        result = await self.db.execute(
            select(SellerCustomerRelationship).where(
                SellerCustomerRelationship.seller_id == seller_id,
                SellerCustomerRelationship.customer_id == conversation_id,
            )
        )
        rel = result.scalar_one_or_none()
        if not rel:
            return None

        rel.total_interactions += 1
        rel.last_contact_at = datetime.now(timezone.utc)
        if revenue:
            rel.total_revenue = Decimal(rel.total_revenue or 0) + revenue

        # Actualizar etapa según interacciones
        if rel.total_interactions >= 5 and rel.relationship_stage == "first_contact":
            rel.relationship_stage = "nurturing"
        elif rel.total_interactions >= 10 and rel.relationship_stage == "nurturing":
            rel.relationship_stage = "proposal"

        await self.db.commit()
        await self.db.refresh(rel)
        return rel

    async def record_sale(
        self,
        seller_id: uuid.UUID,
        conversation_id: uuid.UUID,
        amount: Decimal,
    ) -> Optional[Dict[str, Any]]:
        """Registra una venta, actualiza relación, stats del seller y crea celebración."""
        result = await self.db.execute(
            select(SocialSeller).where(SocialSeller.id == seller_id)
        )
        seller = result.scalar_one_or_none()
        if not seller:
            return None

        result = await self.db.execute(
            select(SellerCustomerRelationship).where(
                SellerCustomerRelationship.seller_id == seller_id,
                SellerCustomerRelationship.customer_id == conversation_id,
            )
        )
        rel = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if rel:
            rel.deals_closed += 1
            rel.total_revenue = Decimal(rel.total_revenue or 0) + amount
            rel.last_contact_at = now
            rel.relationship_stage = "closed"
            rel.loyalty_score = min(100, rel.loyalty_score + 10)
        else:
            rel = SellerCustomerRelationship(
                seller_id=seller_id,
                customer_id=conversation_id,
                first_contact_at=now,
                last_contact_at=now,
                total_interactions=1,
                deals_closed=1,
                total_revenue=amount,
                relationship_stage="closed",
                loyalty_score=10,
            )
            self.db.add(rel)

        # Actualizar stats del seller
        seller_stats = dict(seller.stats or {})
        seller_stats["total_sales"] = seller_stats.get("total_sales", 0) + 1
        seller_stats["revenue"] = float(seller_stats.get("revenue", 0)) + float(amount)
        seller.stats = seller_stats
        seller.updated_at = now

        await self.db.commit()
        await self.db.refresh(rel)
        await self.db.refresh(seller)

        # Intentar crear evento de celebración
        celebration = None
        try:
            from app.domains.gamification.models import CelebrationEvent
            celebration_event = CelebrationEvent(
                user_id=seller.business_id,  # simplificado
                business_id=seller.business_id,
                event_type="sale",
                event_title=f'Venta cerrada por {seller.name}',
                event_description=f'Venta de ${float(amount):.2f} en {seller.platform}',
                event_value=amount,
                intensity="medium" if float(amount) < 100 else "big",
                companion_message=f'¡{seller.name} acaba de cerrar una venta! 🎉',
                companion_emotion="excited",
            )
            self.db.add(celebration_event)
            await self.db.commit()
            celebration = str(celebration_event.id)
        except Exception:
            pass

        return {
            "status": "recorded",
            "seller_id": seller_id,
            "conversation_id": conversation_id,
            "amount": amount,
            "new_total_revenue": rel.total_revenue,
            "celebration": celebration,
        }

    async def get_team_report(
        self,
        business_id: uuid.UUID,
        period: str = "week",
    ) -> Dict[str, Any]:
        """Reporte agregado de todo el equipo de sellers."""
        sellers = await self.get_sellers(business_id)
        if not sellers:
            return {
                "business_id": business_id,
                "period": period,
                "total_sellers": 0,
                "total_revenue": Decimal("0"),
                "total_deals": 0,
                "total_leads": 0,
                "avg_conversion_rate": Decimal("0"),
                "top_seller": None,
            }

        total_revenue = Decimal("0")
        total_deals = 0
        total_leads = 0
        top_seller = None
        top_revenue = Decimal("0")

        for seller in sellers:
            stats = seller.stats or {}
            rev = Decimal(str(stats.get("revenue", 0)))
            total_revenue += rev
            total_deals += int(stats.get("total_sales", 0))
            total_leads += int(stats.get("loyal_customers", 0))
            if rev > top_revenue:
                top_revenue = rev
                top_seller = {
                    "id": str(seller.id),
                    "name": seller.name,
                    "platform": seller.platform,
                    "revenue": float(rev),
                }

        avg_conversion = Decimal("0")
        if len(sellers) > 0:
            rates = [Decimal(str(s.stats.get("conversion_rate", 0))) for s in sellers if s.stats]
            if rates:
                avg_conversion = sum(rates) / len(rates)

        return {
            "business_id": business_id,
            "period": period,
            "total_sellers": len(sellers),
            "total_revenue": total_revenue,
            "total_deals": total_deals,
            "total_leads": total_leads,
            "avg_conversion_rate": avg_conversion,
            "top_seller": top_seller,
        }

    async def get_seller_pipeline(self, seller_id: uuid.UUID) -> Dict[str, Any]:
        """Devuelve el pipeline desglosado por etapa de relación."""
        result = await self.db.execute(
            select(
                SellerCustomerRelationship.relationship_stage,
                func.count(SellerCustomerRelationship.id).label("count"),
                func.sum(SellerCustomerRelationship.total_revenue).label("revenue"),
            )
            .where(SellerCustomerRelationship.seller_id == seller_id)
            .group_by(SellerCustomerRelationship.relationship_stage)
        )
        rows = result.all()

        stages = []
        total_customers = 0
        total_revenue = Decimal("0")
        for row in rows:
            stage_revenue = Decimal(row.revenue or 0)
            stages.append({
                "stage": row.relationship_stage,
                "count": row.count,
                "revenue": stage_revenue,
            })
            total_customers += row.count
            total_revenue += stage_revenue

        return {
            "seller_id": seller_id,
            "stages": stages,
            "total_customers": total_customers,
            "total_revenue": total_revenue,
        }

    async def get_seller_performance(
        self,
        seller_id: uuid.UUID,
        period: str = "week",
    ) -> List[SellerPerformance]:
        """Obtiene métricas de rendimiento del seller."""
        result = await self.db.execute(
            select(SellerPerformance)
            .where(
                SellerPerformance.seller_id == seller_id,
                SellerPerformance.period == period,
            )
            .order_by(desc(SellerPerformance.period_start))
        )
        return list(result.scalars().all())

    async def decide_next_action(
        self,
        seller_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """Determina la siguiente mejor acción basada en el estado del cliente."""
        result = await self.db.execute(
            select(SellerCustomerRelationship).where(
                SellerCustomerRelationship.seller_id == seller_id,
                SellerCustomerRelationship.customer_id == conversation_id,
            )
        )
        rel = result.scalar_one_or_none()
        if not rel:
            return None

        actions = {
            "first_contact": {
                "action": "send_message",
                "message": "Hola! 👋 Gracias por contactarnos. ¿En qué puedo ayudarte hoy?",
                "priority": "high",
            },
            "nurturing": {
                "action": "send_message",
                "message": "Te quería mostrar algo que capaz te interesa 😉",
                "priority": "medium",
            },
            "proposal": {
                "action": "offer_discount",
                "discount_pct": 10,
                "message": "Te armo una propuesta exclusiva con un 10% de descuento solo por hoy. ¿Te sirve?",
                "priority": "high",
            },
            "closed": {
                "action": "wait",
                "message": "El cliente ya compró. Mejor no spammear. Revisar en 7 días para upsell.",
                "priority": "low",
            },
            "loyal": {
                "action": "send_message",
                "message": "¡Gracias por ser parte de la familia! 🎁 Te tengo una sorpresa exclusiva.",
                "priority": "medium",
            },
            "advocate": {
                "action": "send_message",
                "message": "¿Te animás a recomendarnos? Tenemos un regalo especial para vos y tus amigos.",
                "priority": "medium",
            },
        }

        next_action = actions.get(rel.relationship_stage, actions["first_contact"])
        next_action["relationship_stage"] = rel.relationship_stage
        next_action["loyalty_score"] = rel.loyalty_score
        next_action["total_interactions"] = rel.total_interactions

        return next_action
