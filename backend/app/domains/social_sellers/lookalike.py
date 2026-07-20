"""Lookalike Audience Engine — encuentra clientes como tu mejor cliente."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.social_sellers.models import (
    SocialSeller,
    SellerCustomerRelationship,
    UnifiedCustomer,
)
from app.domains.channels.models import Conversation, Message, MessageDirection
from app.domains.orders.models import Order
from app.core.logger import get_logger
from app.domains.social_sellers.lookalike_scorer import (
    calculate_similarity_score,
    extract_behavioral_features,
    match_platform_preference,
)

logger = get_logger(__name__)

BUYING_INTENT_KEYWORDS = [
    'precio', 'precios', 'cuanto', 'cuesta', 'costo', 'valor',
    'comprar', 'ordenar', 'pedir', 'encargar', 'reservar',
    'descuento', 'oferta', 'promo', 'promocion', 'rebaja',
    'envio', 'envío', 'entrega', 'cuando llega', 'disponible',
    'stock', 'tallas', 'colores', 'variantes', 'medios de pago',
    'mercadopago', 'transferencia', 'tarjeta', 'cuotas',
    'lo quiero', 'me interesa', 'me convence', 'dale',
    'pasame datos', 'como pago', 'factura', 'ticket',
]


class LookalikeEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_ideal_customer_profile(self, business_id: uuid.UUID) -> Dict[str, Any]:
        """Analiza el top 20% de clientes por LTV y construye un perfil ideal."""
        result = await self.db.execute(
            select(
                SellerCustomerRelationship.customer_id,
                func.sum(SellerCustomerRelationship.total_revenue).label('ltv'),
                func.sum(SellerCustomerRelationship.deals_closed).label('deals'),
                func.count(SellerCustomerRelationship.id).label('seller_count'),
            )
            .where(
                SellerCustomerRelationship.seller_id.in_(
                    select(SocialSeller.id).where(SocialSeller.business_id == business_id)
                )
            )
            .group_by(SellerCustomerRelationship.customer_id)
            .order_by(desc('ltv'))
        )
        customers = list(result.all())
        if not customers:
            return {
                'avg_lifetime_value': 0.0,
                'avg_purchase_frequency_days': 0.0,
                'preferred_platforms': [],
                'common_keywords_in_messages': [],
                'avg_deal_value': 0.0,
                'best_performing_seller': None,
            }

        top_20_count = max(1, len(customers) // 5)
        top_customers = customers[:top_20_count]
        customer_ids = [c.customer_id for c in top_customers]

        # Conversaciones para plataformas
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id.in_(customer_ids))
        )
        conversations = {c.id: c for c in conv_result.scalars().all()}

        total_ltv = sum(float(c.ltv) for c in top_customers)
        total_deals = sum(int(c.deals) for c in top_customers)
        avg_ltv = total_ltv / len(top_customers)
        avg_deal_value = total_ltv / max(1, total_deals)

        # Plataformas preferidas
        platform_counts: Dict[str, int] = {}
        for cid in customer_ids:
            conv = conversations.get(cid)
            platform = (conv.lead_source or 'unknown').lower() if conv else 'unknown'
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        preferred_platforms = sorted(
            platform_counts.keys(),
            key=lambda p: platform_counts[p],
            reverse=True,
        )[:3]

        # Frecuencia de compra
        uc_result = await self.db.execute(
            select(UnifiedCustomer).where(
                and_(
                    UnifiedCustomer.business_id == business_id,
                    UnifiedCustomer.total_purchases > 0,
                )
            )
            .order_by(desc(UnifiedCustomer.total_lifetime_value))
            .limit(top_20_count)
        )
        unified_customers = list(uc_result.scalars().all())
        if unified_customers:
            avg_frequency = sum(
                uc.buying_frequency_days or 30 for uc in unified_customers
            ) / max(1, len(unified_customers))
        else:
            order_result = await self.db.execute(
                select(Order).where(
                    and_(
                        Order.conversation_id.in_(customer_ids),
                        Order.status.in_(['paid', 'shipped', 'delivered']),
                    )
                ).order_by(Order.created_at)
            )
            orders = list(order_result.scalars().all())
            if len(orders) >= 2:
                dates = sorted([o.created_at for o in orders if o.created_at])
                intervals = [
                    (dates[i] - dates[i - 1]).days
                    for i in range(1, len(dates))
                ]
                avg_frequency = sum(intervals) / len(intervals) if intervals else 30.0
            else:
                avg_frequency = 30.0

        # Best performing seller
        seller_result = await self.db.execute(
            select(
                SellerCustomerRelationship.seller_id,
                func.sum(SellerCustomerRelationship.total_revenue).label('seller_rev'),
            )
            .where(SellerCustomerRelationship.customer_id.in_(customer_ids))
            .group_by(SellerCustomerRelationship.seller_id)
            .order_by(desc('seller_rev'))
        )
        best_seller_row = seller_result.first()
        best_seller_name = None
        if best_seller_row:
            seller_obj = await self.db.execute(
                select(SocialSeller).where(
                    SocialSeller.id == best_seller_row.seller_id
                )
            )
            best_seller = seller_obj.scalar_one_or_none()
            best_seller_name = best_seller.name if best_seller else None

        # Common keywords
        msg_result = await self.db.execute(
            select(Message).where(
                and_(
                    Message.conversation_id.in_(customer_ids),
                    Message.direction == MessageDirection.INBOUND,
                )
            )
        )
        messages = list(msg_result.scalars().all())
        content = ' '.join([m.content.lower() for m in messages])
        keyword_counts = {}
        for kw in BUYING_INTENT_KEYWORDS:
            count = content.count(kw)
            if count > 0:
                keyword_counts[kw] = count
        common_keywords = sorted(
            keyword_counts.keys(),
            key=lambda k: keyword_counts[k],
            reverse=True,
        )[:5]

        return {
            'avg_lifetime_value': round(avg_ltv, 2),
            'avg_purchase_frequency_days': round(avg_frequency, 1),
            'preferred_platforms': preferred_platforms,
            'common_keywords_in_messages': common_keywords,
            'avg_deal_value': round(avg_deal_value, 2),
            'best_performing_seller': best_seller_name,
        }

    async def score_lead_similarity(
        self,
        lead: Conversation,
        ideal_profile: Dict[str, Any],
    ) -> int:
        """Puntaje 0-100 de qué tan similar es un lead al cliente ideal."""
        msg_result = await self.db.execute(
            select(Message).where(Message.conversation_id == lead.id)
        )
        messages = list(msg_result.scalars().all())

        behavior = extract_behavioral_features([
            {
                'content': m.content,
                'direction': (
                    m.direction.value
                    if hasattr(m.direction, 'value')
                    else str(m.direction)
                ),
                'created_at': m.created_at,
            }
            for m in messages
        ])

        inbound_msgs = [
            m for m in messages if m.direction == MessageDirection.INBOUND
        ]
        outbound_msgs = [
            m for m in messages if m.direction == MessageDirection.OUTBOUND
        ]
        total_msgs = len(messages)
        inbound_ratio = len(inbound_msgs) / max(1, len(outbound_msgs))

        content_lower = ' '.join([m.content.lower() for m in inbound_msgs])
        buying_keywords = sum(
            content_lower.count(kw) for kw in BUYING_INTENT_KEYWORDS
        )
        price_mentioned = any(
            kw in content_lower
            for kw in ['precio', 'precios', 'cuanto', 'cuesta', 'costo', 'valor']
        )

        lead_data = {
            'platform': lead.lead_source or 'unknown',
            'engagement': {
                'total_messages': total_msgs,
                'inbound_ratio': inbound_ratio,
            },
            'intent': {
                'buying_keywords': buying_keywords,
                'price_mentioned': price_mentioned,
            },
            'behavior': behavior,
            'demographic': {
                'email': lead.lead_email,
                'phone': lead.lead_phone,
                'name': lead.lead_name,
            },
        }

        return calculate_similarity_score(lead_data, ideal_profile)

    async def find_similar_to_customer(
        self,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Encuentra leads más similares a un cliente top dado."""
        ideal_profile = await self.build_ideal_customer_profile(business_id)

        customer_conv = await self.db.execute(
            select(Conversation).where(Conversation.id == customer_id)
        )
        customer = customer_conv.scalar_one_or_none()
        if not customer:
            return []

        leads_result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.business_id == business_id,
                    Conversation.is_active == True,
                    Conversation.id != customer_id,
                )
            )
        )
        leads = list(leads_result.scalars().all())

        scored_leads = []
        for lead in leads:
            score = await self.score_lead_similarity(lead, ideal_profile)
            if lead.lead_source == customer.lead_source:
                score = min(100, score + 5)

            scored_leads.append({
                'lead_id': str(lead.id),
                'name': lead.lead_name or 'Lead anónimo',
                'platform': lead.lead_source or 'unknown',
                'similarity_score': score,
                'why': self._generate_why(score, lead, ideal_profile),
                'recommended_seller': ideal_profile.get('best_performing_seller'),
            })

        scored_leads.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_leads[:limit]

    async def prioritize_leads(self, business_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Obtiene todos los inbound leads y los puntúa contra el perfil ideal."""
        ideal_profile = await self.build_ideal_customer_profile(business_id)

        leads_result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.business_id == business_id,
                    Conversation.is_active == True,
                )
            )
        )
        leads = list(leads_result.scalars().all())

        scored_leads = []
        for lead in leads:
            score = await self.score_lead_similarity(lead, ideal_profile)
            scored_leads.append({
                'lead_id': str(lead.id),
                'name': lead.lead_name or 'Lead anónimo',
                'platform': lead.lead_source or 'unknown',
                'similarity_score': score,
                'why': self._generate_why(score, lead, ideal_profile),
                'recommended_seller': ideal_profile.get('best_performing_seller'),
            })

        scored_leads.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_leads

    async def get_lookalike_report(self, business_id: uuid.UUID) -> Dict[str, Any]:
        """Genera un resumen: 'Tus mejores clientes compran por IG cada 30 días...'."""
        profile = await self.build_ideal_customer_profile(business_id)
        all_leads = await self.prioritize_leads(business_id)
        top_leads = [l for l in all_leads if l['similarity_score'] >= 50][:10]

        platform = (
            profile.get('preferred_platforms', ['IG'])[0].upper()
            if profile.get('preferred_platforms')
            else 'IG'
        )
        freq = int(profile.get('avg_purchase_frequency_days', 30))

        summary = (
            f'Tus mejores clientes compran por {platform} cada {freq} días '
            f'y responden en < 5 min'
        )

        return {
            'summary': summary,
            'ideal_profile': profile,
            'top_opportunities': top_leads,
            'total_leads_scored': len(all_leads),
        }

    def _generate_why(
        self,
        score: int,
        lead: Conversation,
        ideal_profile: Dict[str, Any],
    ) -> List[str]:
        """Genera razones legibles de por qué el lead es similar."""
        reasons = []
        platform = (lead.lead_source or '').lower()
        if platform in [p.lower() for p in ideal_profile.get('preferred_platforms', [])]:
            reasons.append('Misma plataforma preferida')

        if score >= 80:
            reasons.append('Muy alto engagement e intención de compra')
        elif score >= 60:
            reasons.append('Buena intención de compra')
        elif score >= 40:
            reasons.append('Engagement moderado')

        if lead.lead_name:
            reasons.append('Perfil completado con nombre')

        return reasons[:3]
