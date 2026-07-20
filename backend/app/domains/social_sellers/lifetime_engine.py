"""Customer Lifetime Engine

Detecta momentos de compra, predice próximas compras y genera
oportunidades para el Radar de Oportunidades.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, List, Dict
from decimal import Decimal

from sqlalchemy import select, func, desc, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.social_sellers.models import SocialSeller, SellerCustomerRelationship
from app.domains.channels.models import Conversation, Message, MessageDirection
from app.domains.orders.models import Order, OrderStatus
from app.domains.crm.models import LeadScore, LeadActivity
from app.domains.intelligence.models import ConversationIntelligence
from app.core.logger import get_logger

logger = get_logger(__name__)

# Keywords that signal buying intent
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

CHURN_RISK_KEYWORDS = [
    'caro', 'muy caro', 'me cobran', 'no me alcanza',
    'me voy', 'cancelar', 'no gracias', 'no me interesa',
    'no funciona', 'mala atencion', 'demora', 'tarda mucho',
    'problema', 'reclamo', 'devolucion', 'devolución',
]

HEAT_LEVELS = {
    'hot': (80, 100),
    'warm': (50, 79),
    'nurture': (20, 49),
    'at_risk': (0, 19),
}


class CustomerLifetimeEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Public API ──────────────────────────────────────────────────────

    async def detect_buying_moments(self, business_id: uuid.UUID, lookback_hours: int = 24) -> List[Dict[str, Any]]:
        """Encuentra clientes con alta probabilidad de compra próxima."""
        opportunities = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        # Obtener conversaciones activas del negocio
        conv_result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.business_id == business_id,
                Conversation.status == 'active',
                Conversation.is_active == True,
            )
            .order_by(desc(Conversation.last_message_at))
        )
        conversations = conv_result.scalars().all()

        for conv in conversations:
            score_data = await self.score_opportunity(conv.id)
            if score_data['score'] < 20:
                continue

            # Solo incluir si hay actividad reciente o señales fuertes
            recent_messages = await self._get_recent_messages(conv.id, hours=lookback_hours)
            has_recent_activity = len(recent_messages) > 0 or score_data['score'] >= 50

            if not has_recent_activity:
                continue

            seller_rel = await self._get_seller_relationship(business_id, conv.id)
            seller = None
            if seller_rel:
                seller = await self.db.execute(
                    select(SocialSeller).where(SocialSeller.id == seller_rel.seller_id)
                )
                seller = seller.scalar_one_or_none()

            purchase_history = await self._get_purchase_history(business_id, conv.id)
            predicted = await self.predict_next_purchase(business_id, conv.id)

            opportunities.append({
                'conversation_id': str(conv.id),
                'customer_name': conv.lead_name or 'Cliente anónimo',
                'platform': conv.lead_source or 'unknown',
                'score': score_data['score'],
                'heat_level': score_data['heat_level'],
                'signals': score_data['signals'],
                'seller_id': str(seller.id) if seller else None,
                'seller_name': seller.name if seller else None,
                'seller_avatar': seller.avatar_url if seller else None,
                'last_contact_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
                'predicted_next_purchase': predicted,
                'purchase_history': purchase_history,
                'recent_messages_count': len(recent_messages),
            })

        # Ordenar por score descendente
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities

    async def predict_next_purchase(self, business_id: uuid.UUID, conversation_id: uuid.UUID) -> Dict[str, Any]:
        """Predice la próxima compra basada en historial."""
        orders = await self._get_customer_orders(business_id, conversation_id)

        if not orders:
            return {
                'predicted_date': None,
                'confidence_score': 0,
                'days_until': None,
                'reason': 'Sin historial de compras',
            }

        if len(orders) == 1:
            # Primer comprador: estimar en 30-45 días
            days_since = (datetime.now(timezone.utc) - orders[0].created_at).days
            return {
                'predicted_date': (datetime.now(timezone.utc) + timedelta(days=45)).isoformat(),
                'confidence_score': 30,
                'days_until': max(0, 45 - days_since),
                'reason': 'Primer comprador: estimado 45 días',
            }

        # Calcular frecuencia media entre compras
        dates = sorted([o.created_at for o in orders if o.created_at])
        intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        avg_interval = sum(intervals) / len(intervals) if intervals else 45

        last_order_date = dates[-1]
        days_since_last = (datetime.now(timezone.utc) - last_order_date).days
        days_until = max(0, int(avg_interval - days_since_last))

        # Confianza basada en consistencia de intervalos
        if len(intervals) > 1:
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            consistency = max(0, 1 - (variance / (avg_interval ** 2 + 1)))
            confidence = int(40 + consistency * 50)
        else:
            confidence = 40

        predicted_date = datetime.now(timezone.utc) + timedelta(days=days_until)

        return {
            'predicted_date': predicted_date.isoformat(),
            'confidence_score': confidence,
            'days_until': days_until,
            'avg_interval_days': round(avg_interval, 1),
            'reason': f'Compra cada {round(avg_interval, 0)} días en promedio',
        }

    async def score_opportunity(self, conversation_id: uuid.UUID) -> Dict[str, Any]:
        """Score 0-100 de qué tan listo está el cliente para comprar."""
        score = 0
        signals = []

        # 1. LeadScore existente (hasta 25 pts)
        lead_score = await self._get_lead_score(conversation_id)
        if lead_score:
            score += min(25, lead_score.total_score // 4)
            if lead_score.classification == 'hot':
                signals.append('Lead calificado como HOT')
            elif lead_score.classification == 'warm':
                signals.append('Lead calificado como WARM')

        # 2. Recency (hasta 25 pts)
        recent_activity = await self._get_recent_activity_score(conversation_id)
        score += recent_activity['points']
        if recent_activity['points'] > 15:
            signals.append('Actividad muy reciente')
        elif recent_activity['points'] > 5:
            signals.append('Actividad reciente')

        # 3. Frequency / historial (hasta 20 pts)
        order_data = await self._get_order_frequency_score(conversation_id)
        score += order_data['points']
        if order_data.get('approaching_reorder'):
            signals.append(f"Se acerca fecha de recompra ({order_data['days_since']} días)")
        if order_data.get('repeat_buyer'):
            signals.append('Cliente recurrente')

        # 4. Intent signals (hasta 20 pts)
        intent_data = await self._get_intent_signals(conversation_id)
        score += intent_data['points']
        if intent_data.get('buying_keywords'):
            signals.append(f"Mencionó intención de compra ({intent_data['buying_keywords']} veces)")
        if intent_data.get('price_asked'):
            signals.append('Preguntó por precio')

        # 5. Engagement quality (hasta 10 pts)
        engagement = await self._get_engagement_score(conversation_id)
        score += engagement['points']
        if engagement.get('fast_responder'):
            signals.append('Responde rápido')

        # Cap and classify
        score = max(0, min(100, score))
        heat_level = self._classify_heat(score)

        return {
            'score': score,
            'heat_level': heat_level,
            'signals': signals,
            'components': {
                'lead_score': min(25, lead_score.total_score // 4) if lead_score else 0,
                'recency': recent_activity['points'],
                'frequency': order_data['points'],
                'intent': intent_data['points'],
                'engagement': engagement['points'],
            },
        }

    async def generate_reorder_prompt(self, seller_id: uuid.UUID, conversation_id: uuid.UUID) -> Optional[str]:
        """Genera un mensaje personalizado para recompra."""
        seller_result = await self.db.execute(
            select(SocialSeller).where(SocialSeller.id == seller_id)
        )
        seller = seller_result.scalar_one_or_none()
        if not seller:
            return None

        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            return None

        name = conv.lead_name or 'Hola'
        predicted = await self.predict_next_purchase(seller.business_id, conversation_id)

        templates = {
            'hot': (
                f"¡{name}! 👋 Noté que venís usando nuestro producto hace un tiempo. "
                f"¿Te queda stock? Si necesitás, te armo el mismo pedido con envío gratis. "
                f"Respondé con un 'sí' y lo gestiono al toque 🚀"
            ),
            'warm': (
                f"¡Hola {name}! 👋 ¿Cómo te fue con tu última compra? "
                f"Si necesitás reponer, tengo una promo especial para clientes frecuentes. "
                f"¿Te interesa que te cuente? 😉"
            ),
            'nurture': (
                f"¡{name}! 💜 Pasaba para recordarte que tenemos novedades. "
                f"Si querés ver lo nuevo, te paso el catálogo. Sin compromiso!"
            ),
            'at_risk': (
                f"{name}, te extrañamos! 😊 "
                f"¿Hubo algo que no te haya convencido? "
                f"Me encantaría saber cómo mejorar. Y si querés, te doy un 15% de descuento en tu próxima compra."
            ),
        }

        score_data = await self.score_opportunity(conversation_id)
        return templates.get(score_data['heat_level'], templates['nurture'])

    async def get_radar_data(self, business_id: uuid.UUID) -> Dict[str, Any]:
        """Datos principales para el dashboard del Radar."""
        opportunities = await self.detect_buying_moments(business_id, lookback_hours=168)  # 7 días

        buckets = {'hot': [], 'warm': [], 'nurture': [], 'at_risk': []}
        for opp in opportunities:
            heat = opp['heat_level']
            if heat in buckets:
                buckets[heat].append(opp)

        # Calcular métricas agregadas
        total_opps = len(opportunities)
        total_potential_revenue = sum(
            float(o['purchase_history'].get('avg_order_value', 0)) for o in opportunities
        )

        # Top oportunidades por categoría
        top_hot = sorted(buckets['hot'], key=lambda x: x['score'], reverse=True)[:3]
        top_warm = sorted(buckets['warm'], key=lambda x: x['score'], reverse=True)[:3]

        return {
            'business_id': str(business_id),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_opportunities': total_opps,
                'hot_count': len(buckets['hot']),
                'warm_count': len(buckets['warm']),
                'nurture_count': len(buckets['nurture']),
                'at_risk_count': len(buckets['at_risk']),
                'total_potential_revenue': round(total_potential_revenue, 2),
            },
            'opportunities': buckets,
            'top_actions': self._generate_top_actions(buckets),
        }

    async def execute_radar_action(self, business_id: uuid.UUID, conversation_id: uuid.UUID, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecuta una acción recomendada desde el radar."""
        payload = payload or {}

        if action == 'send_message':
            seller_rel = await self._get_seller_relationship(business_id, conversation_id)
            seller_id = payload.get('seller_id')
            if seller_rel:
                seller_id = seller_id or str(seller_rel.seller_id)

            if seller_id:
                message = await self.generate_reorder_prompt(uuid.UUID(seller_id), conversation_id)
            else:
                message = payload.get('message', '¡Hola! ¿En qué puedo ayudarte?')

            return {
                'status': 'success',
                'action': 'send_message',
                'message': message,
                'conversation_id': str(conversation_id),
            }

        if action == 'offer_discount':
            discount = payload.get('discount_pct', 10)
            return {
                'status': 'success',
                'action': 'offer_discount',
                'discount_pct': discount,
                'message': f'¡Te ofrecemos un {discount}% de descuento exclusivo por ser cliente frecuente! 🎁',
                'conversation_id': str(conversation_id),
            }

        if action == 'view_profile':
            return {
                'status': 'success',
                'action': 'view_profile',
                'redirect_url': f'/dashboard/conversaciones/{conversation_id}',
                'conversation_id': str(conversation_id),
            }

        return {
            'status': 'error',
            'action': action,
            'detail': 'Acción no reconocida.',
        }

    # ── Private helpers ─────────────────────────────────────────────────

    async def _get_recent_messages(self, conversation_id: uuid.UUID, hours: int = 24) -> List[Message]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.created_at >= cutoff,
            )
            .order_by(desc(Message.created_at))
        )
        return list(result.scalars().all())

    async def _get_seller_relationship(self, business_id: uuid.UUID, conversation_id: uuid.UUID) -> Optional[SellerCustomerRelationship]:
        result = await self.db.execute(
            select(SellerCustomerRelationship)
            .where(SellerCustomerRelationship.customer_id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def _get_customer_orders(self, business_id: uuid.UUID, conversation_id: uuid.UUID) -> List[Order]:
        result = await self.db.execute(
            select(Order)
            .where(
                Order.business_id == business_id,
                Order.conversation_id == conversation_id,
                Order.status.in_(['paid', 'shipped', 'delivered']),
            )
            .order_by(desc(Order.created_at))
        )
        return list(result.scalars().all())

    async def _get_purchase_history(self, business_id: uuid.UUID, conversation_id: uuid.UUID) -> Dict[str, Any]:
        orders = await self._get_customer_orders(business_id, conversation_id)
        if not orders:
            return {'total_orders': 0, 'total_spent': 0, 'avg_order_value': 0}

        total = sum(float(o.total_amount) for o in orders)
        return {
            'total_orders': len(orders),
            'total_spent': round(total, 2),
            'avg_order_value': round(total / len(orders), 2),
            'last_order_at': orders[0].created_at.isoformat() if orders[0].created_at else None,
        }

    async def _get_lead_score(self, conversation_id: uuid.UUID) -> Optional[LeadScore]:
        result = await self.db.execute(
            select(LeadScore).where(LeadScore.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def _get_recent_activity_score(self, conversation_id: uuid.UUID) -> Dict[str, Any]:
        """Puntaje por recencia de actividad (0-25)."""
        points = 0
        now = datetime.now(timezone.utc)

        # Mensajes en últimas 24h
        msgs_24h = await self._get_recent_messages(conversation_id, hours=24)
        if msgs_24h:
            points += min(15, len(msgs_24h) * 3)

        # Mensajes en últimas 72h
        msgs_72h = await self._get_recent_messages(conversation_id, hours=72)
        if msgs_72h and not msgs_24h:
            points += 5

        # LeadActivity reciente
        cutoff = now - timedelta(days=7)
        result = await self.db.execute(
            select(LeadActivity)
            .where(
                LeadActivity.conversation_id == conversation_id,
                LeadActivity.created_at >= cutoff,
            )
        )
        activities = result.scalars().all()
        if activities:
            points += min(10, len(activities) * 2)

        return {'points': min(25, points), 'recent_messages_24h': len(msgs_24h)}

    async def _get_order_frequency_score(self, conversation_id: uuid.UUID) -> Dict[str, Any]:
        """Puntaje por frecuencia de compra (0-20)."""
        # Necesitamos business_id; usamos conversación para inferirlo
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            return {'points': 0}

        orders = await self._get_customer_orders(conv.business_id, conversation_id)
        if not orders:
            return {'points': 0}

        points = min(10, len(orders) * 3)

        # Si compra regularmente y se acerca la fecha
        if len(orders) >= 2:
            dates = sorted([o.created_at for o in orders if o.created_at])
            intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
            avg_interval = sum(intervals) / len(intervals) if intervals else 45
            days_since = (datetime.now(timezone.utc) - dates[-1]).days

            # Se acerca a la fecha estimada de recompra
            if days_since >= avg_interval * 0.7:
                points += 10
                return {
                    'points': min(20, points),
                    'approaching_reorder': True,
                    'days_since': days_since,
                    'avg_interval': round(avg_interval, 1),
                }

        return {'points': min(20, points), 'repeat_buyer': len(orders) >= 2}

    async def _get_intent_signals(self, conversation_id: uuid.UUID) -> Dict[str, Any]:
        """Puntaje por señales de intención de compra (0-20)."""
        points = 0
        buying_count = 0
        price_asked = False

        # Analizar mensajes recientes (30 días)
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.direction == MessageDirection.INBOUND,
                Message.created_at >= cutoff,
            )
        )
        messages = result.scalars().all()

        content_lower = ' '.join([m.content.lower() for m in messages])

        for keyword in BUYING_INTENT_KEYWORDS:
            count = content_lower.count(keyword)
            buying_count += count
            if keyword in ('precio', 'precios', 'cuanto', 'cuesta', 'costo', 'valor'):
                if count > 0:
                    price_asked = True

        # Inteligencia de conversación
        conv_intel = await self.db.execute(
            select(ConversationIntelligence).where(
                ConversationIntelligence.conversation_id == conversation_id
            )
        )
        intel = conv_intel.scalar_one_or_none()

        if intel:
            if intel.dominant_intent in ('purchase', 'buy', 'order'):
                points += 8
            if intel.buying_readiness_score and intel.buying_readiness_score > 60:
                points += 7
            if intel.buying_signals_count and intel.buying_signals_count > 0:
                points += min(5, intel.buying_signals_count)

        # Keywords manual
        points += min(10, buying_count * 2)

        return {
            'points': min(20, points),
            'buying_keywords': buying_count,
            'price_asked': price_asked,
            'messages_analyzed': len(messages),
        }

    async def _get_engagement_score(self, conversation_id: uuid.UUID) -> Dict[str, Any]:
        """Puntaje por calidad de engagement (0-10)."""
        points = 0
        fast_responder = False

        # Contar total de mensajes
        result = await self.db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
        )
        total_msgs = result.scalar() or 0
        points += min(5, total_msgs // 4)

        # Ratio respuesta (inbound vs outbound)
        inbound_result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id,
                Message.direction == MessageDirection.INBOUND,
            )
        )
        inbound = inbound_result.scalar() or 0

        outbound_result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id,
                Message.direction == MessageDirection.OUTBOUND,
            )
        )
        outbound = outbound_result.scalar() or 0

        if outbound > 0 and inbound / outbound > 0.8:
            points += 3
            fast_responder = True

        # Loyalty score desde relación
        rel_result = await self.db.execute(
            select(SellerCustomerRelationship).where(
                SellerCustomerRelationship.customer_id == conversation_id
            )
        )
        rel = rel_result.scalar_one_or_none()
        if rel and rel.loyalty_score > 50:
            points += 2

        return {'points': min(10, points), 'fast_responder': fast_responder, 'total_messages': total_msgs}

    @staticmethod
    def _classify_heat(score: int) -> str:
        for level, (low, high) in HEAT_LEVELS.items():
            if low <= score <= high:
                return level
        return 'at_risk'

    @staticmethod
    def _generate_top_actions(buckets: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        actions = []

        if buckets['hot']:
            actions.append({
                'priority': 'urgent',
                'target': buckets['hot'][0]['customer_name'],
                'action': 'send_message',
                'reason': 'Listo para comprar hoy',
            })

        if buckets['at_risk']:
            actions.append({
                'priority': 'high',
                'target': buckets['at_risk'][0]['customer_name'] if buckets['at_risk'] else 'Cliente en riesgo',
                'action': 'offer_discount',
                'reason': 'En riesgo de irse',
            })

        if buckets['warm']:
            actions.append({
                'priority': 'medium',
                'target': buckets['warm'][0]['customer_name'] if buckets['warm'] else 'Cliente tibio',
                'action': 'send_message',
                'reason': 'Probable esta semana',
            })

        return actions
