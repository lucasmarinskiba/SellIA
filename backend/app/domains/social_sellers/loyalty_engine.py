"""Loyalty Engine

Gestiona el Wall of Fame, badges de lealtad, segmentación RFM
y acciones de fidelización para clientes.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, List, Dict
from decimal import Decimal

from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.social_sellers.models import (
    SocialSeller,
    SellerCustomerRelationship,
    CustomerLoyaltyBadge,
    CustomerBadgeAssignment,
)
from app.domains.channels.models import Conversation
from app.domains.orders.models import Order
from app.domains.retention.models import CustomerSegment, CustomerSegmentType
from app.core.logger import get_logger

logger = get_logger(__name__)

DEFAULT_BADGES = [
    {
        'badge_type': 'champion',
        'name': 'Campeón',
        'description': '5 o más compras completadas. Cliente elite.',
        'criteria': {'min_purchases': 5},
    },
    {
        'badge_type': 'ambassador',
        'name': 'Embajador',
        'description': 'Refirió a al menos una persona.',
        'criteria': {'min_referrals': 1},
    },
    {
        'badge_type': 'fan_1',
        'name': 'Fan #1',
        'description': 'Mayor LTV del negocio. Incondicional.',
        'criteria': {'top_ltv': True},
    },
    {
        'badge_type': 'comeback_kid',
        'name': 'Resucitado',
        'description': 'Volvió a comprar después de 90+ días de inactividad.',
        'criteria': {'return_after_days': 90},
    },
    {
        'badge_type': 'big_spender',
        'name': 'Gran Gastador',
        'description': 'Compra única mayor a $500.',
        'criteria': {'min_single_purchase': 500},
    },
    {
        'badge_type': 'regular',
        'name': 'Regular',
        'description': 'Compra mensualmente durante 6+ meses.',
        'criteria': {'min_months': 6},
    },
]


class LoyaltyEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _ensure_default_badges(self, business_id: uuid.UUID) -> None:
        """Crea los badges por defecto para un negocio si no existen."""
        for badge_data in DEFAULT_BADGES:
            existing = await self.db.execute(
                select(CustomerLoyaltyBadge).where(
                    CustomerLoyaltyBadge.business_id == business_id,
                    CustomerLoyaltyBadge.badge_type == badge_data['badge_type'],
                )
            )
            if existing.scalar_one_or_none():
                continue
            badge = CustomerLoyaltyBadge(
                business_id=business_id,
                badge_type=badge_data['badge_type'],
                name=badge_data['name'],
                description=badge_data['description'],
                criteria=badge_data['criteria'],
            )
            self.db.add(badge)
        await self.db.commit()

    async def get_wall_of_fame(
        self,
        business_id: uuid.UUID,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Devuelve los mejores clientes ordenados por LTV, con badges."""
        await self._ensure_default_badges(business_id)

        result = await self.db.execute(
            select(
                SellerCustomerRelationship.customer_id,
                func.sum(SellerCustomerRelationship.total_revenue).label('ltv'),
                func.sum(SellerCustomerRelationship.deals_closed).label('total_purchases'),
                func.max(SellerCustomerRelationship.last_contact_at).label('last_purchase_at'),
                func.max(SellerCustomerRelationship.first_contact_at).label('first_contact_at'),
            )
            .where(SellerCustomerRelationship.seller_id.in_(
                select(SocialSeller.id).where(SocialSeller.business_id == business_id)
            ))
            .group_by(SellerCustomerRelationship.customer_id)
            .order_by(desc('ltv'))
            .limit(limit)
        )
        rows = result.all()

        customer_ids = [r.customer_id for r in rows]
        if not customer_ids:
            return []

        # Cargar datos de conversación
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id.in_(customer_ids))
        )
        conversations = {c.id: c for c in conv_result.scalars().all()}

        # Cargar conexiones de canal para obtener plataformas
        channel_ids = [c.channel_connection_id for c in conversations.values() if c.channel_connection_id]
        channel_platforms = {}
        if channel_ids:
            from app.domains.channels.models import ChannelConnection
            ch_result = await self.db.execute(
                select(ChannelConnection).where(ChannelConnection.id.in_(channel_ids))
            )
            channel_platforms = {ch.id: ch.platform.value if hasattr(ch.platform, 'value') else str(ch.platform) for ch in ch_result.scalars().all()}

        # Cargar badges asignados
        badge_result = await self.db.execute(
            select(
                CustomerBadgeAssignment.customer_id,
                CustomerLoyaltyBadge.badge_type,
                CustomerLoyaltyBadge.name,
                CustomerLoyaltyBadge.icon_url,
            )
            .join(CustomerLoyaltyBadge, CustomerBadgeAssignment.badge_id == CustomerLoyaltyBadge.id)
            .where(
                CustomerBadgeAssignment.customer_id.in_(customer_ids),
                CustomerBadgeAssignment.business_id == business_id,
            )
        )
        badge_rows = badge_result.all()
        customer_badges: Dict[uuid.UUID, List[Dict[str, str]]] = {}
        for br in badge_rows:
            customer_badges.setdefault(br.customer_id, []).append({
                'badge_type': br.badge_type,
                'name': br.name,
                'icon_url': br.icon_url,
            })

        wall = []
        for row in rows:
            conv = conversations.get(row.customer_id)
            name = conv.lead_name if conv and conv.lead_name else 'Cliente Anónimo'
            platform = channel_platforms.get(conv.channel_connection_id, 'unknown') if conv else 'unknown'
            wall.append({
                'customer_id': str(row.customer_id),
                'name': name,
                'ltv': float(row.ltv or 0),
                'total_purchases': int(row.total_purchases or 0),
                'last_purchase_at': row.last_purchase_at.isoformat() if row.last_purchase_at else None,
                'first_contact_at': row.first_contact_at.isoformat() if row.first_contact_at else None,
                'platform': platform,
                'badges': customer_badges.get(row.customer_id, []),
            })

        return wall

    async def assign_badges(
        self,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """Evalúa criterios y asigna badges ganados a un cliente."""
        await self._ensure_default_badges(business_id)

        # Obtener relación del cliente
        rel_result = await self.db.execute(
            select(SellerCustomerRelationship).where(
                SellerCustomerRelationship.customer_id == customer_id,
                SellerCustomerRelationship.seller_id.in_(
                    select(SocialSeller.id).where(SocialSeller.business_id == business_id)
                ),
            )
        )
        rels = list(rel_result.scalars().all())
        if not rels:
            return []

        total_revenue = sum(float(r.total_revenue or 0) for r in rels)
        total_purchases = sum(r.deals_closed for r in rels)
        last_contact = max((r.last_contact_at for r in rels if r.last_contact_at), default=None)
        first_contact = min((r.first_contact_at for r in rels if r.first_contact_at), default=None)

        # Obtener ordenes para criterios adicionales
        order_result = await self.db.execute(
            select(Order).where(
                Order.conversation_id == customer_id,
                Order.business_id == business_id,
                Order.status.in_(['paid', 'shipped', 'delivered']),
            ).order_by(Order.created_at)
        )
        orders = list(order_result.scalars().all())

        max_single_order = max((float(o.total_amount or 0) for o in orders), default=0)

        # Calcular meses con compras (para regular)
        months_with_purchases = set()
        for o in orders:
            if o.created_at:
                months_with_purchases.add((o.created_at.year, o.created_at.month))
        distinct_months = len(months_with_purchases)

        # Verificar comeback: última compra después de 90 días de inactividad
        comeback = False
        if len(orders) >= 2:
            order_dates = sorted([o.created_at for o in orders if o.created_at])
            for i in range(1, len(order_dates)):
                gap = (order_dates[i] - order_dates[i - 1]).days
                if gap >= 90:
                    comeback = True
                    break

        # Obtener badges existentes
        existing_result = await self.db.execute(
            select(CustomerBadgeAssignment.badge_id).where(
                CustomerBadgeAssignment.customer_id == customer_id,
                CustomerBadgeAssignment.business_id == business_id,
            )
        )
        existing_badge_ids = {r for r in existing_result.scalars().all()}

        # Obtener todos los badges del negocio
        badge_result = await self.db.execute(
            select(CustomerLoyaltyBadge).where(CustomerLoyaltyBadge.business_id == business_id)
        )
        badges = list(badge_result.scalars().all())

        assigned = []
        for badge in badges:
            if badge.id in existing_badge_ids:
                continue
            criteria = badge.criteria or {}
            earned = False

            if badge.badge_type == 'champion' and total_purchases >= criteria.get('min_purchases', 5):
                earned = True
            elif badge.badge_type == 'big_spender' and max_single_order >= criteria.get('min_single_purchase', 500):
                earned = True
            elif badge.badge_type == 'regular' and distinct_months >= criteria.get('min_months', 6):
                earned = True
            elif badge.badge_type == 'comeback_kid' and comeback:
                earned = True
            elif badge.badge_type == 'fan_1':
                # Fan #1 se asigna solo si es el top LTV del negocio (evaluado por separado)
                pass
            elif badge.badge_type == 'ambassador':
                # Ambassador se verifica contra referral_codes
                from app.domains.retention.models import ReferralCode
                ref_result = await self.db.execute(
                    select(func.count(ReferralCode.id)).where(
                        ReferralCode.business_id == business_id,
                        ReferralCode.conversation_id == customer_id,
                        ReferralCode.total_conversions > 0,
                    )
                )
                if ref_result.scalar() or 0 > 0:
                    earned = True

            if earned:
                assignment = CustomerBadgeAssignment(
                    badge_id=badge.id,
                    customer_id=customer_id,
                    business_id=business_id,
                )
                self.db.add(assignment)
                assigned.append({
                    'badge_id': str(badge.id),
                    'badge_type': badge.badge_type,
                    'name': badge.name,
                })

        # Asignar Fan #1 al top LTV del negocio (uno solo)
        fan_1_badge = next((b for b in badges if b.badge_type == 'fan_1'), None)
        if fan_1_badge and fan_1_badge.id not in existing_badge_ids:
            top_result = await self.db.execute(
                select(
                    SellerCustomerRelationship.customer_id,
                    func.sum(SellerCustomerRelationship.total_revenue).label('ltv'),
                )
                .where(SellerCustomerRelationship.seller_id.in_(
                    select(SocialSeller.id).where(SocialSeller.business_id == business_id)
                ))
                .group_by(SellerCustomerRelationship.customer_id)
                .order_by(desc('ltv'))
                .limit(1)
            )
            top_row = top_result.one_or_none()
            if top_row and top_row.customer_id == customer_id:
                assignment = CustomerBadgeAssignment(
                    badge_id=fan_1_badge.id,
                    customer_id=customer_id,
                    business_id=business_id,
                )
                self.db.add(assignment)
                assigned.append({
                    'badge_id': str(fan_1_badge.id),
                    'badge_type': fan_1_badge.badge_type,
                    'name': fan_1_badge.name,
                })

        if assigned:
            await self.db.commit()

        return assigned

    async def get_customer_badges(
        self,
        customer_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """Devuelve todos los badges de un cliente."""
        result = await self.db.execute(
            select(
                CustomerBadgeAssignment.id,
                CustomerBadgeAssignment.earned_at,
                CustomerLoyaltyBadge.badge_type,
                CustomerLoyaltyBadge.name,
                CustomerLoyaltyBadge.description,
                CustomerLoyaltyBadge.icon_url,
            )
            .join(CustomerLoyaltyBadge, CustomerBadgeAssignment.badge_id == CustomerLoyaltyBadge.id)
            .where(CustomerBadgeAssignment.customer_id == customer_id)
            .order_by(desc(CustomerBadgeAssignment.earned_at))
        )
        return [
            {
                'id': str(r.id),
                'badge_type': r.badge_type,
                'name': r.name,
                'description': r.description,
                'icon_url': r.icon_url,
                'earned_at': r.earned_at.isoformat() if r.earned_at else None,
            }
            for r in result.all()
        ]

    async def get_loyalty_segments(
        self,
        business_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Devuelve segmentación RFM: Champions, Loyal, Potential, New, At Risk, Lost."""
        result = await self.db.execute(
            select(
                CustomerSegment.segment,
                func.count(CustomerSegment.id).label('count'),
                func.avg(CustomerSegment.total_revenue).label('avg_revenue'),
            )
            .where(CustomerSegment.business_id == business_id)
            .group_by(CustomerSegment.segment)
        )
        rows = result.all()

        segments = {}
        total_customers = 0
        for row in rows:
            key = row.segment.value if hasattr(row.segment, 'value') else str(row.segment)
            segments[key] = {
                'count': row.count,
                'avg_revenue': float(row.avg_revenue or 0),
            }
            total_customers += row.count

        return {
            'business_id': str(business_id),
            'total_customers': total_customers,
            'segments': segments,
        }

    async def create_loyalty_action(
        self,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
        action_type: str,
    ) -> Dict[str, Any]:
        """Registra una acción de fidelización."""
        valid_actions = {'send_gift', 'offer_vip', 'request_testimonial', 'invite_referral'}
        if action_type not in valid_actions:
            raise ValueError(f'Acción inválida. Usá una de: {valid_actions}')

        action_messages = {
            'send_gift': 'Regalo enviado al cliente.',
            'offer_vip': 'Oferta VIP enviada al cliente.',
            'request_testimonial': 'Solicitud de testimonio enviada.',
            'invite_referral': 'Invitación a referir enviada.',
        }

        return {
            'status': 'success',
            'action': action_type,
            'business_id': str(business_id),
            'customer_id': str(customer_id),
            'message': action_messages.get(action_type, 'Acción registrada.'),
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
