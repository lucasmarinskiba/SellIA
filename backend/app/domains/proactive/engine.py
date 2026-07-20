"""Proactive Outreach Engine

Detects outreach opportunities and generates personalized messages using AI.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.proactive.models import OutreachOpportunity, OutreachRule
from app.domains.memory.models import CustomerMemory, ConversationMemoryChunk
from app.domains.memory.service import MemoryEngine
from app.domains.orders.models import Order
from app.domains.channels.models import Conversation, Message
from app.domains.catalogs.models import CatalogItem
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.agents.business_type_registry import BusinessTypeRegistry

logger = get_logger(__name__)

OPPORTUNITY_TYPES = [
    "cart_abandonment",
    "re_engagement",
    "product_recommendation",
    "anniversary",
    "birthday",
    "price_drop",
    "back_in_stock",
    "churn_risk",
]

# Detector relevance by business type (score 0-100)
DETECTOR_RELEVANCE = {
    "cart_abandonment": {
        "physical_products": 95, "digital_products": 90, "services": 30,
        "consulting": 20, "software": 60, "food_beverage": 85,
        "fashion_beauty": 95, "health_wellness": 80, "home_decor": 90,
        "handcraft": 85, "other": 70,
    },
    "re_engagement": {
        "physical_products": 80, "digital_products": 85, "services": 90,
        "consulting": 90, "software": 95, "food_beverage": 75,
        "fashion_beauty": 80, "health_wellness": 85, "home_decor": 75,
        "handcraft": 70, "other": 80,
    },
    "product_recommendation": {
        "physical_products": 95, "digital_products": 90, "services": 40,
        "consulting": 30, "software": 70, "food_beverage": 80,
        "fashion_beauty": 95, "health_wellness": 85, "home_decor": 90,
        "handcraft": 85, "other": 75,
    },
    "anniversary": {
        "physical_products": 70, "digital_products": 70, "services": 80,
        "consulting": 85, "software": 75, "food_beverage": 70,
        "fashion_beauty": 75, "health_wellness": 80, "home_decor": 70,
        "handcraft": 70, "other": 70,
    },
    "birthday": {
        "physical_products": 70, "digital_products": 70, "services": 80,
        "consulting": 85, "software": 75, "food_beverage": 70,
        "fashion_beauty": 75, "health_wellness": 80, "home_decor": 70,
        "handcraft": 70, "other": 70,
    },
    "price_drop": {
        "physical_products": 90, "digital_products": 85, "services": 50,
        "consulting": 40, "software": 70, "food_beverage": 75,
        "fashion_beauty": 90, "health_wellness": 75, "home_decor": 85,
        "handcraft": 80, "other": 70,
    },
    "back_in_stock": {
        "physical_products": 95, "digital_products": 20, "services": 10,
        "consulting": 10, "software": 30, "food_beverage": 80,
        "fashion_beauty": 90, "health_wellness": 70, "home_decor": 85,
        "handcraft": 80, "other": 60,
    },
    "churn_risk": {
        "physical_products": 60, "digital_products": 80, "services": 85,
        "consulting": 90, "software": 95, "food_beverage": 50,
        "fashion_beauty": 60, "health_wellness": 75, "home_decor": 55,
        "handcraft": 50, "other": 70,
    },
}


class ProactiveEngine:
    """Detects opportunities and generates personalized outreach messages."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.memory = MemoryEngine(db)

    async def _get_business_type(self, business_id: uuid.UUID) -> Optional[str]:
        """Load the specific business type from BusinessContext."""
        try:
            from sqlalchemy import select
            from app.domains.business_context.models import BusinessContext
            result = await self.db.execute(
                select(BusinessContext.business_type).where(
                    BusinessContext.business_id == business_id,
                    BusinessContext.is_active == True,
                )
            )
            btype = result.scalar_one_or_none()
            return btype.value if btype else None
        except Exception as exc:
            logger.debug(f"Could not load business_type for proactive engine: {exc}")
            return None

    # ------------------------------------------------------------------
    # Opportunity Detection
    # ------------------------------------------------------------------

    async def detect_opportunities(self, business_id: uuid.UUID) -> List[OutreachOpportunity]:
        """Run all opportunity detectors for a business and return created opportunities.

        Detectors are filtered by business type relevance so a software company
        doesn't get 'back_in_stock' alerts and a service business doesn't get
        'cart_abandonment' spam.
        """
        opportunities: List[OutreachOpportunity] = []

        # Load business type for filtering
        business_type = await self._get_business_type(business_id)

        # Load active rules for this business
        rules_result = await self.db.execute(
            select(OutreachRule).where(
                OutreachRule.business_id == business_id,
                OutreachRule.is_active == True,
            )
        )
        rules = rules_result.scalars().all()
        rules_by_type: Dict[str, List[OutreachRule]] = {}
        for rule in rules:
            rules_by_type.setdefault(rule.rule_type, []).append(rule)

        # Map detector methods to their opportunity type names
        detector_map = {
            self._detect_cart_abandonment: "cart_abandonment",
            self._detect_re_engagement: "re_engagement",
            self._detect_product_recommendation: "product_recommendation",
            self._detect_anniversary_birthday: "anniversary",
            self._detect_churn_risk: "churn_risk",
            self._detect_price_drop_back_in_stock: "price_drop",
        }

        for detector, opp_type in detector_map.items():
            # Skip detectors irrelevant for this business type
            if business_type:
                relevance = DETECTOR_RELEVANCE.get(opp_type, {}).get(business_type, 50)
                if relevance < 40:
                    logger.debug(f"Skipping detector {detector.__name__} for business {business_id} (type={business_type}, relevance={relevance})")
                    continue

            try:
                detected = await detector(business_id, rules_by_type)
                opportunities.extend(detected)
            except Exception as e:
                logger.exception(f"Detector {detector.__name__} failed for business {business_id}: {e}")

        if opportunities:
            await self.db.commit()

        return opportunities

    async def _detect_cart_abandonment(
        self,
        business_id: uuid.UUID,
        rules_by_type: Dict[str, List[OutreachRule]],
    ) -> List[OutreachOpportunity]:
        """Find pending orders older than configured hours."""
        rules = rules_by_type.get("cart_abandonment", [])
        hours = 24
        min_value = 0
        for rule in rules:
            hours = rule.conditions.get("cart_abandoned_hours", hours)
            min_value = rule.conditions.get("min_cart_value", min_value)

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = (
            select(Order)
            .where(
                Order.business_id == business_id,
                Order.status == "pending",
                Order.created_at < since,
            )
        )
        if min_value:
            stmt = stmt.where(Order.total_amount >= min_value)

        result = await self.db.execute(stmt)
        orders = result.scalars().all()

        created: List[OutreachOpportunity] = []
        for order in orders:
            customer_id = await self._customer_id_from_conversation(order.conversation_id)
            if not customer_id:
                continue

            # Skip if opportunity already exists for this order
            existing = await self.db.execute(
                select(OutreachOpportunity).where(
                    OutreachOpportunity.business_id == business_id,
                    OutreachOpportunity.customer_id == customer_id,
                    OutreachOpportunity.opportunity_type == "cart_abandonment",
                    OutreachOpportunity.trigger_data.contains({"order_id": str(order.id)}),
                )
            )
            if existing.scalar_one_or_none():
                continue

            opp = OutreachOpportunity(
                business_id=business_id,
                customer_id=customer_id,
                opportunity_type="cart_abandonment",
                priority="high" if order.total_amount and float(order.total_amount) > 200 else "medium",
                trigger_data={
                    "order_id": str(order.id),
                    "total_amount": str(order.total_amount) if order.total_amount else None,
                    "currency": order.currency,
                    "items": order.items,
                },
                suggested_channel=rules[0].channel if rules else "whatsapp",
            )
            self.db.add(opp)
            created.append(opp)

        return created

    async def _detect_re_engagement(
        self,
        business_id: uuid.UUID,
        rules_by_type: Dict[str, List[OutreachRule]],
    ) -> List[OutreachOpportunity]:
        """Find customers with no message in the last 3 days."""
        rules = rules_by_type.get("re_engagement", [])
        days = 3
        for rule in rules:
            days = rule.conditions.get("inactive_days", days)

        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Find conversations for this business with last_message_at older than `since`
        stmt = (
            select(Conversation)
            .where(
                Conversation.business_id == business_id,
                Conversation.is_active == True,
                Conversation.last_message_at < since,
            )
        )
        result = await self.db.execute(stmt)
        conversations = result.scalars().all()

        created: List[OutreachOpportunity] = []
        for conv in conversations:
            customer_id = await self._customer_id_from_conversation(conv.id)
            if not customer_id:
                continue

            existing = await self.db.execute(
                select(OutreachOpportunity).where(
                    OutreachOpportunity.business_id == business_id,
                    OutreachOpportunity.customer_id == customer_id,
                    OutreachOpportunity.opportunity_type == "re_engagement",
                    OutreachOpportunity.status.in_(["pending", "sent"]),
                )
            )
            if existing.scalar_one_or_none():
                continue

            opp = OutreachOpportunity(
                business_id=business_id,
                customer_id=customer_id,
                opportunity_type="re_engagement",
                priority="medium",
                trigger_data={
                    "conversation_id": str(conv.id),
                    "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                    "days_inactive": days,
                },
                suggested_channel=rules[0].channel if rules else "whatsapp",
            )
            self.db.add(opp)
            created.append(opp)

        return created

    async def _detect_product_recommendation(
        self,
        business_id: uuid.UUID,
        rules_by_type: Dict[str, List[OutreachRule]],
    ) -> List[OutreachOpportunity]:
        """Use CustomerMemory to find customers who might like catalog items."""
        rules = rules_by_type.get("product_recommendation", [])
        min_confidence = 0.7
        for rule in rules:
            min_confidence = rule.conditions.get("min_confidence", min_confidence)

        # Find customers with preference or purchase_history memories
        stmt = (
            select(CustomerMemory)
            .where(
                CustomerMemory.business_id == business_id,
                CustomerMemory.memory_type.in_(["preference", "purchase_history"]),
                CustomerMemory.confidence >= min_confidence,
            )
            .order_by(desc(CustomerMemory.created_at))
        )
        result = await self.db.execute(stmt)
        memories = result.scalars().all()

        created: List[OutreachOpportunity] = []
        seen_customers: set = set()
        for mem in memories:
            if mem.customer_id in seen_customers:
                continue
            seen_customers.add(mem.customer_id)

            existing = await self.db.execute(
                select(OutreachOpportunity).where(
                    OutreachOpportunity.business_id == business_id,
                    OutreachOpportunity.customer_id == mem.customer_id,
                    OutreachOpportunity.opportunity_type == "product_recommendation",
                    OutreachOpportunity.status.in_(["pending", "sent"]),
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Find a relevant catalog item using simple keyword overlap
            catalog_items = await self.db.execute(
                select(CatalogItem).where(
                    CatalogItem.business_id == business_id,
                    CatalogItem.is_active == True,
                    CatalogItem.is_available == True,
                )
            )
            items = catalog_items.scalars().all()
            recommended = None
            for item in items:
                if mem.content and item.name and item.name.lower() in mem.content.lower():
                    recommended = item
                    break

            opp = OutreachOpportunity(
                business_id=business_id,
                customer_id=mem.customer_id,
                opportunity_type="product_recommendation",
                priority="low",
                trigger_data={
                    "memory_type": mem.memory_type,
                    "memory_content": mem.content,
                    "recommended_item_id": str(recommended.id) if recommended else None,
                    "recommended_item_name": recommended.name if recommended else None,
                },
                suggested_channel=rules[0].channel if rules else "whatsapp",
            )
            self.db.add(opp)
            created.append(opp)

        return created

    async def _detect_anniversary_birthday(
        self,
        business_id: uuid.UUID,
        rules_by_type: Dict[str, List[OutreachRule]],
    ) -> List[OutreachOpportunity]:
        """Check CustomerMemory for birthday or anniversary facts."""
        rules = rules_by_type.get("birthday", []) + rules_by_type.get("anniversary", [])

        stmt = (
            select(CustomerMemory)
            .where(
                CustomerMemory.business_id == business_id,
                CustomerMemory.memory_type.in_(["birthday", "anniversary", "preference"]),
            )
            .order_by(desc(CustomerMemory.created_at))
        )
        result = await self.db.execute(stmt)
        memories = result.scalars().all()

        created: List[OutreachOpportunity] = []
        seen: set = set()
        today = datetime.now(timezone.utc).strftime("%m-%d")

        for mem in memories:
            if mem.customer_id in seen:
                continue

            content_lower = (mem.content or "").lower()
            is_birthday = "cumpleaños" in content_lower or "birthday" in content_lower or mem.memory_type == "birthday"
            is_anniversary = "aniversario" in content_lower or "anniversary" in content_lower or mem.memory_type == "anniversary"

            if not is_birthday and not is_anniversary:
                continue

            # Try to extract MM-DD from content for simple matching
            import re
            date_match = re.search(r"(\d{2})[/-](\d{2})", mem.content or "")
            if date_match:
                mem_date = f"{date_match.group(1)}-{date_match.group(2)}"
                if mem_date != today:
                    continue
            else:
                # If no exact date parsed, create opportunity anyway (engine will handle yearly logic externally if needed)
                pass

            seen.add(mem.customer_id)

            opp_type = "birthday" if is_birthday else "anniversary"
            existing = await self.db.execute(
                select(OutreachOpportunity).where(
                    OutreachOpportunity.business_id == business_id,
                    OutreachOpportunity.customer_id == mem.customer_id,
                    OutreachOpportunity.opportunity_type == opp_type,
                    OutreachOpportunity.status.in_(["pending", "sent"]),
                )
            )
            if existing.scalar_one_or_none():
                continue

            opp = OutreachOpportunity(
                business_id=business_id,
                customer_id=mem.customer_id,
                opportunity_type=opp_type,
                priority="medium",
                trigger_data={
                    "memory_content": mem.content,
                    "memory_type": mem.memory_type,
                },
                suggested_channel=rules[0].channel if rules else "whatsapp",
            )
            self.db.add(opp)
            created.append(opp)

        return created

    async def _detect_churn_risk(
        self,
        business_id: uuid.UUID,
        rules_by_type: Dict[str, List[OutreachRule]],
    ) -> List[OutreachOpportunity]:
        """Detect customers with low engagement + negative emotions."""
        rules = rules_by_type.get("churn_risk", [])
        inactive_days = 7
        for rule in rules:
            inactive_days = rule.conditions.get("inactive_days", inactive_days)

        since = datetime.now(timezone.utc) - timedelta(days=inactive_days)

        # Find customers with negative memories
        stmt = (
            select(CustomerMemory)
            .where(
                CustomerMemory.business_id == business_id,
                CustomerMemory.memory_type.in_(["pain_point", "objection"]),
                CustomerMemory.confidence >= 0.6,
            )
        )
        result = await self.db.execute(stmt)
        negative_memories = result.scalars().all()

        created: List[OutreachOpportunity] = []
        seen: set = set()
        for mem in negative_memories:
            if mem.customer_id in seen:
                continue
            seen.add(mem.customer_id)

            # Check if also inactive
            recent_msg = await self.db.execute(
                select(func.count(Message.id))
                .join(Conversation, Message.conversation_id == Conversation.id)
                .join(
                    ConversationMemoryChunk,
                    ConversationMemoryChunk.conversation_id == Conversation.id,
                )
                .where(
                    ConversationMemoryChunk.user_id == mem.customer_id,
                    Conversation.business_id == business_id,
                    Message.created_at >= since,
                )
            )
            msg_count = recent_msg.scalar() or 0
            if msg_count > 0:
                continue

            existing = await self.db.execute(
                select(OutreachOpportunity).where(
                    OutreachOpportunity.business_id == business_id,
                    OutreachOpportunity.customer_id == mem.customer_id,
                    OutreachOpportunity.opportunity_type == "churn_risk",
                    OutreachOpportunity.status.in_(["pending", "sent"]),
                )
            )
            if existing.scalar_one_or_none():
                continue

            opp = OutreachOpportunity(
                business_id=business_id,
                customer_id=mem.customer_id,
                opportunity_type="churn_risk",
                priority="high",
                trigger_data={
                    "negative_memory_type": mem.memory_type,
                    "negative_memory_content": mem.content,
                    "inactive_days": inactive_days,
                },
                suggested_channel=rules[0].channel if rules else "whatsapp",
            )
            self.db.add(opp)
            created.append(opp)

        return created

    async def _detect_price_drop_back_in_stock(
        self,
        business_id: uuid.UUID,
        rules_by_type: Dict[str, List[OutreachRule]],
    ) -> List[OutreachOpportunity]:
        """Detect catalog items that recently became available or had price drops.

        Since there is no price history table, we look at catalog items
        with `extra_data` flags set by external sync processes.
        """
        rules = rules_by_type.get("price_drop", []) + rules_by_type.get("back_in_stock", [])

        stmt = (
            select(CatalogItem)
            .where(
                CatalogItem.business_id == business_id,
                CatalogItem.is_active == True,
                CatalogItem.extra_data.contains({"recent_change": True}),
            )
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        created: List[OutreachOpportunity] = []
        for item in items:
            change_type = item.extra_data.get("change_type", "price_drop")
            opp_type = "back_in_stock" if change_type == "back_in_stock" else "price_drop"

            # Find customers interested in this item via memory similarity
            interested = await self.memory.search_customer_memories(
                query=item.name or item.description or "",
                customer_id=None,  # search across all customers
                k=20,
            )
            # memory.search_customer_memories requires customer_id, so we do a broader search
            # Instead, fetch all preference memories for this business
            mem_result = await self.db.execute(
                select(CustomerMemory)
                .where(
                    CustomerMemory.business_id == business_id,
                    CustomerMemory.memory_type.in_(["preference", "purchase_history"]),
                )
            )
            all_memories = mem_result.scalars().all()

            seen_customers: set = set()
            for mem in all_memories:
                if mem.customer_id in seen_customers:
                    continue
                if item.name and item.name.lower() in (mem.content or "").lower():
                    seen_customers.add(mem.customer_id)

                    existing = await self.db.execute(
                        select(OutreachOpportunity).where(
                            OutreachOpportunity.business_id == business_id,
                            OutreachOpportunity.customer_id == mem.customer_id,
                            OutreachOpportunity.opportunity_type == opp_type,
                            OutreachOpportunity.trigger_data.contains({"item_id": str(item.id)}),
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    opp = OutreachOpportunity(
                        business_id=business_id,
                        customer_id=mem.customer_id,
                        opportunity_type=opp_type,
                        priority="medium",
                        trigger_data={
                            "item_id": str(item.id),
                            "item_name": item.name,
                            "old_price": str(item.extra_data.get("old_price")) if item.extra_data else None,
                            "new_price": str(item.price) if item.price else None,
                        },
                        suggested_channel=rules[0].channel if rules else "whatsapp",
                    )
                    self.db.add(opp)
                    created.append(opp)

        return created

    # ------------------------------------------------------------------
    # Message Generation
    # ------------------------------------------------------------------

    async def generate_outreach_message(
        self,
        opportunity: OutreachOpportunity,
    ) -> Optional[str]:
        """Generate a personalized outreach message using LLM + CustomerMemory."""
        # Load customer profile
        customer_profile = await self.memory.get_customer_profile_summary(opportunity.customer_id)

        # Build prompt
        system_prompt = (
            "Eres un experto en ventas y marketing conversacional. "
            "Generas mensajes cortos, personalizados y naturales para clientes. "
            "NUNCA uses placeholders como [nombre]. Si no conoces el nombre, saluda amigablemente sin nombre. "
            "Máximo 3 oraciones. Tonos: amigable, profesional, empático."
        )

        user_prompt_parts = [
            f"Tipo de outreach: {opportunity.opportunity_type}",
            f"Canal sugerido: {opportunity.suggested_channel}",
            f"Datos del trigger: {opportunity.trigger_data}",
        ]
        if customer_profile:
            user_prompt_parts.append(f"Perfil del cliente:\n{customer_profile}")

        type_instructions = {
            "cart_abandonment": "Recordarle amablemente que tiene items en el carrito. Ofrecer ayuda, no presionar.",
            "re_engagement": "Reconectar con valor puro: tip, insight, o noticia relevante. Sin pedir nada a cambio.",
            "product_recommendation": "Recomendar un producto basado en sus preferencias. Incluir beneficio claro.",
            "birthday": "Saludo de cumpleaños personalizado. Puede incluir una oferta especial si es apropiado.",
            "anniversary": "Celebrar el aniversario con el cliente. Agradecer lealtad.",
            "price_drop": "Informar sobre una baja de precio de un producto que le interesaba. Incluir urgencia leve.",
            "back_in_stock": "Avisar que un producto que le interesaba volvió a estar disponible.",
            "churn_risk": "Mensaje de empatía. Preguntar qué pasó, ofrecer solución. NO vender todavía.",
        }
        instruction = type_instructions.get(opportunity.opportunity_type, "Generar un mensaje personalizado y relevante.")
        user_prompt_parts.append(f"Instrucción: {instruction}")

        user_prompt = "\n\n".join(user_prompt_parts)

        try:
            message = await generate_raw_ai_response(
                db=self.db,
                business_id=opportunity.business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=500,
                temperature=0.7,
            )
            return message
        except Exception as e:
            logger.exception(f"Failed to generate outreach message for opportunity {opportunity.id}: {e}")
            return None

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    async def schedule_outreach(
        self,
        opportunity: OutreachOpportunity,
        send_at: Optional[datetime] = None,
    ) -> None:
        """Schedule a Celery task to send the outreach at the given time."""
        from app.domains.proactive.tasks import send_outreach_task

        opportunity.scheduled_at = send_at or datetime.now(timezone.utc)
        await self.db.commit()

        # Queue Celery task; Celery handles ETA internally if we pass countdown or eta
        if send_at and send_at > datetime.now(timezone.utc):
            countdown = int((send_at - datetime.now(timezone.utc)).total_seconds())
            send_outreach_task.apply_async(args=[str(opportunity.id)], countdown=max(countdown, 0))
        else:
            send_outreach_task.delay(str(opportunity.id))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _customer_id_from_conversation(
        self,
        conversation_id: Optional[uuid.UUID],
    ) -> Optional[uuid.UUID]:
        """Resolve a customer_id from a conversation_id via memory chunks."""
        if not conversation_id:
            return None
        result = await self.db.execute(
            select(ConversationMemoryChunk.user_id)
            .where(ConversationMemoryChunk.conversation_id == conversation_id)
            .limit(1)
        )
        return result.scalar_one_or_none()
